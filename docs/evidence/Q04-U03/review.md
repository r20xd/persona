# Q04/U03 — независимая приёмка локального UI

- Постановка: [prompt.md](prompt.md), исходные наблюдения: [audit-notes.md](audit-notes.md).
- Исполнитель: Sol/low; результат: [implementation.md](implementation.md).
- Промежуточные замечания: [review-01.md](review-01.md), все7 устранены.
- Требования: PRD-02/03/04, CORE-01–05, TECH-02/03/06, SEC-01, BRAND-01.
- **Решение: accepted** в границах локальных Q04/U03; реальный телефон/системный zoom не закрыты. Версионирование на момент записи pending.

## Проверенный результат

Основной агент прочитал новый UI fixture, тест-модуль, forms.js, HTML/CSS diff, отчёты и новые изображения. Изменения ограничены UI semantics/стилями/новыми проверками; services, модели, auth/history.js, схема и зависимости/lock не менялись. Палитра сохранена, disabled preview не менялся.

| Область | Независимое подтверждение |
| --- | --- |
| Responsive путь | Chromium полный suite, Firefox/WebKit целевой модуль:360/390/768/1440, вход/профиль/учёба/расписание, заявка→оператор→готова, сохранение и чужая404 |
| Читаемость/фокус | Вычисленный input contrast>=4.5, активный cursor; aria-invalid/describedby, error summary focus, фокус controls, skip link hit-test над desktop nav и focusable main |
| Mobile/reflow | Focused submit после прокрутки не перекрыт fixed nav; long unbroken text не даёт overflow; reduced motion реально scrollBehavior:auto.720×500 — reflow эквивалент, не OS zoom |
| Ошибки/конфликт | Login/request/operator validation, terminal stale cancel409 и active operator409. Сохраняется старая expected_version до GET refresh; после него version2 и допустимый переход ready |
| Сеть | Abort до POST без записи; потеря ответа после фактического commit без ложного success, карточка доступна, повтор того же тела/CSRF/submission_key возвращает тот же UUID и не дублируется |
| Empty | Пустой фильтр заявок показывает объяснение/следующее действие, пустая дата расписания показывает отсутствие занятий; тест не выдаёт seed dataset за полностью пустую БД |
| Скриншоты | Основной агент открыл login-error360, keyboard1440, request390/768 и итоговый request-error360: палитра цельная, skip link виден, focused submit над nav.7 PNG — viewport captures только Chromium |

## Фактические команды основного агента

```text
env -u Q04_PLAYWRIGHT_ENDPOINT DJANGO_SETTINGS_MODULE=config.settings.test DB_PORT=55432 TEST_DB_PORT=55432 TEST_DB_NAME=test_q04_parent_full PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest --browser-channel chromium -q
→ exit0, 179 passed, 1 warning, 162.21s

env -u Q04_PLAYWRIGHT_ENDPOINT DJANGO_SETTINGS_MODULE=config.settings.test TEST_DB_PORT=55432 TEST_DB_NAME=test_q04_parent_firefox PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser firefox -q
→ exit0, 11 passed, 1 warning, 57.66s

DJANGO_SETTINGS_MODULE=config.settings.test TEST_DB_PORT=55432 TEST_DB_NAME=test_q04_parent_webkit Q04_PLAYWRIGHT_ENDPOINT=ws://127.0.0.1:53000/ PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser webkit -q
→ exit0, 11 passed, 1 warning, 58.25s

.venv/bin/ruff check .          → exit0
.venv/bin/ruff format --check . → exit0, 183 files already formatted
git diff --check               → exit0
```

Chromium11 входят в179 full suite;179+11+11 не выдаются за201 уникальный тест. Firefox/full частично выполнялись параллельно на разных configured TEST_DB_NAME и случайных test_browser_*; общий test DB/миграции не делились. UI fixture использует private static root. WebKit запущен после завершения Firefox; все tests после writer freeze. UPDATE_EVIDENCE не задавался, старые PNG не менялись.

Django check и makemigrations --check --dry-run основной агент выполнил через новую собственную ui_site fixture: сначала migrate/seed/private static/web, затем безопасный env явной созданной БД. Обе команды exit0: no issues/No changes detected, без warning. Generator finally закрыт, временная БД/web/static удалены. Финальный read-only pg_database audit показал remaining_qa_databases=[] для test_browser_* и трёх parent test names. Это отдельный QA PostgreSQL, пользовательский .env/dev не использовался.

## QA контур и разобранные замечания

Официальный browser-only Playwright1.64.1 Docker server соответствует locked version. [Документация Docker remote connection](https://playwright.dev/python/docs/docker#remote-connection) использована только для подготовки QA; host Python3.13/pytest/app остаются. Нужный host WebKit runtime отсутствовал. Exact image digest и команды — [ui-review.md](../../testing/ui-review.md). Независимый inspect подтвердил label, pwuser, private IPC, privileged=false, CapAdd=null, Mounts=[], только127.0.0.1:53000→3000. Endpoint fixture принимает loopback WS, expose_network только loopback. Никакого production/public bind/host package install.

Native hash POST прошёл независимый minimal ThreadingHTTPServer probe основного агента в WebKit с focusable/non-focusable main. При сравнении исполнителя sync1 блокировался, а threads4 устранил блокировку; это согласуется с QA preconnect starvation. Canonical action/tabindex не выдаются за исправление серверного CSRF дефекта. Реальные async requests/DB не подменялись mock. Основной агент также уточнил текущие локальные команды README/V2 до проверенных threads4; production-конфигурация не меняется.

Замечания review закрыты: фактические empty states, terminal focus, достижимый mobile submit, meaningful contrast/reduced-motion assertions и сохранённый refresh путь для active409. Последняя регрессия исходила из удаления общего refresh link при внедрении summary; link восстановлен до финальных прогонов, версия автоматически не подменяется. Код после независимых прогонов не менялся; последующие изменения только в документах основного агента.

## Границы и следующий шаг

Подтверждены desktop engines и CSS viewport/reflow. Реальные Safari/iOS/Android/телефон, системный zoom, настоящий BFCache, production TLS/CSP/proxy и доступность РФ не подтверждены. Это ограниченный аудит, не сертификация WCAG и не полный Q04 hardware sign-off. Q02 loss-after-commit теперь подтверждён controlled HTTP-response failure, а не аварией узла/диска в середине транзакции. Native browser progress/error сохранены; fetch/SPA/новых зависимостей нет.

Следующий блок — Q06, итоговая сверка Q01/Q02, затем production-контур/размещение после V2 и согласования ресурсов. Допустим обычный commit/push точного allowlist в main/origin с обязательным `атрибуция команды`, сверкой staged diff/trailer/remote SHA. После этого exact cleanup оставленных собственных PG и browser server по labels/портам; пользовательский dev/образы не трогать.
