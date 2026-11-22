# D02-01 — реализация исполнителя

Исполнитель: `gpt-6.1-sol`, effort `low`, явный вызов родителя; один writer, без субагентов. Основа `архивная-версия`. Требования: TECH-01/03/04/06, SEC-01/02, DATA-01, LIC-01; HOST-01/02 остаются будущей проверкой размещения.

## Реализовано

- Multi-stage Python3.13.14/uv0.12.1 image, locked runtime-only venv, offline manifest collectstatic, non-root10001. Runtime не включает uv/compiler/dev packages/project tests/.git/.env; notices в dist-info сохранены, libargon2 license скопирована отдельно.
- Production Compose с отдельными config images PG/Caddy, без host bind mounts, app root read-only/tmpfs/cap-drop, internal app/DB и app/Caddy networks, отдельный edge Caddy. Bootstrap secret не поступает в app/Caddy.
- PG app роль NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOREPLICATION, отдельный bootstrap; одноразовый init пустого volume, PUBLIC CREATE revoked. Миграции/seed отдельными one-shot commands, worker entrypoint ничего не мигрирует.
- Caddy автоматический production HTTPS и private local CA только в QA, no admin, forced scheme/real IP + stripping spoof headers, CSP/security headers/body cap/timeouts. Trusted-peer IP parser, exact health redirect exceptions и production required CIDR.
- Узкий runner строит allowlist tar на stdin native Windows Docker CLI и преобразует настоящий production Compose в QA JSON в памяти; generated own credentials, local-only endpoint, unique labels/project, loopback high ports, private mode0600 temp state. Default удаляет только проверенные owner-labelled ресурсы и проверяет отсутствие. `--retain` явно означает отсутствие cleanup. Ошибки выводят phase/type без exception message/Playwright calllog. SIGTERM запускает контролируемый cleanup, Python `-O` запрещён.
- Runbook: `docs/operations/production.md`. CSRF cookie остаётся readable для ADR001; session cookie HttpOnly. Служебные значения не передаются через build args/образ и не записаны в evidence.

## Первичные источники и проверенные image pins

Native `docker.exe buildx imagetools inspect` реально подтвердил tags и OCI index digests:

| Image | Digest |
| --- | --- |
| docker.io/library/python:3.13.14-slim-bookworm | `sha256:67a1e1f215ccda113cfc024e8639049257e88f273898f595b61476d128d387e8` |
| ghcr.io/astral-sh/uv:0.12.1 | `sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded` |
| docker.io/library/postgres:17.11-bookworm | `sha256:665dc7b37ac52a17e298511414c21d23ffa4e6a6ef6225b3e5d59c7afb35e994` |
| docker.io/library/caddy:2.11.2-alpine | `sha256:834468128c7696cec0ceea6172f7d692daf645ae51983ca76e39da54a97c570d` |

Проверка registry выполнена 2026-11-06; все три derived images реально построены Docker Desktop Linux engine. Версии не являются утверждением о прохождении native/OS audit. Официальные Dockerfiles tags: [Python](https://github.com/docker-library/python), [PostgreSQL](https://github.com/docker-library/postgres), [Caddy](https://github.com/caddyserver/caddy-docker); [uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/), [Caddy reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy), [request_body](https://caddyserver.com/docs/caddyfile/directives/request_body).

## Проверки и исправления

- `UV_CACHE_DIR=/tmp/deanery-uv-cache uv run ruff check .` — passed; format check —209 файлов без изменений.
- `uv run pytest tests/test_production.py tests/test_foundation.py -q` —43 passed. Проверены IPv4/IPv6 trusted/untrusted/malformed IP, CIDR /0 rejection, обязательная конфигурация, точные health exceptions, offline build settings, cleanup owner refusal/absence-vs-daemon-error и redacted failure.
- Реальная retained QA успешно прошла Python TLS chain+hostname по own CA, browser smoke трёх ролей, создание заявки/POST оператора, status после restart app+DB, чужой UUID404, 360/1440, статические файлы/CSP/script errors, cookie/CSRF, two-tab login/logout rotation, spoofed Axes counters, HTTP XFP redirect,413, readiness503/recovery, app DB-role flags, nonroot/read-only/runtime closure и sentinel log non-disclosure. Предыдущие retained контейнеры/сети/volumes/images удалены по ownership; пользовательские dev ресурсы не менялись.
- Начальные ошибки реализации исправлены по фактам: regex Compose `:?` placeholders; YAML inline tmpfs list требовал quoted scalar; Playwright submit selector требовал scope к форме заявки (logout тоже submit). Предварительное root review также выявило несовместимый HttpOnly у CSRF marker, попадание bootstrap env в app и отсутствующую root templates directory — исправлено до приёмки. Успех не выдавался за фактическое сохранение при этих ошибках.
- Default runner реально завершился `status=passed`, `cleanup=complete`, project `deanery-d02-64dff4a3e92f4c2795293c6934254497`; агрегат `production-smoke.json`. После этого добавлены точный cap64KiB и narrow upstream502/actual Docker health assertions — их независимый прогон root pending. Полный regression root pending; исполнитель не запускал full suite параллельно.

## Ограничения

Публичного deploy/ACME/DNS, проверки РФ без VPN и до28ноября, полного native/OS license/CVE audit, release/rollback/backup/timers и финальной конкурсной готовности нет. Это не завершение всего D02. Глобальные default Caddy operational logs discarded ради исключения sensitive error request fields; безопасное сохранение TLS/infra diagnostics и мониторинг отложены D02-02/D04. Chromium private QA использует ignore_https_errors только после отдельной настоящей Python SSL проверки CA/hostname; публичный сертификат так не проверялся.


## Уточнение независимого ревью: suite bootstrap и Windows environment

При первом handoff отдельной host regression PG ошибочно была объявлена подготовленной до фактического SELECT1. Root получил64passed/286setupDBerrors, не ошибки app assertions. Исполнитель установил: own контейнер exited, official PG entrypoint не получил password, потому что native `docker.exe -e POSTGRES_PASSWORD` не наследовал произвольную WSL env переменную. Это ошибка исполнителя, не конфигурации root. Первый локальный traceback с выведенным generated QA password не включён в evidence.

Исправлен только exact own suite контейнер/volume: generated QA password rotated, передан через Compose JSON stdin (не argv), старый private state обновлён mode0600. Реальный `psycopg.connect` с обновлённым state и `SELECT1` —passed; readiness подтверждена до повторного full regression. Пользовательские dev ресурсы и независимый production QA не затронуты.

По той же причине runner больше не полагается только на subprocess COMPOSE_DISABLE_ENV_FILE: обе Compose-команды явно получают `--env-file NUL` для native Windows CLI либо `/dev/null` для Linux CLI. Native `--env-file NUL` фактически принят Compose при восстановлении own suite DB; никакая пользовательская `.env` при этих командах не загружается.

## Продолжение финальной проверки 2026-11-08

После прерванной сессии восстановлена `.venv` через uv0.12.1: `UV_CACHE_DIR=/tmp/deanery-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/deanery-python uv sync --locked --python 3.13.14`. Lock и зависимости проекта не изменялись; исчезнувший временный interpreter заменён тем же CPython3.13.14.

Последнее узкое изменение — `require_local_endpoint` и8unit cases разрешённых локальных/запрещённых remote или malformed Docker endpoints. `pytest tests/test_production.py tests/test_foundation.py -q` — **51 passed in0.92s** без БД. `ruff check .` passed; `ruff format --check .` —210files already formatted. Guard отдельно принял фактический local named-pipe endpoint текущего Docker context; ресурсы при этой проверке не создавались, полная конфигурация context не выводилась.

Ранее выполненные независимые root TLS и full350 regression результаты не перезаписывались и повторно не запускались: они предшествуют8новым endpoint cases. Оставшиеся own regression container/volume удалены после точного ownership inspect; подробности и проверка отсутствия — `cleanup.md`. Код приложения/runner в этом продолжении не менялся. Приёмка и версионирование ожидают основного агента.
