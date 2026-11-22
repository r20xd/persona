"""Session regressions against isolated PostgreSQL and production-style static serving."""

import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from urllib.request import urlopen

import psycopg
import pytest
from psycopg import sql


class PrivateSite(tuple):
    def __repr__(self):
        return "<isolated QA site>"


@pytest.fixture
def security_site():
    db_name = "test_browser_" + uuid.uuid4().hex
    db = {
        key: os.environ.get("TEST_DB_" + key.upper(), default)
        for key, default in {
            "host": "127.0.0.1",
            "port": "5432",
            "user": "deanery",
            "password": "",
        }.items()
    }
    password = secrets.token_urlsafe(24)
    process = None
    created = False
    with tempfile.TemporaryDirectory(prefix="q03-static-") as static_root:
        env = {
            key: value
            for key, value in os.environ.items()
            if key
            in {
                "PATH",
                "SYSTEMROOT",
                "WINDIR",
                "TEMP",
                "TMP",
                "HOME",
                "USERPROFILE",
                "PLAYWRIGHT_BROWSERS_PATH",
                "VIRTUAL_ENV",
            }
        }
        env.update(
            DJANGO_SETTINGS_MODULE="tests.session_qa_settings",
            DJANGO_DEBUG="0",
            DJANGO_SECRET_KEY=secrets.token_urlsafe(64),
            DB_NAME=db_name,
            QA_STATIC_ROOT=static_root,
        )
        env.update({"DB_" + key.upper(): str(value) for key, value in db.items()})
        env.update(
            {
                key: password
                for key in (
                    "DEMO_STUDENT_ONE_PASSWORD",
                    "DEMO_STUDENT_TWO_PASSWORD",
                    "DEMO_OPERATOR_PASSWORD",
                )
            }
        )
        try:
            with psycopg.connect(dbname="postgres", autocommit=True, **db) as admin:
                admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            created = True
            for command in (
                ["migrate", "--noinput"],
                ["seed_demo"],
                ["collectstatic", "--noinput"],
            ):
                subprocess.run(
                    [sys.executable, "manage.py", *command],
                    env=env,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            url = f"http://127.0.0.1:{port}"
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "gunicorn",
                    "config.wsgi:application",
                    "--bind",
                    f"127.0.0.1:{port}",
                ],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("QA server exited")
                try:
                    with urlopen(url + "/health/ready/", timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("QA server unavailable")
            yield PrivateSite((url, password, db_name, db))
        finally:
            try:
                if process is not None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
            finally:
                if created:
                    with psycopg.connect(dbname="postgres", autocommit=True, **db) as admin:
                        admin.execute(
                            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(db_name))
                        )


@pytest.mark.browser
def test_account_switch_refreshes_stale_tab(browser, security_site):
    from tests.test_requests_browser import login

    url, password, _, _ = security_site
    context = browser.new_context()
    try:
        first = context.new_page()
        login(first, url, "student.one", password)
        first.goto(url + "/requests/new/")
        first.get_by_label("Назначение справки").select_option("other")
        first.get_by_label("Пояснение", exact=False).fill("Незавершённая форма первого студента")
        second = context.new_page()
        second.goto(url)
        second.get_by_role("button", name="Выйти", exact=True).click()
        login(second, url, "student.two", password)
        first.bring_to_front()
        first.wait_for_function(
            "document.querySelector('textarea')?.value !== 'Незавершённая форма первого студента'"
        )
        first.wait_for_load_state("networkidle")
        assert (
            first.locator("textarea").count() == 0 or first.locator("textarea").input_value() == ""
        )
        first.goto(url + "/profile/")
        assert "Мирон" in first.content()
        assert "Арина" not in first.content()
    finally:
        context.close()


@pytest.mark.browser
def test_unchanged_session_preserves_form_and_logout_clears_other_tab(browser, security_site):
    from tests.test_requests_browser import login

    url, password, _, _ = security_site
    context = browser.new_context()
    independent = browser.new_context()
    try:
        first = context.new_page()
        login(first, url, "student.one", password)
        first.goto(url + "/requests/new/")
        first.get_by_label("Пояснение", exact=False).fill("Сохранить незавершённый текст")
        second = context.new_page()
        second.goto(url)
        first.bring_to_front()
        first.wait_for_timeout(250)
        assert first.get_by_label("Пояснение", exact=False).input_value() == (
            "Сохранить незавершённый текст"
        )
        other = independent.new_page()
        login(other, url, "student.two", password)
        second.get_by_role("button", name="Выйти", exact=True).click()
        first.bring_to_front()
        first.wait_for_url("**/login/?next=**")
        assert "Сохранить незавершённый текст" not in first.content()
        other.goto(url + "/profile/")
        assert "Мирон" in other.content()
    finally:
        context.close()
        independent.close()


@pytest.mark.browser
def test_login_cookie_rotation_logout_and_history(browser, security_site):
    from tests.test_requests_browser import login

    url, password, db_name, db = security_site
    context = browser.new_context()
    try:
        page = context.new_page()
        restored = []
        page.expose_binding("recordPageShow", lambda source, persisted: restored.append(persisted))
        page.add_init_script(
            "addEventListener('pageshow', e => window.recordPageShow(e.persisted))"
        )
        login(page, url, "student.one", password)
        cookie = next(item for item in context.cookies() if item["name"] == "sessionid")
        assert cookie["httpOnly"] and cookie["sameSite"] == "Lax"
        old_key = cookie["value"]
        page.goto(url + "/profile/")
        response = page.reload()
        assert "no-store" in response.headers["cache-control"]
        assert "private" in response.headers["cache-control"]
        page.get_by_role("button", name="Выйти", exact=True).click()
        with psycopg.connect(dbname=db_name, **db) as connection:
            assert (
                connection.execute(
                    "SELECT count(*) FROM django_session WHERE session_key=%s", [old_key]
                ).fetchone()[0]
                == 0
            )
        page.go_back()
        page.wait_for_load_state("networkidle")
        assert "Арина" not in page.content()
        assert "/login/" in page.url
        page.go_forward()
        assert "Арина" not in page.content()
        assert restored
        print(f"Q03 real navigation pageshow persisted={sum(restored)} of {len(restored)}")
        context.add_cookies([{**cookie, "value": old_key}])
        assert page.goto(url + "/profile/").status == 200  # login redirect followed
        assert "/login/" in page.url
    finally:
        context.close()


@pytest.mark.browser
@pytest.mark.parametrize("inactive", [False, True], ids=["expired", "deactivated"])
def test_stale_form_after_server_session_rejection(browser, security_site, inactive):
    from tests.test_requests_browser import login

    url, password, db_name, db = security_site
    context = browser.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        login(page, url, "student.one", password)
        page.goto(url + "/requests/new/")
        page.get_by_label("Назначение справки").select_option("other")
        page.get_by_label("Пояснение", exact=False).fill("Истёкшая форма")
        with psycopg.connect(dbname=db_name, **db) as connection:
            before = connection.execute("SELECT count(*) FROM requests_servicerequest").fetchone()[
                0
            ]
            if inactive:
                connection.execute(
                    "UPDATE accounts_user SET is_active=false WHERE username=%s", ["student.one"]
                )
            else:
                key = next(
                    item["value"] for item in context.cookies() if item["name"] == "sessionid"
                )
                connection.execute(
                    "UPDATE django_session SET expire_date=now()-interval '1 second' "
                    "WHERE session_key=%s",
                    [key],
                )
        page.get_by_role("button", name="Отправить заявку", exact=True).click()
        assert "/login/" in page.url
        with psycopg.connect(dbname=db_name, **db) as connection:
            assert (
                connection.execute("SELECT count(*) FROM requests_servicerequest").fetchone()[0]
                == before
            )
    finally:
        context.close()


@pytest.mark.browser
def test_user_text_and_announcement_xss_are_inert(browser, security_site):
    from tests.test_requests_browser import login

    url, password, db_name, db = security_site
    payload = (
        '<img src="invalid" onerror="window.xssExecuted=true">'
        "<script>window.xssExecuted=true</script>"
    )
    with psycopg.connect(dbname=db_name, **db) as connection:
        connection.execute("UPDATE notifications_announcement SET body=%s", [payload])
    context = browser.new_context()
    try:
        page = context.new_page()
        login(page, url, "student.one", password)
        page.goto(url + "/requests/new/")
        page.get_by_label("Назначение справки").select_option("other")
        page.get_by_label("Пояснение", exact=False).fill(payload)
        page.get_by_role("button", name="Отправить заявку", exact=True).click()
        assert page.get_by_text(payload, exact=True).count() > 0
        assert page.evaluate("window.xssExecuted === undefined")
        assert page.locator('img[src="invalid"]').count() == 0
        page.goto(url + "/notifications/")
        assert page.get_by_text(payload, exact=True).count() > 0
        assert page.evaluate("window.xssExecuted === undefined")
        assert page.locator('img[src="invalid"]').count() == 0
    finally:
        context.close()


@pytest.mark.browser
def test_broadcast_security_error_keeps_focus_fallback(browser, security_site):
    from tests.test_requests_browser import login

    url, password, _, _ = security_site
    context = browser.new_context()
    context.add_init_script("""
        window.BroadcastChannel = class {
          constructor() { throw new DOMException('Disabled by policy', 'SecurityError'); }
        };
    """)
    errors = []
    try:
        first = context.new_page()
        first.on("pageerror", lambda error: errors.append(error.name))
        login(first, url, "student.one", password)
        first.goto(url + "/profile/")
        assert "Арина" in first.content()
        second = context.new_page()
        second.goto(url)
        second.get_by_role("button", name="Выйти", exact=True).click()
        login(second, url, "student.two", password)
        first.bring_to_front()
        # Chromium headless may not emit real OS focus; explicit event exercises the fallback.
        first.evaluate("dispatchEvent(new Event('focus'))")
        first.wait_for_function("!document.body.textContent.includes('Арина')")
        first.wait_for_load_state("networkidle")
        assert "Мирон" in first.content()
        assert not errors
    finally:
        context.close()


@pytest.mark.browser
def test_persisted_handler_removes_private_dom_before_offline_reload(browser, security_site):
    from tests.test_requests_browser import login

    url, password, _, _ = security_site
    context = browser.new_context()
    try:
        page = context.new_page()
        login(page, url, "student.one", password)
        page.goto(url + "/profile/")
        page.route("**/profile/", lambda route: route.abort())
        # Synthetic handler test, explicitly separate from actual BFCache evidence.
        replacement = page.evaluate("""() => {
          dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}));
          return {text: document.body.textContent, retry: document.querySelector('#main a')?.href};
        }""")
        assert "Обновляем кабинет" in replacement["text"]
        assert "Арина" not in replacement["text"]
        assert replacement["retry"] == url + "/profile/"
    finally:
        context.close()


@pytest.mark.browser
def test_account_switch_from_invalid_post_uses_get_without_resubmission(browser, security_site):
    from tests.test_requests_browser import login

    url, password, db_name, db = security_site
    context = browser.new_context()
    try:
        first = context.new_page()
        methods = []
        dialogs = []
        first.on(
            "request",
            lambda request: (
                methods.append(request.method) if request.is_navigation_request() else None
            ),
        )
        first.on("dialog", lambda dialog: (dialogs.append(dialog.type), dialog.dismiss()))
        login(first, url, "student.one", password)
        first.goto(url + "/requests/new/")
        # Bypass the browser maxlength only, letting the real server reject the POST.
        first.get_by_label("Назначение справки").select_option("other")
        first.get_by_label("Пояснение", exact=False).evaluate(
            "element => { element.removeAttribute('maxlength'); element.value = 'x'.repeat(1001); }"
        )
        first.get_by_role("button", name="Отправить заявку", exact=True).click()
        assert first.locator("body").get_attribute("data-request-method") == "POST"
        with psycopg.connect(dbname=db_name, **db) as connection:
            before = connection.execute("SELECT count(*) FROM requests_servicerequest").fetchone()[
                0
            ]
        second = context.new_page()
        second.goto(url)
        methods.clear()
        second.get_by_role("button", name="Выйти", exact=True).click()
        login(second, url, "student.two", password)
        first.bring_to_front()
        first.wait_for_function("document.body.dataset.requestMethod === 'GET'")
        first.wait_for_load_state("networkidle")
        assert first.locator("textarea").count() == 0
        assert methods and all(method == "GET" for method in methods)
        assert not dialogs
        with psycopg.connect(dbname=db_name, **db) as connection:
            assert (
                connection.execute("SELECT count(*) FROM requests_servicerequest").fetchone()[0]
                == before
            )
    finally:
        context.close()
