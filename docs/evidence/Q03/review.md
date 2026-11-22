# Q03 — независимая приёмка локальной безопасности сессий

- Постановка: [prompt.md](prompt.md); отчёт Sol/low: [implementation.md](implementation.md).
- Архитектурный контракт: [ADR001](../../decisions/001-session-tab-refresh.md).
- Замечания: [review-01.md](review-01.md), все5 устранены.
- Требования: SEC-01/02, PRD-05, CORE-01/04, TECH-03/06.
- **Статус: accepted** в локальных границах Q03; версионирование на момент записи pending.

## Что изменилось и независимо проверено

Главный агент прочитал реальный diff views/password command/shared JS/base и удаления дублирующих include, а также все новые тесты и QA fixture/settings. Модели, зависимости/lock и схема не менялись. Старый DOM после смены аккаунта — подтверждённый дефект интерфейса; серверный обход авторизации не обнаружен и не заявляется исправленным.

| Область | Фактическая проверка |
| --- | --- |
| Две вкладки | A→logout/loginB удаляет старую форму и открывает актуальный кабинет; A→guest обновляется; прежний вход сохраняет текст обычного focus; разные contexts независимы |
| UI механизм | Штатный rotate_token при logout, существующая login rotation; memory-only cookie comparison, BroadcastChannel только сигнал. Без нового endpoint/HMAC/contextprocessor/cookie/storage или polling |
| Старый POST-документ | Реальная server validation error1001символ → смена аккаунта: только GET, нет resubmission dialog и новой заявки. location.replace/безопасная retry ссылка; data-request-method задаётся сервером |
| Серверная защита | Client(enforce_csrf_checks=True) без JS: старый токен после A→B даёт403; browser с JS disabled после expiry/deactivation идёт во вход, число заявок неизменно |
| History/сессии | Logout удаляет DB session, старый cookie/прямой URL не работают; реальные Back/Forward не показывают прежний профиль. BFCache попадание не подтверждено: исполнитель зафиксировал0 из7; синтетический persisted handler проверяется отдельно и не выдаётся за реальный BFCache |
| Fallback/состояние | SecurityError конструктора BroadcastChannel не даёт pageerror; focus fallback работает. До aborted повторного GET приватный DOM удалён, нейтральный текст и ссылка доступны |
| XSS/headers | Комментарий и объявление plain text, img/script не исполняются; session cookie HttpOnly/SameSite=Lax, private/no-store |
| Bootstrap | Все4 причины ValidationError понятны, введённый пароль не выводится, rollback после ошибки второго аккаунта; RuntimeError не маскируется как плохой пароль |
| Изоляция теста | Own test_browser_* DB, порт, temporary static, random secret/password, safe environment, default5432; наш PG55432 передаётся env. Nested cleanup охватывает setup/teardown failure; только свой Popen |

Команды основного агента:

```text
DB_PORT=55432 TEST_DB_PORT=55432 TEST_DB_NAME=test_q03_suite PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest --browser-channel chromium -q
→ exit0, 168 passed, 1 warning, 109.76s
.venv/bin/ruff check .          → exit0, All checks passed
.venv/bin/ruff format --check . → exit0, 174 files already formatted
git diff --check               → exit0
DB_NAME=deanery DB_HOST=127.0.0.1 DB_PORT=55432 .venv/bin/python manage.py check
→ exit0, no issues
```

Первый makemigrations check дал warning отсутствующей QA БД deanery. Основной агент затем создал отдельную уникальную test_q03_parent_check_*, мигрировал её и выполнил `makemigrations --check --dry-run`: **exit0, No changes detected, без warning**. Эта проверка и finally DROP завершились exit0, пользовательская БД не использовалась. Полный pytest выполнялся отдельно на test_q03_suite, без параллельного pytest.

Production `manage.py check --deploy` основной агент независимо запустил с очищенным env и случайным synthetic SECRET_KEY/фиктивными DB-параметрами: exit0, только ожидаемый security.W004 (HSTS). Это проверка конфигурации, не реального TLS/Caddy. Существующий pytest-playwright warning о будущем pytest10 остался; тесты не отключались. UPDATE_EVIDENCE не задавался, исторические PNG не менялись.

## Решение и остатки

Все замечания этого объёма устранены: optional BroadcastChannel, нейтральный текст, GET вместо потенциального повторного POST, defaults/env и надёжный cleanup fixture. Независимый full suite пройден после writer freeze; последующие изменения только в документах основного агента.

Следующий этап — Q04/U03 (другие движки, размеры, zoom, клавиатура, состояния сети), затем Q06 и D02. Настоящий BFCache, Firefox/WebKit/телефон, CSP enforcement, proxy/IP, публичный HTTPS/HSTS и сети РФ не подтверждены. Истечение/деактивация обнаруживаются при следующем серверном запросе; мгновенная offline проверка не обещается. При будущем изменении CSRF_COOKIE_NAME/HTTPONLY пересмотреть ADR001. V2/публикация не одобрены автоматически этим аудитом.

Разрешён ограниченный commit/push принятого allowlist в main/origin: `fix(Q03): refresh stale account tabs without resubmitting forms`, обязательный trailer `атрибуция команды`. Проверить staged diff, сообщение и HEAD=ls-remote. Затем удалить только оставленный собственный suite container `deanery-q03-20261105` после exact label проверки. Никаких пользовательских dev-ресурсов не трогать.
