from django.test import Client


def test_real_login_and_safe_csrf_without_database():
    client = Client(enforce_csrf_checks=True)
    response = client.get("/login/")
    assert response.status_code == 200
    assert b'name="csrfmiddlewaretoken"' in response.content
    assert b'name="password"' in response.content
    assert "no-store" in response["Cache-Control"]
    rejected = client.post("/login/", {"username": "example", "password": "not-a-secret"})
    assert rejected.status_code == 403
    assert "Обновите страницу" in rejected.content.decode()
    assert client.get("/profile/").url.startswith("/login/?next=")
    assert client.get("/logout/").status_code == 405
    assert client.get("/admin/").status_code == 404
    assert client.get("/signup/").status_code == 404
