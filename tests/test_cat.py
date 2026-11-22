"""CAT01 persistence, low-stakes rewards, authorization and request integrity."""

import json
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client

from apps.accounts.cat import own_cat, save_cat
from apps.accounts.models import StudentCat
from tests.test_accounts import identities  # noqa: F401

pytestmark = pytest.mark.django_db


def settings(**overrides):
    return {"name": "Бублик", "character": "chaos", "toys": [], **overrides}


def begin(client):
    with patch("apps.accounts.cat.time.time", return_value=1000):
        response = client.post("/cat/start/")
    assert response.status_code == 200
    assert response.json()["seconds"] == 20
    return response.json()


def payload(attempt):
    first, swapped, third = attempt["initial"]
    return {
        "token": attempt["token"],
        "swap_from": swapped,
        "collected": [first, third, attempt["replacement"]],
    }


def finish(client, data, now=1003):
    with patch("apps.accounts.cat.time.time", return_value=now):
        return client.post("/cat/finish/", json.dumps(data), content_type="application/json")


def test_get_and_settings_persistence(client, identities):  # noqa: F811
    client.force_login(identities[0][0])
    for path in ("/cat/", "/profile/"):
        response = client.get(path)
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
    assert StudentCat.objects.count() == 0
    assert client.post("/cat/", settings()).status_code == 302
    cat = own_cat(identities[0][0])
    assert (cat.name, cat.character, cat.accessory) == ("Бублик", "chaos", "none")
    assert "Бублик" in client.get("/profile/").text
    assert "Прикладной тыгыдык" in client.get("/profile/").text
    assert "Тапок в рюкзаке?" in client.get("/profile/").text
    client.logout()
    client.force_login(identities[0][0])
    assert 'value="Бублик"' in client.get("/cat/").text
    client.post("/cat/", settings(name='<script>alert("x")</script>'))
    # Too long is rejected and previous value kept.
    assert own_cat(identities[0][0]).name == "Бублик"
    client.post("/cat/", settings(name="<b>Кот</b>"))
    assert "&lt;b&gt;Кот&lt;/b&gt;" in client.get("/profile/").text


def test_four_rewards_replay_and_locked_accessory(client, identities):  # noqa: F811
    user = identities[0][0]
    client.force_login(user)
    assert client.post("/cat/", settings(toys=["fish"])).status_code == 200
    assert StudentCat.objects.count() == 0
    for index, accessory in enumerate(("yarn", "ball", "mouse", "fish"), 1):
        attempt = begin(client)
        data = payload(attempt)
        response = finish(client, data)
        assert response.status_code == 200
        assert "no-store" in response["Cache-Control"]
        assert response.json()["completed"] == index
        assert finish(client, data).json()["duplicate"] is True
        assert own_cat(user).completed == index
        assert client.post("/cat/", settings(toys=[accessory])).status_code == 302
        assert own_cat(user).accessory == accessory
    old = data
    begin(client)
    assert finish(client, old).status_code == 400
    assert own_cat(user).completed == 4
    assert 'data-toys="fish"' in client.get("/profile/").text


def test_forged_instant_and_expired_finishes(client, identities):  # noqa: F811
    client.force_login(identities[0][0])
    attempt = begin(client)
    valid = payload(attempt)
    invalid = [
        {**valid, "token": "fake"},
        {**valid, "score": 100},
        {**valid, "collected": attempt["initial"]},
        {**valid, "collected": [valid["collected"][0]] * 3},
        {**valid, "swap_from": valid["collected"][0]},
        {**valid, "collected": [True, [], {}]},
        {**valid, "swap_from": []},
    ]
    for data in invalid:
        assert finish(client, data).status_code == 400
    assert finish(client, valid, now=1000).status_code == 400
    assert finish(client, valid, now=9000).status_code == 400
    assert client.post("/cat/finish/", "[", content_type="application/json").status_code == 400
    assert StudentCat.objects.count() == 0


def test_own_state_roles_and_csrf(client, identities):  # noqa: F811
    students, operator = identities
    first, second = students[:2]
    save_cat(first, settings(name="Личный первый кот"))
    client.force_login(second)
    assert "Личный первый кот" not in client.get("/profile/").text
    assert "Личный первый кот" not in client.get("/cat/").text
    client.post("/cat/", {**settings(), "student_id": first.studentprofile.pk, "owner": first.pk})
    assert own_cat(first).name == "Личный первый кот"
    first_client = Client()
    first_client.force_login(first)
    stolen = payload(begin(first_client))
    assert finish(client, stolen).status_code == 400
    assert own_cat(first).completed == 0
    assert client.get(f"/cat/{first.studentprofile.pk}/").status_code == 404
    client.force_login(operator)
    for path in ("/cat/", "/cat/start/", "/cat/finish/"):
        assert client.post(path, {}).status_code == 403
    with pytest.raises(PermissionDenied):
        save_cat(operator, settings())
    missing = get_user_model().objects.create_user(username="missing-cat")
    client.force_login(missing)
    assert client.get("/cat/").status_code == 403
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(first)
    for path in ("/cat/", "/cat/start/", "/cat/finish/"):
        assert csrf.post(path, {}).status_code == 403
    csrf.logout()
    assert csrf.get("/cat/").status_code == 302
    first_client.logout()
    assert first_client.post("/cat/finish/", {}).status_code == 302


def test_service_validation_rolls_back(client, identities):  # noqa: F811
    with pytest.raises(ValidationError):
        save_cat(identities[0][0], settings(toys=["fish"]))
    assert StudentCat.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_additive_migration_preserves_existing_profiles(identities):  # noqa: F811
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    from apps.accounts.models import StudentProfile

    def snapshot():
        return list(
            StudentProfile.objects.order_by("pk").values_list(
                "pk", "user_id", "full_name", "course", "group_id", "user__password"
            )
        )

    before = snapshot()
    executor = MigrationExecutor(connection)
    executor.migrate([("accounts", "0003_studentpersona")])
    try:
        MigrationExecutor(connection).migrate([("accounts", "0004_studentcat")])
        assert snapshot() == before
        assert StudentCat.objects.count() == 0
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())


def test_repeated_rounds_reject_previous_receipt_and_bad_json(client, identities):  # noqa: F811
    client.force_login(identities[0][0])
    first = payload(begin(client))
    assert finish(client, first).json()["completed"] == 1
    second = payload(begin(client))
    assert second["token"] != first["token"]
    assert finish(client, first).status_code == 400
    assert finish(client, second).json()["completed"] == 2
    assert finish(client, second).json()["duplicate"] is True
    for body in (b"\xff", b"null", b"[]", b'{"token":[]}', b"x" * 2049):
        response = client.post("/cat/finish/", body, content_type="application/json")
        assert response.status_code == 400
    assert own_cat(identities[0][0]).completed == 2


@pytest.mark.parametrize("character", ["sleepy", "scholar", "chaos"])
def test_character_art_is_selected_in_own_page_and_profile(client, identities, character):  # noqa: F811
    client.force_login(identities[0][0])
    client.post("/cat/", settings(character=character))
    for path in ("/cat/", "/profile/"):
        response = client.get(path)
        assert response.status_code == 200
        assert (f"cat-assistant-style48/{character}.png") in response.text
        assert 'data-character="' + character + '"' in response.text


def test_twelve_items_have_unique_ids_and_generated_wardrobe(client, identities):  # noqa: F811
    from apps.accounts.cat import ITEMS

    assert len(ITEMS) == 12 and len({item["id"] for item in ITEMS}) == 12
    assert {"headphones", "key", "tea", "alarm", "yarn"} <= {item["id"] for item in ITEMS}
    user = identities[0][0]
    client.force_login(user)
    cat = save_cat(user, settings())
    cat.completed = 4
    cat.save(update_fields=["completed"])
    for accessory in ("yarn", "ball", "mouse", "fish"):
        client.post("/cat/", settings(toys=[accessory]))
        for path in ("/cat/", "/profile/"):
            response = client.get(path)
            assert f"toy-{accessory}" in response.text
            assert f"images/cat-pixel48/toy-{accessory}.png" in response.text


@pytest.mark.django_db(transaction=True)
def test_pixel_toy_migration_preserves_legacy_state_and_reverses(identities):  # noqa: F811
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    from apps.accounts.models import StudentProfile, User

    students = list(identities[0])
    fourth = User.objects.create_user(username="fictional-fourth-cat")
    StudentProfile.objects.create(
        user=fourth,
        full_name="Вымышленный Четвёртый",
        course=2,
        group=students[0].studentprofile.group,
    )
    students.append(fourth)
    executor = MigrationExecutor(connection)
    executor.migrate([("accounts", "0004_studentcat")])
    try:
        historical = executor.loader.project_state([("accounts", "0004_studentcat")]).apps
        model = historical.get_model("accounts", "StudentCat")
        old = ["scarf", "glasses", "gown", "mug"]
        for index, (user, accessory) in enumerate(zip(students, old, strict=True)):
            model.objects.create(
                student_id=user.studentprofile.pk,
                name=f"Кот {index}",
                character="chaos",
                completed=index + 1,
                last_attempt=f"old-receipt-{index}",
                accessory=accessory,
            )
        before = list(
            model.objects.order_by("pk").values_list(
                "student_id", "name", "character", "completed", "last_attempt"
            )
        )
        MigrationExecutor(connection).migrate([("accounts", "0005_cat_pixel_toys")])
        assert (
            list(
                StudentCat.objects.order_by("pk").values_list(
                    "student_id", "name", "character", "completed", "last_attempt"
                )
            )
            == before
        )
        assert list(StudentCat.objects.order_by("pk").values_list("accessory", flat=True)) == [
            "yarn",
            "ball",
            "mouse",
            "fish",
        ]
        MigrationExecutor(connection).migrate([("accounts", "0004_studentcat")])
        assert list(model.objects.order_by("pk").values_list("accessory", flat=True)) == old
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())


def test_multiple_toys_canonical_validation_clear_and_isolation(client, identities):  # noqa: F811
    first, second = identities[0][:2]
    cat = save_cat(first, settings())
    cat.completed = 4
    cat.save(update_fields=["completed"])
    client.force_login(first)
    assert client.post("/cat/", settings(toys=["fish", "yarn", "fish"])).status_code == 302
    cat.refresh_from_db()
    assert cat.toys == ["yarn", "fish"] and cat.accessory == "yarn"
    client.logout()
    client.force_login(first)
    assert 'data-toys="yarn,fish"' in client.get("/cat/").text
    for invalid in (["fake"], ["yarn", "gown"], "yarn"):
        with pytest.raises(ValidationError):
            save_cat(first, settings(toys=invalid))
    cat.refresh_from_db()
    assert cat.toys == ["yarn", "fish"]
    client.force_login(second)
    response = client.post("/cat/", settings(toys=["fish"], owner=first.pk))
    assert response.status_code == 200
    assert own_cat(second) is None
    cat.refresh_from_db()
    assert cat.toys == ["yarn", "fish"]
    assert client.post("/cat/", settings(owner=first.pk)).status_code == 302
    assert own_cat(second).toys == []
    assert own_cat(first).toys == ["yarn", "fish"]
    client.force_login(first)
    assert client.post("/cat/", settings()).status_code == 302
    cat.refresh_from_db()
    assert cat.toys == [] and cat.accessory == "none"


@pytest.mark.django_db(transaction=True)
def test_multiple_toy_migration_preserves_receipt_and_legacy_selection(identities):  # noqa: F811
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    executor.migrate([("accounts", "0005_cat_pixel_toys")])
    try:
        historical = executor.loader.project_state([("accounts", "0005_cat_pixel_toys")]).apps
        model = historical.get_model("accounts", "StudentCat")
        cat = model.objects.create(
            student_id=identities[0][0].studentprofile.pk,
            name="До миграции",
            character="scholar",
            completed=4,
            last_attempt="fictional-receipt",
            accessory="mouse",
        )
        MigrationExecutor(connection).migrate([("accounts", "0006_cat_multiple_toys")])
        current = StudentCat.objects.get(pk=cat.pk)
        assert (
            current.name,
            current.completed,
            current.last_attempt,
            current.accessory,
            current.toys,
        ) == ("До миграции", 4, "fictional-receipt", "mouse", ["mouse"])
        current.toys = ["yarn", "fish"]
        current.accessory = "yarn"
        current.save(update_fields=["toys", "accessory"])
        MigrationExecutor(connection).migrate([("accounts", "0005_cat_pixel_toys")])
        assert model.objects.get(pk=cat.pk).accessory == "yarn"
    finally:
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
