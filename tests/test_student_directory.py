"""Read-only student directory whitelist and unchanged owner-only writes."""

import pytest
from django.test import Client

from apps.accounts.models import StudentPersona, StudentProfile, User
from apps.accounts.selectors import directory_profiles, directory_student
from apps.accounts.services import save_persona
from tests.test_accounts import identities  # noqa: F401
from tests.test_persona import values

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def local_directory(settings):
    settings.ENABLE_STUDENT_DIRECTORY = True


def test_audience_and_methods(client, identities):  # noqa: F811
    students, operator = identities
    detail = f"/students/{students[1].studentprofile.pk}/"
    for path in ["/students/", detail]:
        assert client.get(path).status_code == 302
        client.force_login(operator)
        assert client.get(path).status_code == 403
        client.force_login(students[0])
        assert client.post(path, {}).status_code == 405
        assert client.put(path).status_code == 405
        client.logout()
    client.force_login(students[0])
    assert client.get("/students/99999999/").status_code == 404
    response = client.get(f"/students/{students[0].studentprofile.pk}/")
    assert response.status_code == 302 and response.url == "/profile/"
    assert "no-store" in response["Cache-Control"]
    students[0].is_active = False
    students[0].save()
    assert client.get("/students/").status_code == 302


def test_cross_group_whitelist_persona_and_empty(client, identities):  # noqa: F811
    students, _ = identities
    owner = students[0]
    save_persona(actor=owner, **values(goal="Дебаты в новом семестре"))
    owner.email = "private-marker@example.invalid"
    owner.save()
    expected_fields = {
        "pk",
        "full_name",
        "course",
        "group__code",
        "group__program__name",
        "group__program__faculty__name",
    }
    for viewer in students[1:]:
        # identities supplies both a different-group and a same-group viewer.
        client.force_login(viewer)
        response = client.get(f"/students/{owner.studentprofile.pk}/")
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
        html = response.text
        assert owner.studentprofile.full_name in html
        assert "Дебаты в новом семестре" in html and "Анализирую" in html
        for marker in [owner.username, owner.email, owner.password, "is_staff", "last_login"]:
            assert marker not in html
        assert "Редактировать" not in html and "Сохранить persōna" not in html
        assert set(response.context["student"]) == expected_fields
        assert "user" not in directory_student(viewer, owner.studentprofile.pk)
        assert set(directory_profiles(viewer).first()) == expected_fields
        assert '<meta name="robots" content="noindex, nofollow">' in html
    client.force_login(owner)
    empty = client.get(f"/students/{students[1].studentprofile.pk}/")
    assert "пока не заполнил persōna" in empty.text
    assert "Расскажите о себе" not in empty.text


def test_search_case_pagination_and_inactive_filter(client, identities):  # noqa: F811
    students, _ = identities
    group = students[0].studentprofile.group
    for index in range(23):
        user = User.objects.create_user(username=f"fiction-directory-{index}")
        StudentProfile.objects.create(user=user, full_name="Алёна Каталог", course=1, group=group)
    hidden = User.objects.create_user(username="fiction-inactive", is_active=False)
    StudentProfile.objects.create(user=hidden, full_name="Скрытый каталог", course=1, group=group)
    client.force_login(students[0])
    response = client.get("/students/", {"q": "аЛЁнА"})
    assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    page_one = [row["pk"] for row in response.context["items"]]
    assert len(page_one) == 20 and page_one == sorted(page_one)
    response = client.get("/students/", {"q": "аЛЁнА", "page": 2})
    page_two = [row["pk"] for row in response.context["items"]]
    assert len(page_two) == 3 and not set(page_one) & set(page_two)
    assert page_two == sorted(page_two)
    assert "Скрытый каталог" not in client.get("/students/", {"q": "каталог"}).text
    assert "Никого не нашли" in client.get("/students/", {"q": "Несуществующий"}).text
    response = client.get("/students/", {"q": '<script>alert("x")</script>'})
    assert "&lt;script&gt;" in response.text and '<script>alert("x")</script>' not in response.text


@pytest.mark.parametrize(
    "query",
    [
        "q=" + "a" * 81,
        "q=a&q=b",
        "page=1&page=2",
        "other=x",
        "page=0",
        "page=-1",
        "page=abc",
        "page=99999999",
    ],
)
def test_bad_search(client, identities, query):  # noqa: F811
    client.force_login(identities[0][0])
    response = client.get("/students/?" + query)
    assert response.status_code == 400 and "no-store" in response["Cache-Control"]


def test_reading_and_forged_writes_do_not_change_other_persona(client, identities):  # noqa: F811
    owner, viewer = identities[0][:2]
    persona = save_persona(actor=owner, **values(goal="Цель владельца"))
    client.force_login(viewer)
    detail = f"/students/{owner.studentprofile.pk}/"
    before = StudentPersona.objects.count()
    client.get("/students/")
    client.get(detail)
    assert StudentPersona.objects.count() == before
    assert client.post(detail, values(goal="Чужая подмена")).status_code == 405
    response = client.post(
        "/profile/persona/",
        {**values(goal="Моя цель"), "owner": owner.pk, "profile_id": owner.studentprofile.pk},
    )
    assert response.status_code == 302 and response.url == "/profile/"
    persona.refresh_from_db()
    assert persona.goal == "Цель владельца"
    assert StudentPersona.objects.get(student=viewer.studentprofile).goal == "Моя цель"
    protected = Client(enforce_csrf_checks=True)
    protected.force_login(viewer)
    assert protected.post("/profile/persona/", values()).status_code == 403


def test_directory_omits_academic_request_and_notification_markers(client, monkeypatch):
    from apps.academics.models import Subject
    from apps.notifications.models import Notification
    from apps.requests.models import ServiceRequest
    from tests.test_dashboard_demo import seed

    seed(monkeypatch)
    owner = User.objects.get(username="student.one")
    viewer = User.objects.get(username="student.two")
    Subject.objects.all().update(name="ACADEMIC_PRIVATE_MARKER")
    ServiceRequest.objects.filter(student=owner.studentprofile).update(
        comment="REQUEST_PRIVATE_MARKER"
    )
    Notification.objects.filter(recipient=owner).update(body="NOTICE_PRIVATE_MARKER")
    client.force_login(viewer)
    for path in ["/students/", f"/students/{owner.studentprofile.pk}/"]:
        response = client.get(path)
        assert response.status_code == 200
        for marker in [
            "ACADEMIC_PRIVATE_MARKER",
            "REQUEST_PRIVATE_MARKER",
            "NOTICE_PRIVATE_MARKER",
        ]:
            assert marker not in response.text


def test_disabled_directory_hides_other_profiles_before_queries(
    client,
    identities,  # noqa: F811
    settings,
    monkeypatch,
):
    settings.ENABLE_STUDENT_DIRECTORY = False

    def forbidden(*args, **kwargs):
        raise AssertionError("Disabled directory must not select profiles")

    monkeypatch.setattr("apps.accounts.selectors.directory_profiles", forbidden)
    monkeypatch.setattr("apps.accounts.selectors.directory_student", forbidden)
    students = identities[0]
    for index, student in enumerate(students):
        save_persona(actor=student, **values(goal=f"PRIVATE_PERSONA_{index}"))
    for owner in students:
        others = [student for student in students if student != owner]
        client.force_login(owner)
        for path in (
            "/students/",
            *(f"/students/{student.studentprofile.pk}/" for student in students),
            "/students/99999999/",
        ):
            response = client.get(path)
            assert response.status_code == 404
            assert "no-store" in response["Cache-Control"]
            assert "PRIVATE_PERSONA_" not in response.text
            for other in others:
                assert other.studentprofile.full_name not in response.text
                assert other.studentprofile.group.code not in response.text
        response = client.get("/profile/")
        assert response.status_code == 200
        assert owner.studentprofile.full_name in response.text
        for other in others:
            assert other.studentprofile.full_name not in response.text
        assert 'href="/students/"' not in response.text
        editor = client.get("/profile/persona/")
        assert editor.status_code == 200
        assert owner.studentprofile.studentpersona.goal in editor.text
        for other in others:
            assert other.studentprofile.studentpersona.goal not in editor.text


@pytest.mark.parametrize("enabled", [False, True])
def test_empty_own_persona_describes_current_visibility(
    client,
    identities,  # noqa: F811
    settings,
    enabled,
):
    settings.ENABLE_STUDENT_DIRECTORY = enabled
    client.force_login(identities[0][0])
    response = client.get("/profile/")
    assert response.status_code == 200
    assert "Добавьте интересы, сильные стороны или цель на семестр." in response.text
    promise = "Вашу persōna смогут посмотреть другие студенты в каталоге."
    assert (promise in response.text) is enabled
