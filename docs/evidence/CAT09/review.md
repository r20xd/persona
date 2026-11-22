# CAT09 — независимая приёмка

- **Статус кода и результата: accepted.** Версионирование: pending, отдельно от приёмки.
- Ревьюер: основной агент. Исполнитель: cat01, согласованный Sol/low, один writer без субагентов.
- Постановки: prompt.md, prompt-performance.md. Контракт: ARCHITECTURE §31. Требования: PRD-03/04, TECH-03/06, пользовательский запрос CAT09; серверные правила CAT01–CAT07 сохранены.
- Проверено финальное дерево после performance freeze, входы — source-sha256-release.txt. Исходные CAT08 и logoPNG не менялись; пользовательские файлы/.gitignore/.env не входят в этап.

## Что принято

Вместо исторических рисованных котов сайт использует внешний вид трёх CAT08 персонажей. Локальный renderer рисует48×48canvas, отдельно двигает голову/тело/хвост и меняет пиксели глаз/рта для7состояний. Source artwork/palette/rig/counts передаются из presentation-модели через json_script; ни ключей сервисов, ни внешних вызовов здесь нет. В обычном /cat/ и /profile/ загружаются компактные48PNG, а не1254мастера. Профиль рисует один исходный кадр; game state machine отвечает за движения только во время игры и реакции на действия. Pending/error source не блокирует Start/повторные раунды; canvas имеет доступное имя и обычный img fallback. Pause/hidden/calm/reduced сбрасывают кадр, profile/game-before-start остаются неподвижными.

Сцена и игрушки сохраняют целые физические пиксели приDPR1/1.25/2. CoreAPI/20секунд/12карточек/перестановки/награды/ownership/CSRF/сохранение не менялись; models/migrations/deps и ИИ-чат вне diff. ScopedCSS добавляет только размеры fallback/canvas. Дополнительная оптимизация brand/favicon меняет URL на96PNG, сохраняя геометрию/рисунок/навигацию; большой P-декор login остаётся прежним.

Root прочитал фактический renderer, cat.js diff, cat_card, шаблоны, CSS, devbuilder и тесты. Builder копирует только явные публичные inputs в собственный temp root, слушает loopback, завершает свой browser/server; не раздаёт repository/.env и не подключается к БД. Native режим валидирует48размер, binaryalpha и palette и не делает повторный crop. --check сравнивает decodedRGBA, не нестабильные между Chrome версиями байты PNG; все150raw/native frame hashes совпали. PNGмастера не правились, преобразование — экспорт фактического renderer.

## Независимые проверки

| Область | Фактический результат |
| --- | --- |
| Финальный frozen suite | **43 passed, 1 existing warning, 146.54s**, exit0; independent-tests-final.txt |
| Команда | `TEST_DB_PORT=55439 TEST_DB_NAME=test_cat09_root_final PLAYWRIGHT_BROWSERS_PATH=/tmp/persona-browsers UPDATE_CAT09_EVIDENCE=1 uv run --locked pytest tests/test_cat.py tests/test_cat_pixels.py tests/test_cat_browser.py tests/test_cat_renderer_browser.py tests/test_cat_art_build.py tests/test_design_browser.py -q` с UV_CACHE_DIR=/tmp/persona-uv-cache |
| Стабильность |27хешей кода/inputs/PNG/lock до и после совпали; source-sha256-release.txt. Контактный лист renderer до/после оптимизации совпал побайтно через cmp |
| Реальный renderer | Все150кадров:48grid, alpha0/255, до13RGBAзначений, прозрачные границы, одна крупная8-connected компонента;7различных middle poses на3характерах |
| Живой сценарий | Вход → игра/несколько раундов/timeout/retry → выбор4игрушек → профиль/повторный вход; keyboard, shuffle/focus, pause/calm/reduced/hidden, staticprofile, pending/failed source |
| Мобильность и оболочка | Реальный Chromium:360/390/768/1440, общая навигация/вход/основные разделы и keyboard narrow reflow; native physical screenshot blocks наDPR1/1.25/2 |
| Размеры/загрузка | RuntimePNG1532/1280/1400байт, logo10385байт; запросов heavy master/large logo в /cat/profile нет. Buildercheck работает при намеренно неверном DBport1 |
| Статика/синтаксис | Ruff check/format7изменённыхPythonфайлов, JSsyntax, Django previewcheck, diffcheck прошли |
| Локальный запуск | collectstatic5copied/242unmodified/64postprocessed, собственный GunicornHUP; health/live и readyok. НовыйHTTPchaos48PNG совпал с shippedfile через cmp |

Предыдущий вариант честно проверен отдельным36passed/120.13s,17hashes; затем исправлен только guard DPRснимков и выполнены3passed/13.55s. После реального perfFAIL код/ассеты изменились, поэтому root повторил весь релевантный suite и добавил shared-shell/build coverage. Первые результаты не выданы за финальные. Единственный warning — прежний PytestRemovedIn10Warning стороннего base_url fixture, не новая ошибка приложения.

## Визуальное ревью и исправления

Root просмотрел первоначальный contact, передал замечания по прямоугольной шее/резким глазам/хвосту (review-01.md), просмотрел исправленный contact. Удалена сплошная кремовая вставка, сохранён воротничок, surprise получил округлённые зрачки/блик и небольшой рот. Проверка всех кадров поймала реальный отрыв хвоста; исправлены границы/перекрытие исходных пикселей и связь с телом без ослабления теста. Финальный contact содержит узнаваемых CAT08 персонажей и разные выражения. Root также просмотрел реальные cat360, chaos-game360 и scholar-profile1440: новые рисунки видны,4игрушки рядом, швы/обрезка не обнаружены. Все прочие matrix screenshots сохранены тестами.

## Taste Skill

**GATE: OPEN 33 (rounds used up)**,31WARN, formalwaivers0. Полные обе версии gate и финальная классификация — taste-gate.txt, taste-gate-summary.json, taste-consistency-report.json, taste-classification.md. Применён Taste2.5.1, собственная палитра/персонажи и текущая функциональная раскладка сохранены. На каждом из двух вариантов задан1автоматический review round ограниченного visualpatch; вручную проведены отдельные итерации качества рисунка. Kit/правила не менялись, marketingPASS не заявляется. Открытые требования fullscreenhero/.wrap/dealtmoment и подобные не превращают личный кабинет в landing; существующий main:focus и прочие a11y/metadata замечания остаются явно открытыми вне CAT09. Каталог всех33FAIL/31WARN с причиной сохранения приведён в классификации.

Финальный **perf:0FAIL/2WARN**, exit0, taste-perf.txt. На1440transfer53.6KiB, на39042.4KiB, images13.7KiB, largest10.3KiB; прежние2660.5/1725.7KiB и2FAIL/7WARN сохранены в taste-perf-before.txt. Сохранились только lazy-warning для маленьких логотипа/fallback: это используемые заранее элементы UI, несколькоКиБ; дальнейшее усложнение загрузки не нужно. Это локальные CPU/snapshot измерения, не реальная скорость сети из России. Нулевые brokenrequests/CLS зафиксированы инструментом.

Обезличенный Django snapshot с review-onlyCSRF создан и actualTaste shoot360 просмотрен; он не подменяет livePOSTпроверки. Формы/reduced/частьwalk не проверены маркетинговым checker, но целевые сценарии выполнены отдельно реальным browser suite. Chrome/PGданы только для QA, новые productiondependencies отсутствуют.

## Решение и ограничения

Замечаний к результату CAT09 нет. Принять и версионировать явный allowlist. Общая сдача/интернет-публикация и исправление всех старых site-wide замечаний не входят в эту приёмку. В этой итерации не проверялись реальные устройства, Firefox/WebKit и публичный хостинг; статусы прошлых этапов их не заменяют. Постоянная пользовательская БД и исходники сохранены. Временный persona-cat09-qa проверен по имени/image/labelcat09/id8d0078ec0e1379e564816261c2a6c347266dc6a3931e212a619bbce65e61008f и остановлен после тестов; локальная devБД и сайт оставлены работающими.

GitSHA/обычныйpush/подтверждение remote фиксируются в versioning.md после действий. Requiredtrailer: `атрибуция команды`. До этого accepted не означает pushed.
