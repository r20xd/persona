"""CAT10: own-only read projection, one JOIN, no GET writes or new endpoints."""

import json
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from apps.accounts.context_processors import cat_cameo
from apps.accounts.models import StudentCat
from tests.test_accounts import identities  # noqa: F401

pytestmark = pytest.mark.django_db


def project(user, route="home", method="get"):
    request = getattr(RequestFactory(), method)("/")
    request.user = user
    request.resolver_match = SimpleNamespace(url_name=route)
    return cat_cameo(request)


def test_owner_projection_single_query_and_no_write(identities, django_assert_num_queries):  # noqa: F811
    first, second = identities[0][:2]
    StudentCat.objects.create(student=first.studentprofile, name="Лапа", character="chaos")
    StudentCat.objects.create(student=second.studentprofile, name="Чужой", character="scholar")
    for user, name in ((first, "Лапа"), (second, "Чужой")):
        with django_assert_num_queries(1):
            value = project(user)
        cameo = value["cat_cameo"]
        assert cameo["name"] == name
        assert set(cameo) == {"name", "character_label", "renderer", "quote"}
        assert not any(
            key in json.dumps(value) for key in ("password", "full_name", "last_attempt")
        )
        owner = value["cat_walk_preference"]["owner"]
        assert len(owner) == 40 and owner != str(user.pk)
    assert project(first)["cat_walk_preference"] != project(second)["cat_walk_preference"]
    with django_assert_num_queries(1):
        default = project(identities[0][2])
    assert default["cat_cameo"]["name"] == "Плюш"
    assert StudentCat.objects.count() == 2


def test_exclusions_and_cat_toggle(identities, django_assert_num_queries):  # noqa: F811
    first = identities[0][0]
    empty = get_user_model().objects.create_user(username="no-profile")
    assert project(empty) == {}
    for user in (AnonymousUser(), identities[1]):
        with django_assert_num_queries(0):
            assert project(user) == {}
    for route in ("profile", "request-new", "persona-edit", "login"):
        with django_assert_num_queries(0):
            assert project(first, route) == {}
    assert project(first, method="post") == {}
    first.is_active = False
    assert project(first) == {}
    first.is_active = True
    toggle = project(first, "cat")
    assert set(toggle) == {"cat_walk_preference"}


def test_rendered_routes_are_own_and_do_not_duplicate_renderer(client, identities, settings):  # noqa: F811
    settings.ENABLE_STUDENT_DIRECTORY = True
    first, second = identities[0][:2]
    StudentCat.objects.create(student=first.studentprofile, name="Свой Кот", character="chaos")
    StudentCat.objects.create(student=second.studentprofile, name="Чужой Кот", character="scholar")
    client.force_login(first)
    for path in (
        "/",
        "/schedule/",
        "/grades/",
        "/assistant/",
        "/requests/",
        "/notifications/",
        "/students/",
        f"/students/{second.studentprofile.pk}/",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert "no-store" in response["Cache-Control"]
        assert "Свой Кот" in response.text and "Чужой Кот" not in response.text
        assert response.text.count('id="cat-renderer-config"') == 1
        assert response.text.count("data-cat-cameo hidden") == 1
    for path in ("/profile/", "/cat/"):
        html = client.get(path).text
        assert "data-cat-cameo hidden" not in html
        assert html.count('id="cat-renderer-config"') == 1
    assert "data-cat-walk-toggle" in client.get("/cat/").text
    assert StudentCat.objects.count() == 2


def test_page_question_pools(identities):  # noqa: F811
    from apps.accounts.cat_feedback import QUESTION_POOLS
    from apps.accounts.context_processors import READ_ROUTES

    for route in READ_ROUTES:
        questions = project(identities[0][0], route)["cat_rating_questions"]
        assert len(questions) >= 2
        assert len({item["key"] for item in questions}) == len(questions)
        assert route in QUESTION_POOLS


def test_rating_owner_validation_and_update(client, identities):  # noqa: F811
    from apps.accounts.models import CatPageRating

    first, second = identities[0][:2]
    for user, value in ((first, "2"), (second, "5"), (first, "4")):
        client.force_login(user)
        response = client.post(
            "/cat/rating/",
            {"question": "home.site", "rating": value, "student": second.studentprofile.pk},
        )
        assert response.status_code == 200
        assert response.json() == {"question": "home.site", "rating": int(value)}
    assert CatPageRating.objects.count() == 2
    assert CatPageRating.objects.get(student=first.studentprofile).rating == 4
    assert CatPageRating.objects.get(student=second.studentprofile).rating == 5
    for value in ("0", "6", "1.0", "", "NaN"):
        assert (
            client.post("/cat/rating/", {"question": "home.site", "rating": value}).status_code
            == 400
        )
    assert client.post("/cat/rating/", {"question": "unknown", "rating": "3"}).status_code == 400
    assert client.get("/cat/rating/").status_code == 405
    client.force_login(identities[1])
    assert client.post("/cat/rating/", {"question": "home.site", "rating": "3"}).status_code == 403
    client.logout()
    assert client.post("/cat/rating/", {"question": "home.site", "rating": "3"}).status_code == 403


def test_rating_csrf_and_database_constraints(identities):  # noqa: F811
    from django.db import IntegrityError, transaction
    from django.test import Client

    from apps.accounts.models import CatPageRating

    user = identities[0][0]
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    assert client.post("/cat/rating/", {"question": "home.site", "rating": "5"}).status_code == 403
    for value in (0, 6):
        with pytest.raises(IntegrityError), transaction.atomic():
            CatPageRating.objects.create(
                student=user.studentprofile, question="home.site", rating=value
            )
    CatPageRating.objects.create(student=user.studentprofile, question="home.site", rating=5)
    with pytest.raises(IntegrityError), transaction.atomic():
        CatPageRating.objects.create(student=user.studentprofile, question="home.site", rating=4)
