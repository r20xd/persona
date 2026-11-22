# Q03 — безопасность входа, сессий и нескольких вкладок

- Исполнитель: `gpt-6.1-sol / low`, один writer, без субагентов.
- Исходное состояние: main чистый, Q05 pushed9d5bd762;152tests. Настоящие Django sessions/CSRF/Axes/Argon2, no-store, pageshow.persisted reload уже есть. Пользователь запускает свой dev-кабинет — .env, пароли, БД, порты5432/8000 и его процессы не трогать. Ключи SSH не читать.
- Требования: SEC-01/02, PRD-05, CORE-01/04, TECH-03/06. PLAN Q03 и ограниченная часть Q04; ARCHITECTURE session/security/HTTP/UX. Прочитать TASK.md, AGENTS.md, нужные разделы PLAN/ARCHITECTURE, docs/agents/TASK_TEMPLATE.md и WORKFLOW.md. Родитель проводит независимое ревью/приёмку.

## Цель

Проверить настоящий браузерный сценарий сессий/форм и исправить подтверждённые дефекты. Не повторять уже покрытые проверки буквально. Доставить один законченный локально проверенный результат, не объявлять всё production security/Q04 выполненным.

1. PostgreSQL+Chromium+DEBUG=False Gunicorn/WhiteNoise: login меняет session key, cookie HttpOnly/SameSite, logout только CSRF POST и инвалидирует серверную сессию. После logout/back/forward и BFCache нет работоспособного старого кабинета; старый session cookie и прямой URL не дают доступ.
2. Реальные вкладки одного browser context: студентA в двух вкладках → во второй logout/login студентB → первая не должна продолжать показывать A после возвращения к ней или отправлять старую форму как B. Отдельные contexts сохраняют независимые сессии. Старый CSRF hidden token после нового login должен быть отклонён сервером, даже если JS отключён. Не выдавать JS за авторизацию.
3. Истёкшая session и деактивация пользователя: вход/безопасная ошибка при следующем действии, заявка не создаётся от гостя/другого пользователя. Устаревшая форма и запрет CSRF не показывают ложный success и дают рабочее следующее действие.
4. XSS в пользовательском тексте/объявлении показывается текстом без исполнения в браузере. Private ответы no-store и no shared-cache; внешний next не открывается, error не раскрывает secrets/DSN/traceback. Существенно новые сценарии only, существующие unit tests читать и использовать как покрытие.
5. Проверить production cookie/HTTPS settings на безопасных synthetic values; реальный Caddy/CSP/proxy/HSTS и публичный HTTPS пока D02, не объявлять их подтверждёнными. Не ослаблять CSRF/Axes/session policy и не подменять auth тестовым bypass.
6. Реальный дефект из диалога: provision_accounts скрывает причину плохого пароля общим CommandError и ловит Exception. Сделать понятные причины штатного Django ValidationError (минимальная длина/числа/common/similarity), без вывода введённого пароля, без ослабления validators и сброса существующих паролей. Проверить transaction rollback и отсутствие секретной строки в ошибке; неожиданные ошибки не маскировать как неправильный пароль.

## Реализация при найденном дефекте вкладок

Сначала воспроизведи на существующем history.js и сообщи родителю факты и минимальный вариант исправления. Если нужен новый endpoint/contextprocessor/cookie или изменение архитектуры — дождись краткого решения родителя по конкретному контракту, продолжая независимые тесты. Не добавляй постоянный polling, JWT, SPA, localStorage/sessionStorage с персональными данными, раскрытие raw session key, публичный API или сторонние зависимости. Решение не должно перезагружать/терять незавершённую форму при каждом обычном фокусе, если сессия не менялась. Недоступность сервера не даёт фальшивых данных; JS выключен — серверные права/CSRF всё равно работают. Учитывать параллельные focus/visibility/pageshow без циклов запросов.

## Владение файлами

Разрешено: apps/accounts/static/accounts/history.js; apps/accounts/views.py, urls.py, templates/accounts/{base,login,access_error}.html для подтверждённого исправления; provision_accounts.py для конкретного password validation; новые tests/test_session_security.py и tests/test_session_security_browser.py, при нужде узкий tests helper/QA settings с временной static root; docs/testing/security-review.md; README.md только изменившееся поведение/запуск; docs/evidence/Q03/implementation.md и безопасные результаты. Новые accounts middleware/contextprocessor/helper и регистрация в settings.base — только после решения родителя. Shared auth services/models/schema/migrations/зависимости/lock/CI/другие модули — read only до конкретного согласования. TASK/AGENTS/ARCHITECTURE/PLAN/STATE и prompt/review изменяет только родитель.

## Проверки и QA

- Никакого чтения .env и реальных доступов. Own PostgreSQL17.11 pinned digest из compose.local, уникальный container label/name, loopback55432 если свободен; чужой сервис не останавливать. Native Windows Docker CLI `/mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe` через штатную require_escalated. Не менять системные права/группы. Disposable trust только своей QA БД.
- Браузер использует отдельную own test_browser_* DB, динамический loopback port и временную static root; cleanup в finally охватывает также setup failures. Env приложения очищен от пользовательских DB/SECRET/DEMO; тестовые пароли генерируемые/вымышленные и не печатаются. Не выключать async safety Django.
- Fixtures, fake session cookie/CSRF и XSS payload не сохранять в evidence как секреты. Обычные regression тесты не переписывают PNG (UPDATE_EVIDENCE не задавать). Production не публиковать, туннель не создавать.
- Meaningful regression для найденного дефекта и новых сценариев, статические проверки Ruff/check/migration/diff. Полный pytest один за раз на том же test PG. После writer freeze передать точное имя suite PG для независимого rerun родителя. Свои web/browser/temp DB очищать сразу, PG оставить до review, затем точный cleanup по отдельному поручению.
- Отчёт: actual tests/results, исходный дефект и исправление, список файлов, ограничения. Реальный BFCache определять по событию/браузерной навигации; искусственно посланное pageshow не выдавать за доказательство настоящего попадания в BFCache. Если движок не использует BFCache при no-store — так и записать, проверку обработчика отделить. Нельзя объявлять Firefox/WebKit/реальный телефон проверенными по Chromium.

Не commit/push до отдельного поручения после accepted. Основной агент сверит фактический diff и независимо выполнит критические сценарии, затем даст точный allowlist и commit message. Каждый commit с атрибуция команды.

## Уточнение после воспроизведения

Исполнитель воспроизвёл stale формуA после смены наB в другой вкладке на настоящем Chromium. Родитель выбрал контракт docs/decisions/001-session-tab-refresh.md: CSRF rotation login/logout + memory-only сравнение при focus/visibility/pageshow, нейтральный BroadcastChannel сигнал без данных, единый include в base. Новый endpoint/contextprocessor не разрешён. Расширена запись только для удаления прежнего history.js include в profile/operator, dashboard home, grades study, schedule schedule, requests base. Иные изменения соседних шаблонов не разрешены. Серверный stale-CSRF тест и отсутствие reload обычного focus обязательны.
