# CAT10 — независимая приёмка

**Статус: accepted. Версионирование: pending, отдельно от приёмки.**

Ревьюер — основной агент, исполнитель — прежний cat01/Sol-low, один writer. Постановка prompt.md, контракт ARCHITECTURE §32, PLAN CAT10. Покрыты пользовательский CAT10, PRD-02/03/04/05, TECH-03/06, SEC-01. Root прочитал фактические context processor, JS/CSS, partial/settings/base и тесты, затем выполнил независимые проверки. Это приёмка дополнения, не всей конкурсной работы.

## Результат и границы

На whitelist читаемых вкладок появляется собственный выбранный кот, с настоящим перемещением/подпрыгиванием. Клик/Enter/Space останавливает, вызывает радость и открывает реплику с переходом к коту/скрытием/отключением. Первая прогулка8–18секунд и дальнейший интервал90–180секунд — локальные инженерные настройки; timestamp разделяется между навигациями/окнами аккаунта. Browser preference содержит только boolean/time с opaque salted HMAC ключом, не имя или учебные данные. На странице кота настройку можно снова включить; no-JS/POST-error не показывает неработающий checkbox.

Context processor делает один LEFT JOIN только по request.user.pk активного студента с профилем. В HTML whitelist presentation своего кота; чужой ORM/User/оценки/last_attempt/секреты не передаются. Default cat при отсутствии записи не создаёт её. Guest/operator/no-profile и исключённые маршруты не получают cameo. При просмотре чужой карточки каталога остаётся свой питомец. GET не пишет состояние, моделей/миграций/endpoints/deps нет. Game/profile и награды/20секунд/12карточек/игрушки/статичный профиль остаются прежними; renderer/assets не менялись, дублирования экземпляров нет.

Root потребовал до freeze: desktop-путь справа от sidebar, корректный clamp по высоте, ограничение bubble и DPR-размер, остановку скрытых/выключенных таймеров без вечного5s polling, progressive checkbox и зеркальную маску в screenshot test. Исправления прочитаны и проверены. Ввод/диалог/hidden/reduced подавляют показ, resume событийный; pagehide очищает RAF/timeout/observer. Только pet/bubble перехватывают pointer; нет full-screen interaction layer. Focus/hover останавливают движение, первоначального focus-steal нет, Escape/close возвращают фокус. Низкий экран откладывает показ либо ограничивает облачко скроллом, mobile nav остаётся доступной. Storage failure сохраняет только memory-настройку до закрытия страницы и не ломает кабинет.

## Независимые проверки

- **49 passed, 1 existing warning,232.66s**, exit0: independent-tests.txt. Команда `TEST_DB_PORT=55439 TEST_DB_NAME=test_cat10_root PLAYWRIGHT_BROWSERS_PATH=/tmp/persona-browsers UPDATE_CAT10_EVIDENCE=1 uv run --locked pytest tests/test_cat_cameo.py tests/test_cat_cameo_browser.py tests/test_cat.py tests/test_cat_browser.py tests/test_cat_renderer_browser.py tests/test_cat_art_build.py tests/test_design_browser.py tests/test_dashboard_demo.py::test_dashboard_bounded_queries tests/test_attention.py::test_started_digest_query_count_is_bounded -q` с UV_CACHE_DIR=/tmp/persona-uv-cache.
- Проверены два владельца, projection/query count/no-write, отсутствие payload на исключённых страницах, один renderer и отсутствие чужого кота на прямой каталожной странице. Все прежние игровые/сохранения/CSRF/owner проверки входят в suite.
- Реальный Chromium: run360/hop1440, координаты и пиксели, click events через Enter/Space, popup/44px/Escape/focus, navigation cooldown, выключение/включение, reduced/hidden/input/storage failures, BFcache privacy reload, resize320×400, равномерные3devicepixel-блоки приDPR1.25. Shared-shell/вход/все основные разделы и query budgets также прошли.
-21исходный хеш кода/новых тестов/inputs до и после совпал: source-sha256.txt. Ruff/format трёх новых Python файлов, JSsyntax, Django previewcheck и diffcheck прошли. Existing warning — PytestRemovedIn10Warning стороннего base_url fixture; dependencies не менялись.
- Root просмотрел clicked360 и actualTaste clicked360 приh900: кот выше nav, маленький panel в viewport, controls не менее44px. Остальные run/hop/DPR/desktop screenshots сохранены.

## Taste и представление снимков

**GATE: OPEN40,36WARN**, formal waivers0. Одна review round ограниченного изменения workspace, не полный landing redesign; kit не менялся, PASS не заявляется. Полные findings и причины сохранения — taste-gate.txt, JSON и taste-classification.md. Нет open-findings с selector нового cameo; замечания относятся к неизменённым dashboard/навигации/fullscreen-layout требованиям. Существующий main:focus и другие site-wide a11y/layout замечания не объявляются исправленными.

Первый actual shoot исполнителя использовал default-height780 для page.content с inline координатами живого viewport900: повторное исполнение сериализованного open-state не пересчитало его как новый показ. Ограничение сохранено в отчёте, не выдано за production defect/исправленный тест. Root повторил shoot с исходной высотой900: taste-clicked-360-900.png, exit0, просмотрен. Для проверок разных ширин root снял **настоящий initial GET** отдельной изолированной fixture: rendered-home-initial.html, cameo скрыт как в серверном partial, CSRF заменён placeholder. Код/visibility controls не менялись для checker. Первая попытка capture не прошла только из-за default wait_for_selector(visible) на намеренно скрытом renderer; затем ожидалась готовность dataset, а не видимость. Fixture/browser/БД закрыты в finally. Снимок не подменяет live POST/geometry tests.

Финальный perf **0FAIL/2WARN**, exit0: transfer46.8/36.5KiB на1440/390, CLS0, broken requests0. Остались lazy-warning для маленьких используемых logo/fallback; большие мастера не загружаются. Это локальный snapshot/CPU результат, не измерение российской сети или публичного хостинга.

## Локальное обновление и решение

Collectstatic:2copied/247unmodified/66postprocessed, затем HUP собственного Gunicorn по существующему pidfile. Health/live и ready вернулиok. Временный postgres persona-cat10-qa проверен по имени/labelcat10/id a3e278391454dbe2a4de28b3e2ef3a262f17042db4c5f42ad26abe17ff49bf6c и остановлен, пользовательская devБД и сайт оставлены работающими. Новых user credentials/keys не создавалось, .env/.gitignore/личные картинки/старые evidence не включаются.

Принять CAT10 и выполнить обычный commit/push по явному allowlist. Публичного развёртывания, настоящего устройства и Firefox/WebKit в этой итерации не проверяли. При заблокированном storage настройка не переносится между страницами — это явное ограничение fallback, а не server security. GitSHA и подтверждение origin/main — versioning.md после отправки; required Co-authored-by trailer сохраняется.
