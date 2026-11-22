"""Q02: commit effects, beyond request status/version alone (PostgreSQL)."""

import uuid
from unittest.mock import patch

import pytest

from apps.accounts.models import OperatorScope, User
from apps.notifications.models import Notification
from apps.requests.services import create_request, transition_request
from tests.test_requests import race, requests_data  # noqa: F401
from tests.test_schedule import study  # noqa: F401

pytestmark = pytest.mark.django_db


def effects(application):
    return (
        list(application.events.values()),
        list(Notification.objects.filter(target_id=application.pk).order_by("dedupe_key").values()),
    )


def assert_effects(application, actors):
    application.refresh_from_db()
    events = list(application.events.order_by("version"))
    assert [event.version for event in events] == list(range(1, application.version + 1))
    assert events[-1].to_status == application.status
    assert events[-1].actor_id in actors
    assert events[0].actor_id == application.student.user_id
    assert [(event.from_status, event.to_status) for event in events][0] == ("", "submitted")
    for previous, current in zip(events, events[1:], strict=False):
        assert current.from_status == previous.to_status
    notifications = Notification.objects.filter(target_id=application.pk)
    assert set(notifications.values_list("recipient_id", "dedupe_key")) == {
        (application.student.user_id, f"request:{application.pk}:{version}")
        for version in range(1, application.version + 1)
    }
    assert notifications.count() == application.version
    assert set(notifications.values_list("kind", "target_type")) == {("request", "request")}
    assert notifications.get(
        dedupe_key=f"request:{application.pk}:{application.version}"
    ).title == ("Статус заявки: " + application.get_status_display())


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("contender", ["operator", "cancel"])
def test_winning_transition_has_one_history_and_notification(requests_data, contender):  # noqa: F811
    students, operator = requests_data
    second = User.objects.create_user(username="second-operator", role="operator")
    OperatorScope.objects.create(operator=second, group=students[0].group)
    application = create_request(
        actor=students[0].user, purpose="other", submission_key=uuid.uuid4()
    )
    other_actor = second if contender == "operator" else students[0].user
    desired = "in_progress" if contender == "operator" else "cancelled"

    def transition(actor, status):
        result = transition_request(
            actor=actor, request_id=application.pk, expected_version=1, desired_status=status
        )
        return result.status

    result = race(
        [
            lambda: transition(operator, "in_progress"),
            lambda: transition(other_actor, desired),
        ]
    )
    assert result.count("RequestConflict") == 1
    assert_effects(application, {operator.pk, other_actor.pk})
    assert application.version == 2
    winner = application.events.get(version=2)
    assert (winner.actor_id == students[0].user_id) == (winner.to_status == "cancelled")
    assert winner.to_status in result


@pytest.mark.django_db(transaction=True)
def test_parallel_submit_has_only_owner_initial_effects(requests_data):  # noqa: F811
    students, _ = requests_data
    key = uuid.uuid4()

    def submit():
        return create_request(actor=students[0].user, purpose="other", submission_key=key).pk

    identities = race([submit, submit])
    assert len(set(identities)) == 1
    from apps.requests.models import ServiceRequest

    application = ServiceRequest.objects.get()
    assert_effects(application, {students[0].user_id})
    before = effects(application)
    assert submit() == application.pk
    assert effects(application) == before


def test_notification_failure_preserves_existing_history_then_retry(requests_data):  # noqa: F811
    students, operator = requests_data
    application = create_request(
        actor=students[0].user, purpose="other", submission_key=uuid.uuid4()
    )
    application = transition_request(
        actor=operator, request_id=application.pk, expected_version=1, desired_status="in_progress"
    )
    Notification.objects.filter(target_id=application.pk).update(read_at=application.created_at)
    before = effects(application)
    with patch("apps.notifications.services.notify", side_effect=RuntimeError("injected")):
        with pytest.raises(RuntimeError, match="injected"):
            transition_request(
                actor=operator,
                request_id=application.pk,
                expected_version=2,
                desired_status="ready",
                comment="Проверено",
            )
    application.refresh_from_db()
    assert (application.status, application.version) == ("in_progress", 2)
    assert effects(application) == before
    transition_request(
        actor=operator,
        request_id=application.pk,
        expected_version=2,
        desired_status="ready",
        comment="Проверено",
    )
    assert_effects(application, {operator.pk})
    assert application.version == 3
    assert application.events.get(version=3).public_comment == "Проверено"
    assert Notification.objects.filter(target_id=application.pk, read_at__isnull=False).count() == 2
