# Q04/U03 — отчёт исполнителя

Исходный HEAD76a7dc3,168tests. Один исполнитель Sol/low, без субагентов. Commit/push не выполнялись: требуется независимое accepted родителя.

## Изменения

- accounts.css: active login input cursor:text и контрастный существующий цвет; focus button/select/textarea/summary; skip link выше nav; mobile scroll padding/margin не дают nav перекрывать focused submit.
- accounts/forms.js и base: pageshow focus единственной сводки ошибок (после fragment navigation); history.js/auth/CSRF не менялись.
- login: aria-invalid/describedby, доступное объяснение и canonical native action. Реальные main#main получили tabindex=-1 для skip target; preview не менялся.
- requests: summary с field links и исходными Django errors, terminal/stale409 summary без ссылок на отсутствующие поля; native request-new action; active stale operator summary сохраняет GET refresh link и старую expected_version до явного обновления; подсказка проверить «Мои заявки», если ответ не пришёл.
- tests/ui_qa.py: собственный Q04 fixture с проверенным safe env/случайной DB/static/SECRET_KEY, finally cleanup из Q03; Gunicorn --threads4. Существующие fixtures не менялись.
- test_ui_accessibility_browser.py:11tests;4полных пути на360/390/768/1440 + keyboard/contrast/reflow/reduced motion/hit-test/errors, native network failure до POST, потеря ответа после реального commit и HTTP повтор того же CSRF/submission_key, operator validation, stale cancellation409 и active operator409→GET refresh→ready.

Подтверждённые дефекты до исправления: login cursor/цвет; отсутствие focus основных controls и summary; desktop nav перекрывала focused skip link (elementFromPoint=false); mobile nav перекрывала focused submit после scroll (hit-test не проходил даже после30s). Исправления проверены реальными браузерами.

## QA-контур

PG: `deanery-q04-20261106`, own label `deanery.qa=Q04-U03-20261106`, loopback55432; PostgreSQL17.11 pinned image из compose.local. Пользовательские dev/.env/ключи/порты5432/8000 не использовались.

Host Python3.13.14, locked Playwright1.64.1, Chromium156/Firefox157 из /tmp/deanery-browsers. Host WebKit27.2 не запускался из-за отсутствующих gtk4/gstreamer/libsoup runtime; ОС не изменялась. Согласованный fallback — browser-only официальный Docker `mcr.microsoft.com/playwright@sha256:2f05f8a734509a7b3f26a912639488ee08f58a7b292d14d62271bcff9038768f`. Digest получен реальным pull v1.64.1-noble. Container `deanery-q04-browser-20261106`, label `deanery.qa=Q04-U03-browser-20261106`; ws://127.0.0.1:53000/. Inspect подтвердил pwuser, mounts[], private IPC, privileged=false, CapAdd=null, единственный loopback mapping53000→3000. `expose_network='<loopback>'`; приложение/pytest/Python остаются host. Подробная команда и cleanup в docs/testing/ui-review.md.

Ранний sync1 Gunicorn QA блокировался browser preconnect: route.fetch Chromium и WebKit POST после #main висели. На том же приложении с threads4 проходят. Это starvation QA-контура, не HTML/CSRF дефект. Canonical actions/tabindex улучшают ясность/доступность и не заявляются исправлением starvation.

## Команды и фактические результаты

```text
DB_PORT=55432 TEST_DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers UPDATE_EVIDENCE=1 .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser-channel chromium -q
→ exit0,11passed47.18s
DB_PORT=55432 TEST_DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser firefox -q
→ exit0,11passed51.96s
DB_PORT=55432 TEST_DB_PORT=55432 Q04_PLAYWRIGHT_ENDPOINT=ws://127.0.0.1:53000/ .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser webkit -q
→ exit0,11passed53.67s
DB_PORT=55432 TEST_DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser firefox -k response_lost -q
→ exit0,1passed5.52s (после последнего уточнения exact UUID replay; остальной Firefox11 run выше)
```

Все browser runs выполнялись штатным require_escalated: sandbox runtime Chromium даёт shutdown EPERM. Единственное предупреждение pytest-playwright — существующий PytestRemovedIn10Warning.

PNG `screenshots/{request-360,request-390,request-768,request-1440,login-error-360,request-error-360,keyboard-1440}.png` сняты в viewport (без fullpage) только Chromium через UPDATE_EVIDENCE=1 для нового модуля. Исторические PNG не менялись.

## Ограничения

200% представлен equivalent CSS viewport720×500 для исходной1440×1000 области, не управлением системным zoom. Реальный аппаратный телефон, Safari/iOS/Android, системный zoom, публикация/РФ безVPN остаются pending; Q04 целиком не закрыт. Reduced motion проверяет computed scrollBehavior:auto, контраст активного input вычисляется по computed text/background и>=4.5. Это ограниченный аудит, не WCAG сертификация.

Native SSR формы сохраняют нативный browser progress/error document, не имитируют loading/success. Нет искусственного disabled/fetch. При abort до POST БД не меняется, повтор после открытия формы работает. При потере ответа после commit сохранённая карточка видна в списке, идентичное тело с прежним submission_key не создаёт дубликат.

Родителю оставляются только собственный PG и browser server для независимого rerun; временные web/static/browser DB очищаются fixture finally. Окончательные результаты WebKit/full regression/checks приведены в этом отчёте.

## Завершение проверок и write freeze

```text
DB_PORT=55432 TEST_DB_PORT=55432 TEST_DB_NAME=test_q04_suite PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest --browser-channel chromium -q
→ exit0,179passed,1warning,156.21s
.venv/bin/ruff check . → exit0,All checks passed
.venv/bin/ruff format --check . → exit0,183files formatted
git diff --check → exit0
```

Django `check` и `makemigrations --check --dry-run` выполнены последовательно после suite, на новой собственной случайной migrated test_browser_* через `ui_site.__wrapped__()` с safe subprocess env и finally generator.close(): exit0, «System check identified no issues», «No changes detected». После этого отдельный read-only запрос на собственной PG подтвердил `Remaining Q04 test DBs: []` (test_browser_* и test_q04_suite отсутствуют). Временные Gunicorn/static roots очищены фикстурами.

Оставлены для независимого rerun родителя и повторно inspected running:

- `/deanery-q04-20261106`, label `deanery.qa=Q04-U03-20261106`,127.0.0.1:55432→5432.
- `/deanery-q04-browser-20261106`, label `deanery.qa=Q04-U03-browser-20261106`,127.0.0.1:53000→3000, endpoint `ws://127.0.0.1:53000/`, image digest указан выше.

Write freeze. Код/скриншоты/документы исполнителя готовы к независимому ревью; статус accepted не присваивался. Git commit/push не выполнялись.
