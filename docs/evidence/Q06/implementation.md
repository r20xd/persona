# Q06 — отчёт исполнителя

Статус: передано на независимое ревью; writer freeze. App/schema/dependencies/lock не менялись. Требования TECH-03/04/06, PRD-02/05, SEC-01/02; dependency часть LIC-01, лицензии ведёт root.

## Результат

- `scripts/verify_performance.py`: собственная disposable PostgreSQL17.11, локальный Gunicorn23.0.0 DEBUG=False2workers×4threads/WhiteNoise,20настоящих CSRF login sessions с уникальными sessionid, sequential Argon2 login, barrier20 readers,120warmup и360measured reads, identity/isolation до/после, target/functional failure отдельно, redacted errors и exact owned cleanup.
- `scripts/performance_queries.py`: full GET query audit initial/expanded dataset, execute_wrapper без DEBUG=True, materialized templates, только counts/times.
- `tests/test_performance.py`:6узких проверок nearest-rank/false login200/redirect/wrong page/5xx/redacted failure+cleanup.
- `docs/testing/performance.md`: воспроизведение, scope, caveats, query bounds/fixed cost и audit команды.
- JSON evidence: реальные performance/query агрегаты, runtime/dev audit и metadata, resource repair и exact retained suite resource.

Финальный factual run:2026-11-06T07:44:30Z, exit0,20sessions,360read/120warmup, read p50=71.871ms,p95=180.663ms,max=294.523ms; login p50=86.611ms,p95=106.914ms,max=111.057ms;0functional/non200/5xx/unexpected redirect failures; target_met=true; cleanup_complete=true. Длительность measured reads2.518s. Nearest rank ceil(n*p). Это localhost warm-read smoke, storage=tmpfs, не VPS disk benchmark. До изменения storage первоначальный successful run также достигал цели (~188ms p95); tmpfs выбран для исправления утечки anonymous QA volume, а не улучшения цифры.

Среда: WSL2 kernel6.18.33.2, AMD Ryzen7 9800X3D8-Core Processor,16logical CPU, MemTotal16070300KiB; Python3.13.14,Django5.2.19,Gunicorn23.0.0,PostgreSQL17.11; штатный Argon2,CONN_MAX_AGE=0. Точные sizes и per-route p50/p95/max в performance.json. Initial6enrollments/54lessons/2requests/8notifications/3announcements; expanded46/94/42/48/43. Query counts initial→expanded неизменны26/7/8/9/6/16/5; N+1 не выявлен в этой матрице. Dashboard/notifications имеют повторные фиксированные authorisation/count queries; grades/session/schedule ограничены семестром/днём-неделей/enrollment, но без численного cap. Это явно оценённое ограничение, не обещание масштабирования на произвольные размеры.

Dependency audit:2026-11-06, официальный PyPA pip-audit2.10.1, PyPI JSON advisory API, completed exit0 по обеим scope.13runtime Linux packages (включая psycopg-binary3.3.8),26runtime+dev Linux packages; известных advisories не найдено. Windows-only tzdata/colorama исключены environment markers. Frozen uv export полного closure; audit tool в отдельном uvx environment без изменения lock. Передавались только package/version; это не гарантия отсутствия неизвестных уязвимостей.

## Проверки

- `.venv/bin/ruff check .` — exit0.
- `.venv/bin/ruff format --check scripts/verify_performance.py scripts/performance_queries.py tests/test_performance.py` — exit0.
- `manage.py check` с config.settings.test/own suite PG — exit0,0issues.
- `manage.py makemigrations --check --dry-run` — exit0,no changes.
- `git diff --check` — exit0.
- Полный regression с own PG55432 и `PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers`:184passed,1warning,159.90s,exit0. После collection добавлен шестой узкий runner failure test; весь `tests/test_performance.py` затем6passed,exit0. Root может независимо выполнить финальные185tests.
- Ранний запуск sandbox не имел loopback PG доступа; повтор штатно escalated. Первый escalated fullsuite без browser cache:152passed/32browser setup errors (нет Chromium в default cache); после явного /tmp cache полный повтор прошёл. Это QA infrastructure ошибки, не app failures.
- Ранние runner failures: QA client host исправлен на localhost, page markers сверены с реальными h1. App код не менялся.
- PostgreSQL server_version170011 подтверждён; stylesheet реально200из WhiteNoise. Двадцать независимых cookie jars имеют разные server sessionid; после нагрузки профиль/чужая заявка перепроверены для каждой сессии.

## Resource repair и оставленная среда

Первоначальный runner не задал PGDATA mount и image VOLUME создавал anonymous volumes. По отчёту предыдущего исполнителя exact container ownership и сохранённые mount records с container ID сопоставили пять volumes; это reconstructed ownership evidence, не сохранённые raw Docker create events; они удалены по точным именам, broad prune не выполнялся. Безопасная цепочка — resource-repair.json. Два старых anonymous volumes от2026-08-02 и dev named volume не затрагивались. Runner исправлен на explicit tmpfs и повторён; штатный finally завершил web и подтвердил отсутствие своего container. User .env/dev/keys не читались и не менялись.

Для независимого root rerun намеренно оставлен только собственный suite container из suite-resource.json: `deanery-q05-25856a9ba05e412785c6087aa48a3bc2`, label `deanery.q05.owner=25856a9ba05e412785c6087aa48a3bc2`,127.0.0.1:55432,DBtest_deanery, disposable trust, attached own anonymous volume `f4e6b14364a98f6fa3d3a071be6d259309964d93095efa3c648e41428d321325`. Это исключение для review, не cleanup_complete нагрузочного runner. После review проверить exact label/attached volume через inspect, затем удалить exact container с `docker rm --force --volumes <name>` и подтвердить отсутствие обоих.

```sh
PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=55432 TEST_DB_USER=deanery TEST_DB_NAME=test_deanery TEST_DB_PASSWORD='' .venv/bin/pytest -q
.venv/bin/python -m scripts.verify_performance --docker /mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe
```

Для DB/browser/Docker нужны штатные sandbox escalations. Публичный сайт/Россия без VPN/production capacity не проверены. Commit/push не выполнялись. Лицензии/CI metadata — отдельная работа root.

## Восстановление после рестарта — 2026-11-06

Новый единственный исполнитель восстановил исчезнувший `/tmp` Python через `UV_CACHE_DIR=/tmp/deanery-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/deanery-python /home/local-user/.local/bin/uv sync --locked` (штатная escalation после DNS failure sandbox). Получен CPython3.13.14 и26locked packages; исходники, зависимости и lock не менялись. Chromium156.0.8078.4 (Playwright v1248), headless shell и FFmpeg восстановлены через `PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/python -m playwright install chromium`.

Docker Desktop был остановлен; запущен штатным `docker desktop start`. Exact container/label/port/volume из `suite-resource.json` проверены и совпали; контейнер был `exited`, затем запущен по точному имени. База `test_deanery` отсутствовала (были только postgres/template0/template1), создана пустая suite БД через `createdb -U deanery test_deanery`. Новый контейнер/volume не создавались, удаления ресурсов не выполнялись. Исходные provenance/repair сведения выше не повторялись.

Повторные проверки: Ruff check/format и `git diff --check` — exit0;6runner tests —6passed,0.08s; Django check —0issues. Первый migration check сообщил warning об отсутствующей БД; после создания пустой suite БД повтор `makemigrations --check --dry-run` — exit0,`No changes detected`,без warning. Fullsuite/benchmark оставлены root для независимого запуска, параллельный regression исполнитель не запускал.

Фактическая SSL/libpq идентификация: `psycopg.pq.__impl__ = binary`, `psycopg.pq.version() = 180006` (libpq18.6); Python `ssl.OPENSSL_VERSION = OpenSSL 3.5.7 9 Jun 2026`. Последнее относится к модулю Python ssl и не устанавливает версию OpenSSL, с которой собран bundled libpq.

Уточнение воспроизводимости: команды uvx в `docs/testing/performance.md` закреплены на фактически использованном `pip-audit==2.10.1`. `resource-repair.json` явно обозначает reconstructed ownership evidence и источник removal status — отчёт предыдущего исполнителя; повторных removals не было. Writer freeze сохранён.
