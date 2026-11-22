# ruff: noqa: F811
import uuid
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.test import Client

from apps.accounts.models import OperatorScope, User
from apps.notifications.models import Notification
from apps.requests.models import RequestMessage
from apps.requests.services import RequestConflict, send_request_message
from tests.test_requests import make, race, requests_data  # noqa: F401
from tests.test_schedule import study  # noqa: F401

pytestmark = pytest.mark.django_db


def send(actor, application, **kwargs):
    return send_request_message(
        actor=actor,
        request_id=application.pk,
        body=kwargs.pop("body", "Вопрос"),
        submission_key=kwargs.pop("submission_key", uuid.uuid4()),
        **kwargs,
    )


def test_messages_retry_normalization_audience_and_status(requests_data):
    students, operator = requests_data
    application = make(students[0])
    extra = User.objects.create_user(username="message-operator", role="operator")
    OperatorScope.objects.create(operator=extra, group=students[0].group)
    inactive = User.objects.create_user(
        username="inactive-message-operator", role="operator", is_active=False
    )
    OperatorScope.objects.create(operator=inactive, group=students[0].group)
    key = uuid.uuid4()
    message = send(students[0].user, application, body="  Вопрос\r\nстрока  ", submission_key=key)
    assert message.body == "Вопрос\nстрока"
    assert (
        send(students[0].user, application, body=message.body, submission_key=key).pk == message.pk
    )
    with pytest.raises(RequestConflict):
        send(students[0].user, application, body="другое", submission_key=key)
    notices = Notification.objects.filter(dedupe_key=f"request-message:{message.pk}")
    assert set(notices.values_list("recipient_id", flat=True)) == {operator.pk, extra.pk}
    assert all(n.target_id == application.pk and message.body not in n.body for n in notices)
    reply = send(operator, application, operator=True)
    assert list(
        Notification.objects.filter(dedupe_key=f"request-message:{reply.pk}").values_list(
            "recipient_id", flat=True
        )
    ) == [students[0].user_id]
    application.refresh_from_db()
    assert (
        application.version == 1
        and application.status == "submitted"
        and application.events.count() == 1
    )
    with patch("apps.notifications.services.notify", side_effect=IntegrityError):
        with pytest.raises(IntegrityError):
            send(operator, application, operator=True)
    assert RequestMessage.objects.count() == 2


def test_permissions_validation_and_constraints(requests_data):
    students, operator = requests_data
    application = make(students[0])
    with pytest.raises(Http404):
        send(students[1].user, application)
    with pytest.raises(PermissionDenied):
        send(operator, application)
    OperatorScope.objects.all().delete()
    with pytest.raises(Http404):
        send(operator, application, operator=True)
    User.objects.filter(pk=students[0].user_id).update(role="operator")
    with pytest.raises(PermissionDenied):
        send(students[0].user, application)
    User.objects.filter(pk=students[0].user_id).update(role="student", is_active=False)
    with pytest.raises(PermissionDenied):
        send(students[0].user, application)
    User.objects.filter(pk=students[0].user_id).update(is_active=True)
    for body in ["", " \n\t", "a" * 2001, None]:
        with pytest.raises(ValidationError):
            send(students[0].user, application, body=body)
    for body in ["", " \n\t", "a" * 2001]:
        with pytest.raises(IntegrityError), transaction.atomic():
            RequestMessage.objects.create(
                request=application, author=students[0].user, body=body, submission_key=uuid.uuid4()
            )


def test_http_pagination_reopen_csrf_and_escape(client, requests_data):
    students, operator = requests_data
    application = make(students[0])
    base = f"/requests/{application.pk}/"
    client.force_login(students[1].user)
    assert client.get(base).status_code == 404
    assert client.post(base + "messages/", {}).status_code == 404
    client.force_login(students[0].user)
    assert client.get(base + "messages/").status_code == 405
    payload = {"body": '<script>alert("x")</script>', "submission_key": str(uuid.uuid4())}
    response = client.post(base + "messages/", payload)
    assert response.url == base + "#conversation"
    assert client.post(base + "messages/", payload).status_code == 302
    assert client.post(base + "messages/", {**payload, "body": "changed"}).status_code == 409
    assert client.post(base + "messages/", {**payload, "body": " "}).context["message_form"].errors
    client.logout()
    client.force_login(students[0].user)
    response = client.get(base)
    assert "no-store" in response["Cache-Control"]
    assert b"&lt;script&gt;alert" in response.content and b"<script>alert" not in response.content
    for i in range(22):
        send(students[0].user, application, body=f"Сообщение {i}")
    first = client.get(base).context["conversation_page"]
    second = client.get(base + "?messages_page=2").context["conversation_page"]
    assert len(first) == 20 and len(second) == 3
    assert first[0].pk > first[-1].pk > second[0].pk
    for query in [
        "messages_page=0",
        "messages_page=-1",
        "messages_page=abc",
        "messages_page=1&messages_page=2",
        "student=1",
    ]:
        assert client.get(base + "?" + query).status_code == 400
    assert client.get(base + "?messages_page=999").status_code == 404
    secure = Client(enforce_csrf_checks=True)
    secure.force_login(students[0].user)
    assert secure.post(base + "messages/", payload).status_code == 403
    secure.force_login(operator)
    operator_base = f"/operator/requests/{application.pk}/"
    assert secure.post(operator_base + "messages/", payload).status_code == 403
    client.force_login(operator)
    assert (
        client.post(
            operator_base + "messages/", {**payload, "submission_key": uuid.uuid4()}
        ).status_code
        == 302
    )
    OperatorScope.objects.all().delete()
    assert client.get(operator_base).status_code == 404
    assert client.post(operator_base + "messages/", payload).status_code == 404


@pytest.mark.django_db(transaction=True)
def test_parallel_retry(requests_data):
    students, _ = requests_data
    application = make(students[0])
    key = uuid.uuid4()

    def submit():
        return send(students[0].user, application, submission_key=key).pk

    assert len(set(race([submit, submit]))) == 1
    assert RequestMessage.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_additive_message_migration_preserves_request(requests_data):
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    students, _ = requests_data
    application = make(students[0], comment="До миграции")
    pk = application.pk
    try:
        MigrationExecutor(connection).migrate([("requests", "0001_initial")])
        application.refresh_from_db()
        assert application.comment == "До миграции" and application.events.count() == 1
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
    application.refresh_from_db()
    assert application.pk == pk and application.version == 1
    assert send(students[0].user, application).request_id == pk


@pytest.mark.django_db(transaction=True)
def test_parallel_changed_message_conflicts(requests_data):
    students, _ = requests_data
    application = make(students[0])
    key = uuid.uuid4()
    result = race(
        [
            lambda: send(students[0].user, application, body="Первое", submission_key=key).pk,
            lambda: send(students[0].user, application, body="Второе", submission_key=key).pk,
        ]
    )
    assert result.count("RequestConflict") == 1
    assert RequestMessage.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_parallel_opposite_roles_notify_without_deadlock(requests_data):
    students, operator = requests_data
    application = make(students[0])
    result = race(
        [
            lambda: send(students[0].user, application, body="Вопрос студента").pk,
            lambda: send(operator, application, operator=True, body="Ответ деканата").pk,
        ]
    )
    assert len(set(result)) == 2
    assert RequestMessage.objects.count() == 2
    notices = Notification.objects.filter(dedupe_key__startswith="request-message:")
    assert notices.count() == 2
    assert set(notices.values_list("recipient_id", flat=True)) == {students[0].user_id, operator.pk}
    application.refresh_from_db()
    assert application.status == "submitted" and application.version == 1
    assert application.events.count() == 1
