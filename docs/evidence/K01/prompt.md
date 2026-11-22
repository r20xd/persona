# Задание исполнителю K01

Модель gpt-6.1-sol/low, fork_turns=none, один исполнитель без делегации. Основной агент задаёт архитектуру и независимо принимает. Исходный HEADархивная-версия, дерево чистое до новых root docs.

Читать TASK.md/AGENTS.md, ARCHITECTURE §§5–11, PLAN F08/Q, STATE, docs/ux/attention-and-digest.md (конкретный согласованный контракт), docs/agents/WORKFLOW.md. Изучить фактические dashboard/grade/schedule/request/notification selectors/models/services и tests/test_dashboard_demo.py, test_dashboard_browser.py, tests/ui_qa.py. Реализовать обе пользовательские функции как законченный результат, не только backend.

## Разрешённые файлы

- apps/dashboard/**: модели/additive миграция, selectors/services/forms/views и template partials.
- apps/accounts/views.py: только вызов начала отслеживания при успешном обычном student login; существующие redirects/CSRF/axes/ошибки не ослаблять.
- apps/accounts/urls.py: новый точный POST путь dashboard changes seen, существующий home/profile контракт сохранить.
- static/css/dashboard.css: новые доступные карточки в существующей палитре/360px.
- tests/test_attention.py, tests/test_attention_browser.py; tests/test_dashboard_demo.py только если выяснится обоснованное изменение query cost, сначала сообщить root. Прочие existing tests не менять молча.
- docs/evidence/K01/implementation.md, безопасные новые screenshots/aggregates K01 и собственный временный QA helper в /tmp при необходимости.

Root владеет ARCH/PLAN/STATE/prompt/review/docs/ux/versioning. Не менять schema соседних apps, lock/dependencies/infra/deploy/фальшивую историю уведомлений. Не добавлять JS/HTMX, если обычные HTML forms достаточны; CSP unchanged, данные только fictional. Все правила интерфейса/receipt токенов в docs/ux/attention-and-digest.md. Если видишь конфликт/существенное упрощение, быстро сообщи root; не меняй согласованный контракт самовольно.

## Приёмка

1. Главная показывает приоритеты с причинами/действиями и честные пустые/первые состояния; не выдумывает задолженность по отсутствию данных; радар независим от digest acknowledgement.
2. Сводка реальных grade publication/immutable schedule/request events строго scoped текущим собственным источникам. GET read-only. Первые записи до начала не выданы за новые; будущие/чужие не показаны. До3 детали/категорию, счётчики честные.
3. Подписанный user-bound limited token; CSRF POST ack только показанных exact identities/version dates. Новое событие после GET, поздний commit, обновление оценки, refresh, повторный старый POST и вкладки не стирают другое; нельзя подписать свой payload/подставить owner. УспехPRG/no-store, role/доступ fresh серверно.
4. Изменения совместимы с текущими источниками, миграция сохраняет существующие записи; seed повторяем, старые тесты проходят. Число запросов фиксированное; данных целиком в Python без ограничения выборки не грузить.
5. Browser login360/1440, новые детали и ack/refresh/relogin, новая заявка/операторский статус; доступность клавиатуры и reflow, реальные PNG только новой папки.

## Среда и проверки

.venv Python3.13.14, uv0.12.1; UV_CACHE_DIR=/tmp/deanery-uv-cache, UV_PYTHON_INSTALL_DIR=/tmp/deanery-python, PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers. Native Docker /mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe через штатную require_escalated; engine доступен. Без .env/private SSH/devБД5432/8000, mounts/prune/privileged. Уникальная own label и loopback port, credentials только private state не в argv/logs. Можно переиспользовать /tmp/deanery-root-suite-db.py create/check/cleanup, предварительно прочитать: helper создаёт isolated PG17.11-trixie и хранит private JSON, выводит только путь/owner. Явный --env-file NUL при Compose исключает чтение user .env. Все ресурсы точно чистить после owner check; retained DB для независимого root suite заранее передать и не удалять до указания.

Сначала код/targeted PostgreSQL+browser проверки и makemigrations --check/ruff. Один full suite после freeze основной агент выполнит независимо; не дублировать автоматически. Отдельно прогнать миграции на существующей модели с сохранённой заявкой и новые concurrency/security случаи. Передать root code freeze, команды/пути и private DB state безсекретов, отчёт о выполненном/непроверенном. До accepted/явного Git follow-up не commit/push, не публиковать сайт. После приёмки требуется обычный main/origin commit с атрибуция команды.
