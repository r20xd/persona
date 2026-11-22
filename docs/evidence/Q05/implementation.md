# Q05 — отчёт исполнителя

Статус исполнителя: реализовано, ожидает независимого review основного агента. Commit/push не выполнялись.

## Результат и требования

Добавлен отдельный воспроизводимый lifecycle runner: пустая PostgreSQL17.11 → migrate/seed → настоящий вход через Chromium в DEBUG=False Gunicorn/WhiteNoise → новая заявка формой → scoped оператор → уведомление/прочтение → restart web → stop/start PostgreSQL с сохранённым named volume → readiness503/200 и сохранённая сессия → dump → отдельная БД → восстановление → повторное чтение/вход/изоляция/seed. Сравнение данных, включая password hashes, выполняется в памяти. Исходная БД после restore также сверяется с baseline.

Покрытие: CORE-01/04/05, TECH-02/03, SEC-01/02, DATA-01, DEMO-01/02 в изолированном QA-сценарии. Это не объявление готовности production, D04 или остальных Q/D.

Все9 findings `review-01.md` учтены: create/start раздельно; attempted flag до создания, cleanup после timeout; exact-name preflight, ownership до mount/delete, post-delete absence; очищенный Docker env и локальный endpoint у всех CLI, включая dump/restore; private STATIC_ROOT; завершившийся web/ProcessLookupError; datetime.date в migration test; отказ Python `-O` до мутаций. Узкие safety-тесты проверяют наиболее опасные отказы.

## Файлы исполнителя

- `scripts/verify_data_lifecycle.py` — отдельный runner и безопасный JSON, timeout, own-resource cleanup.
- `scripts/lifecycle_settings.py` — DEBUG=False, отдельный private STATIC_ROOT.
- `tests/test_data_lifecycle.py` — upgrade historical models notifications0001→0002 и safety runner.
- `README.md` — ссылка на инструкции запуска.
- `docs/testing/data-lifecycle.md` — запуск Linux/WSL/PowerShell, ресурсы, ограничения и фактический процесс.
- `docs/evidence/Q05/lifecycle-result.json` — безопасный результат последнего lifecycle.
- `docs/evidence/Q05/implementation.md` — этот отчёт.

`prompt.md`, `review-01.md`, другие docs/testing, ARCHITECTURE/PLAN/STATE и прочие чужие изменения принадлежат основному агенту; исполнитель их не изменял.

## Выполненные проверки

Команды используют `.venv/bin` напрямую: `uv run` в sandbox не смог создать cache lock в read-only `/home/local-user/.cache/uv`; зависимости не менялись.

- `.venv/bin/ruff check .` — exit0.
- `.venv/bin/ruff format --check .` — exit0,163 files already formatted.
- `DJANGO_SETTINGS_MODULE=config.settings.local DB_NAME=deanery DB_PORT=55432 .venv/bin/python manage.py check` — exit0, no issues.
- Та же среда, `manage.py makemigrations --check --dry-run` — exit0, No changes detected. Перед этим own suite DB `deanery` мигрирована; пользовательская БД не использовалась.
- `git diff --check` — exit0.
- `PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/python scripts/verify_data_lifecycle.py --docker /mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe` — exit0, все4 стадии, cleanup_complete=true. Exact имена последнего удалённого container/volume — в `lifecycle-result.json`; web/dump/private static удалены.
- Новый upgrade/safety файл: сначала6passed; добавленный после этого start-failure test включён в финальный полный suite ниже.
- `TEST_DB_PORT=55432 DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest -q` — exit0, **152 passed**,1 existing PytestRemovedIn10Warning (session-scoped fixture в dashboard browser),74.40s. Warning не относится к Q05 и не исправлялся вне границ.
- Последний focused run `pytest tests/test_data_lifecycle.py -q` — **7 passed**, exit0; Ruff/check/format и diff--check повторены после финального уточнения Docker absent-marker. No-such-file/socket не принимается за отсутствие ресурса; принимаются только no-such-container/object/volume.

Первичные попытки выявили ошибки runner (`/study/` вместо `/grades/`; last_login закономерно менялся при втором входе) и keyword date в тесте; исправлены, затем проверки действительно повторены. Первый запуск без PLAYWRIGHT_BROWSERS_PATH не нашёл установленный QA Chromium. Все lifecycle попытки завершили cleanup своих ресурсов. Секреты и строки данных не сохранялись.

## Оставленный ресурс для review

Только отдельный suite container **`deanery-q05-suite-7214fd9e1fbf4e51922d7a1bd1d5ab4e`**, label **`deanery.q05.suite=deanery-q05-suite-7214fd9e1fbf4e51922d7a1bd1d5ab4e`**, pinned PostgreSQL17.11, loopback **55432**, user/db `deanery`, disposable QA trust, без host/user mounts. Собственный default DB мигрирован для Django migration consistency check. Тестовая DB создаётся/удаляется pytest. Container оставлен по постановке основному агенту для независимого suite. После review удалять только этот exact container после label-проверки (`docker rm --force --volumes <exact-name>` удалит и его disposable anonymous data volume). Никаких других оставленных Q05 web/lifecycle ресурсов нет.

## Ограничения и передача

Linux/WSL запуск реально выполнен; PowerShell→WSL команда документирована, непосредственно из PowerShell не выполнялась. Native Windows Python/Gunicorn не заявлен поддерживаемым. SIGKILL/сбой Docker/выключение машины могут потребовать точного ручного cleanup. Upgrade проверяет только предыдущую notifications0001→0002 схему, а не произвольную миграцию/production rollback. Не проверены публикация, offsite encryption, D04, доступность из России. Пользовательский `.env`, чужая БД, процессы, контейнеры/volumes и приватные SSH-ключи не читались/не изменялись.

**Write freeze:** исполнитель завершил изменения Q05; дальнейшие изменения только по замечаниям основного агента. Задача не объявлена принятой исполнителем. Commit/push не выполнялись.
