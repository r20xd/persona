# D02-01 — независимая приёмка локального серверного контура

- **Решение:** accepted в границах D02-01. Весь D02 и готовность к публикации этим не принимаются.
- **Ревьюер:** основной агент; исполнители явно запускались как `gpt-6.1-sol / low`, `fork_turns=none`, без своих субагентов. После прерывания сессии отдельный исполнитель восстановил окружение и завершил узкие проверки/cleanup; архитектуру и приёмку ведёт основной агент.
- **Основание:** [prompt.md](prompt.md), [implementation.md](implementation.md), ADR002, PLAN D02-01.
- **Требования:** TECH-01/03/04/06, SEC-01/02, DATA-01; сохранение notices в пределах сборки LIC-01. HOST-01/02 и полный native/OS аудит остаются неподтверждёнными.
- **Исходный SHA:** `архивная-версия`. Версионирование до отдельного commit/push — pending.

## Проверено основным агентом

| Область | Проверка | Результат |
| --- | --- | --- |
| Объём | Прочитаны Dockerfiles/Compose/Caddy/init, proxy/build/production settings, runner, новые тесты, полный diff и runbook | Нет изменения схемы, lock, бизнес-сервисов, шаблонов или JS. Runtime-only образ и отдельные config images; новые credentials не записываются в Git |
| Образ | Самостоятельная сборка в собственном unique QA project из allowlist tar | Python3.13.14, locked runtime closure13; нет pytest/playwright/ruff/uv/compiler, project tests/.git/.env. App uid/gid10001, read-only rootfs, tmpfs, cap-drop. Dist-info licenses и libargon2 notice сохраняются |
| БД/сети | Настоящие миграции/seed отдельными one-shot commands; runtime flags и Compose topology | App DB-role не superuser/createdb/createrole; bootstrap secret отсутствует в app/Caddy. App/DB без host ports, internal сети; только QA Caddy имеет loopback high ports. Данные в собственных named volumes |
| HTTPS и браузер | Независимый актуальный default runner, артефакт production-independent-final.json | **status=passed, cleanup=complete**. Python проверил chain+hostname по собственному CA; Chromium после этого использовал исключение только для QA CA. Два студента и оператор,360/1440, реальные CSRF формы, создание/обработка заявки, сохранение статуса после restart app/DB, чужой UUID404 |
| Защита proxy | Forced Caddy headers, trusted-peer callable, unit и реальный Axes counter | Поддельные XFF/X-Real-IP не изменили IP ключ счётчика; XFP не отменил HTTP redirect. IPv4/IPv6 peer проверяется отдельно. REMOTE_ADDR глобально не меняется |
| Browser/security | CSP/header/static/cookie/tab checks в том же независимом runner | Manifest assets200, без CSP/script errors на проверенном пути; Secure/SameSite cookies, session HttpOnly, читаемый CSRF marker сохраняет ADR001. Logout/login в двух вкладках не сохраняет прежний доступ |
| Отказы | Реальная остановка DB и app | Readiness503 при остановке БД, live200, восстановление после запуска; при недоступном upstream проверен502 и Docker health app. Oversized body413, CSRF403, без нового сохранения/ложного успеха |
| Логи | Injected sentinel в query/cookie/body, проверка app/Caddy logs и image history | Sentinel и QA login password не обнаружены. Ошибки runner выводят только phase/type. Caddy operational logs пока подавлены; ограничение ниже |
| Полный regression | Независимый PostgreSQL17.11+Chromium прогон 6 ноября; regression-independent.json | **350 passed, 1 warning, 170.93s, exit0**. Перед запуском фактически проверен SELECT1; захват вывода с редактированием QA пароля |
| Последний guard | После полного прогона добавлен отказ от remote/malformed Docker endpoints. Независимо 8 ноября выполнен `pytest tests/test_production.py tests/test_foundation.py -q --tb=short` | **51 passed, 0.80s**, включая43 прежних focused cases и8 новых endpoint cases. Не выдаётся за новый полный suite358; normal local path остальных компонентов не изменился |
| Стиль | Независимые Ruff all, format check6 затронутых Python-файлов, git diff check | Все exit0. Исполнитель также проверил весь format scope. Docker `check --deploy` выполнен, HSTS0/W004 ожидаем до публичного HTTPS |

Полные Docker/TLS результаты сохранены в production-independent-final.json; более ранний production-independent.json также был успешен, но предшествовал explicit empty env-file. Для актуального результата используется final артефакт. Повтор всех browser/DB проверок после единственного дополнительного endpoint guard не требовался: guard покрыт новыми unit cases и проверкой реального локального Docker endpoint исполнителем. Производственные Django/proxy/Compose настройки после успешного полного прогона не менялись.

## Исправления, принятые при ревью

1. Удалён ошибочный HttpOnly у CSRF cookie: ADR001 читает его как UI marker. Защита сессионного cookie не ослаблялась. Production two-tab smoke подтвердил сохранение поведения.
2. Общий runtime env-file передавал bootstrap пароль в app. Заменён явными per-service maps: административный пароль только у DB. QA пароли не передаются через build args/слои; bootstrap demo получает их через private Compose JSON stdin.
3. Исправлены отсутствующая root templates directory, YAML quoting tmpfs, Compose placeholder substitution и Playwright selector с привязкой к форме. Бизнес-код не менялся ради ошибочных тестовых ожиданий.
4. Runner получил ownership-before-delete, обработку отсутствующей image после failed build, controlled SIGTERM cleanup, запрет Python-O и redacted error output. Отдельные safety tests не подменяют реальные Docker проверки.
5. При первом handoff отдельная host suite-БД ещё не была готова: native Windows CLI не получил пароль из WSL environment. Ранний прогон дал64passed/286setup errors; это ошибка QA bootstrap, а не app assertions. Исполнитель заменил только свой контейнер, сменил QA пароль и фактически проверил SELECT1. Старый raw traceback не включён в репозиторий. Основной агент затем выполнил успешный полный прогон с capture/redaction.
6. По той же причине нельзя полагаться на передачу COMPOSE_DISABLE_ENV_FILE через WSL. Обе Compose-команды runner теперь явно используют пустой env-file NUL или /dev/null, исключая автоматическую загрузку пользовательской `.env`. Актуальный независимый Docker/TLS run выполнен после исправления. Прямого просмотра содержимого пользовательской `.env` или SSH-ключей не выполнялось; отсутствие implicit env loading в раннем варианте не утверждается.
7. Последняя проверка local endpoint теперь отвергает remote named pipe/TCP/SSH и malformed endpoints до отправки build context. Эти8 случаев отдельно независимо проверены после возобновления сессии.

Обязательных незакрытых замечаний в границах D02-01 нет.

## Cleanup, ограничения и следующий шаг

Default Docker/TLS runner самостоятельно подтвердил очистку своего unique project/images/volumes/networks. Остаток отдельной host suite-БД удаляется отдельно после exact owner/image/port проверки; фактический результат — [cleanup.md](cleanup.md). Прерывание сессии уничтожило временный managed Python, он восстановлен locked uv sync без смены зависимостей. Повторять уже прошедшую сборку и полный suite по этой причине не требовалось.

Это локальная репетиция на Docker Desktop, не VPS, публичный сертификат/ACME или проверка доступности из России. Native/OS SBOM, актуальные CVE и полные notices образов остаются D02-02. Caddy global operational logs пока discarded, safe request logs приложения сохранены; безопасная TLS/infra диагностика требуется в D02-02/D04 до полноценной эксплуатации. HSTS0, remote CI unverified, release/rollback/backups/timers, аппаратный телефон, V2 и публикация остаются отдельными работами. Существующие pins проверены6ноября, не объявляются бессрочно актуальными.

После приёмки документов root выдаёт точный allowlist для обычного commit/push main→origin. Обязательный trailer `атрибуция команды`, без force/amend/обхода hook. Staged diff/check и фактическое совпадение HEAD с `git ls-remote origin refs/heads/main` обязательны. Итог Git — [versioning.md](versioning.md), отдельно от accepted.
