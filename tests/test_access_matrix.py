"""Q01 authorization matrix. CSRF is checked separately from role/object policy."""

import uuid

import pytest
from django.test import Client

from apps.accounts.models import OperatorScope, User
from apps.notifications.models import Announcement, AnnouncementRead, Notification, PersonalDeadline
from apps.requests.models import RequestEvent, ServiceRequest
from apps.requests.services import create_request
from tests.test_schedule import study  # noqa: F401

pytestmark = pytest.mark.django_db
ROLES = ["guest", "owner", "same", "other", "scoped", "unscoped"]


@pytest.fixture
def matrix(study):  # noqa: F811
    students, operator, _ = study
    OperatorScope.objects.create(operator=operator, group=students[0].group)
    unscoped = User.objects.create_user(username="unscoped", role="operator")
    application = create_request(
        actor=students[0].user,
        purpose="other",
        comment="PRIVATE_OWNER_REQUEST",
        submission_key=uuid.uuid4(),
    )
    news = Announcement.objects.create(
        title="GROUP_NEWS",
        body="Общее для группы",
        audience_kind="group",
        target_group=students[0].group,
    )
    from django.utils import timezone

    deadline = PersonalDeadline.objects.create(
        student=students[0], title="PRIVATE_PERSONAL_DEADLINE", due_date=timezone.localdate()
    )
    return {
        "users": dict(
            zip(ROLES, [None, *(s.user for s in students), operator, unscoped], strict=True)
        ),
        "application": application,
        "notification": Notification.objects.get(target_id=application.pk),
        "news": news,
        "deadline": deadline,
        "students": students,
    }


def paths(data):
    pk = data["application"].pk
    note = data["notification"].pk
    return {
        "home": "/",
        "profile": "/profile/",
        "schedule": "/schedule/?date=2026-11-02",
        "grades": "/grades/",
        "session": "/session/",
        "requests": "/requests/",
        "new": "/requests/new/",
        "detail": f"/requests/{pk}/",
        "cancel": f"/requests/{pk}/cancel/",
        "queue": "/operator/requests/",
        "operator_detail": f"/operator/requests/{pk}/",
        "transition": f"/operator/requests/{pk}/transition/",
        "feed": "/notifications/",
        "read": f"/notifications/{note}/read/",
        "open": f"/notifications/{note}/open/",
        "news_read": f"/announcements/{data['news'].pk}/read/",
        "deadline": f"/deadlines/?focus={data['deadline'].pk}",
    }


READ_EXPECTED = {
    "home": [302, 200, 200, 200, 302, 302],
    **{
        key: [302, 200, 200, 200, 403, 403]
        for key in [
            "profile",
            "schedule",
            "grades",
            "session",
            "requests",
            "new",
        ]
    },
    "detail": [302, 200, 404, 404, 403, 403],
    "queue": [302, 403, 403, 403, 200, 200],
    "operator_detail": [302, 403, 403, 403, 200, 404],
    "feed": [302, 200, 200, 200, 200, 200],
    "open": [302, 302, 404, 404, 404, 404],
    "deadline": [302, 200, 404, 404, 403, 403],
}


def snapshot():
    return (
        list(ServiceRequest.objects.order_by("pk").values()),
        list(RequestEvent.objects.order_by("pk").values()),
        list(Notification.objects.order_by("pk").values()),
        list(AnnouncementRead.objects.order_by("pk").values()),
        list(PersonalDeadline.objects.order_by("pk").values()),
    )


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("route", READ_EXPECTED)
def test_personal_read_policy(client, matrix, role, route):
    user = matrix["users"][role]
    if user:
        client.force_login(user)
    before = snapshot()
    response = client.get(paths(matrix)[route])
    assert response.status_code == READ_EXPECTED[route][ROLES.index(role)]
    if role == "guest":
        assert response.url.startswith("/login/?next=")
    assert snapshot() == before
    if response.status_code == 200:
        text = response.content.decode()
        if route in {"detail", "operator_detail"}:
            assert ("PRIVATE_OWNER_REQUEST" in text) == (role in {"owner", "scoped"})
        if route == "profile":
            assert matrix["students"][ROLES.index(role) - 1].full_name in text
            if role != "owner":
                assert matrix["students"][0].full_name not in text
        if route == "deadline":
            assert "PRIVATE_PERSONAL_DEADLINE" in text
        if route == "feed":
            assert response.context["items"].paginator.count == (role == "owner")
            assert response.context["unread_count"] == (
                2 if role == "owner" else int(role in {"same", "scoped"})
            )
        if route == "requests":
            assert response.context["items"].paginator.count == int(role == "owner")
        if route == "queue":
            assert response.context["items"].paginator.count == int(role == "scoped")


POST_EXPECTED = {
    "new": [302, 302, 302, 302, 403, 403],
    "cancel": [302, 302, 404, 404, 403, 403],
    "transition": [302, 403, 403, 403, 302, 404],
    "read": [302, 302, 404, 404, 404, 404],
    "news_read": [302, 302, 302, 404, 302, 404],
}


def payload(route):
    return {
        "new": {"purpose": "other", "submission_key": uuid.uuid4(), "student": 9999},
        "cancel": {"expected_version": 1},
        "transition": {"expected_version": 1, "desired_status": "in_progress"},
    }.get(route, {})


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("route", POST_EXPECTED)
def test_personal_write_policy_and_effects(client, matrix, role, route):
    user = matrix["users"][role]
    if user:
        client.force_login(user)
    before = snapshot()
    response = client.post(paths(matrix)[route], payload(route))
    assert response.status_code == POST_EXPECTED[route][ROLES.index(role)]
    if role == "guest":
        assert response.url.startswith("/login/?next=")
    if response.status_code != 302 or role == "guest":
        assert snapshot() == before
        return
    application = matrix["application"]
    if route == "new":
        created = ServiceRequest.objects.exclude(pk=application.pk).get()
        assert created.student.user_id == user.pk
        assert created.events.get().actor_id == user.pk
        assert Notification.objects.get(target_id=created.pk).recipient_id == user.pk
        assert response.url == f"/requests/{created.pk}/"
    elif route in {"cancel", "transition"}:
        application.refresh_from_db()
        assert application.status == ("cancelled" if route == "cancel" else "in_progress")
        assert application.version == 2 and application.events.count() == 2
        assert application.events.get(version=2).actor_id == user.pk
        assert set(
            Notification.objects.filter(target_id=application.pk).values_list(
                "recipient_id", flat=True
            )
        ) == {matrix["users"]["owner"].pk}
    elif route == "read":
        matrix["notification"].refresh_from_db()
        assert matrix["notification"].read_at is not None
    else:
        assert list(AnnouncementRead.objects.values_list("user_id", "announcement_id")) == [
            (user.pk, matrix["news"].pk)
        ]


@pytest.mark.parametrize("route", [*POST_EXPECTED, "logout", "login"])
def test_all_mutations_require_csrf(matrix, route):
    client = Client(enforce_csrf_checks=True)
    client.force_login(matrix["users"]["scoped" if route == "transition" else "owner"])
    before = snapshot()
    url = paths(matrix).get(route, f"/{route}/")
    assert client.post(url, payload(route)).status_code == 403
    assert snapshot() == before
    assert client.session.get("_auth_user_id")


@pytest.mark.parametrize("route", ["cancel", "transition", "read", "news_read"])
def test_mutation_get_is_rejected(client, matrix, route):
    client.force_login(matrix["users"]["scoped" if route == "transition" else "owner"])
    before = snapshot()
    assert client.get(paths(matrix)[route]).status_code == 405
    assert snapshot() == before


@pytest.mark.parametrize("route", ["detail", "operator_detail", "open", "deadline"])
def test_hx_request_does_not_expand_object_access(client, matrix, route):
    client.force_login(matrix["users"]["same"])
    before = snapshot()
    expected = 403 if route == "operator_detail" else 404
    assert client.get(paths(matrix)[route], HTTP_HX_REQUEST="true").status_code == expected
    assert snapshot() == before


# New-request and personal-deadline pages intentionally support GET and POST.
# Their validation, CSRF and mutation effects are covered in their focused suites.
@pytest.mark.parametrize("route", [key for key in READ_EXPECTED if key not in {"new", "deadline"}])
def test_read_route_rejects_post_without_effects(client, matrix, route):
    client.force_login(
        matrix["users"]["scoped" if route in {"queue", "operator_detail"} else "owner"]
    )
    before = snapshot()
    assert client.post(paths(matrix)[route], {}).status_code == 405
    assert snapshot() == before


@pytest.mark.parametrize("route", ["home", "profile", *POST_EXPECTED])
def test_guest_with_valid_csrf_redirects_to_login(matrix, route):
    client = Client(enforce_csrf_checks=True)
    assert client.get("/login/").status_code == 200
    before = snapshot()
    response = client.post(
        paths(matrix)[route],
        {**payload(route), "csrfmiddlewaretoken": client.cookies["csrftoken"].value},
    )
    assert response.status_code == 302
    assert response.url.startswith("/login/?next=")
    assert snapshot() == before
    assert not client.session.get("_auth_user_id")


@pytest.mark.parametrize("method", ["get", "post"])
def test_legacy_deadline_route_unavailable(client, matrix, method):
    client.force_login(matrix["users"]["owner"])
    before = snapshot()
    assert getattr(client, method)(f"/deadlines/{matrix['deadline'].pk}/").status_code == 404
    assert snapshot() == before
