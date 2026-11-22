# Q05: локальный жизненный цикл данных

Явная отдельная проверка CORE-01/04/05, TECH-02/03, SEC-01/02 и демоданных. Это не production backup, не шифрованная внешняя копия и не выполнение D04. Публичный сайт и доступность из России этим сценарием не проверяются.

## Запуск

Нужны Python 3.13, зависимости из `uv.lock` (включая dev), Linux runtime для Gunicorn, Docker CLI/daemon с доступом к pinned PostgreSQL17.11 image из `deploy/compose.local.yaml`, установленный Chromium Playwright и его системные библиотеки. Скрипт запускается отдельно от pytest, не требует Docker-in-Docker в CI.

В обычном Linux Docker:

```sh
uv sync --locked
uv run playwright install chromium
uv run python scripts/verify_data_lifecycle.py --docker docker
```

Фактический запуск этой среды (WSL + Windows Docker Desktop CLI):

```sh
PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/python scripts/verify_data_lifecycle.py --docker /mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe
```

Из native Windows PowerShell запускайте Linux runtime через WSL (Gunicorn не поддерживает native Windows Python):

```powershell
wsl --cd /home/local-user/test_mgimo-vibe-coding env PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/python scripts/verify_data_lifecycle.py --docker /mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe
```

`--docker` принимает один executable; путь с пробелами нужно заключить в кавычки как один аргумент. Shell/eval не используется. Native Windows Python без WSL не заявлен поддерживаемым; PowerShell-команда выше документирована, но непосредственно из PowerShell в этой сессии не запускалась.

## Что действительно проверяется

1. Случайные уникальные container/volume с ownership label; только loopback dynamic ports, без host mounts. В пустой БД `migrate --noinput`, `seed_demo --anchor-date=2026-11-02`, `collectstatic --noinput`.
2. DEBUG=False Gunicorn/WhiteNoise. Настоящий вход Chromium, новая заявка формой, изменение статуса scoped оператором, прочтение персонального уведомления и объявления.
3. В памяти сохраняются все поля профилей, enrollment, опубликованных и прочих результатов, занятий, заявок с UUID/status/version, событий, уведомлений и отметок прочтения, пользователей с password hash, scope операторов, историю занятий, deadlines и объявления. Исключён только `last_login`: каждый дополнительный успешный вход должен его менять. Значения и hashes не выводятся.
4. Stop/start своего Gunicorn с тем же SECRET_KEY, затем stop/start своего PostgreSQL процесса при сохранённом named volume. Сессия остаётся действительной, своя заявка читается, второй студент получает404. Readiness503 при недоступности БД и200 после восстановления.
5. `docker exec <owned> pg_dump -U deanery -Fc lifecycle_source` в закрытый временный файл; `CREATE DATABASE lifecycle_restored`; `docker exec -i <owned> pg_restore -U deanery --exit-on-error -d lifecycle_restored`. Dump передаётся через stream без host mount. Source не удаляется и не перезаписывается. Только свой web переключается на restore, повторяются session/login/чтение/отказ чужому студенту.
6. Повторный seed после restart и restore не меняет сравниваемые данные. Любое расхождение/сбой даёт ненулевой код. JSON содержит безопасные стадии, exact owned names и статус cleanup; dump, cookies, пароли и hashes не печатаются.

Python `-O` отклоняется до создания ресурсов. Docker endpoint проверяется как локальный (unix/npipe либо tcp loopback), Docker overrides не наследуются ни одним CLI-вызовом, включая dump/restore. Создание контейнера отделено от запуска; попытки создания регистрируются до вызова CLI, поэтому timeout после создания также проходит ownership cleanup. До mount проверяются отсутствие exact имён и label созданного volume; после удаления подтверждается отсутствие.

Скрипт не читает `.env`, не принимает пользовательские DSN/имена ресурсов и очищает окружение subprocess от DB/SECRET_KEY/DEMO/PG переменных. Demo-пароли случайные, передаются только через env. QA trust применяется исключительно к своему disposable loopback PostgreSQL; это не dev/prod конфигурация.

Статика collectstatic/web размещается в отдельной закрытой temporary directory, repo/staticfiles не изменяется.

Finally завершает свой web и удаляет только свои exact container/volume после сверки ownership label. Нет prune, compose down, остановки чужих портов или удаления по prefix. SIGTERM/SIGINT проходят cleanup; SIGKILL, выключение машины/daemon и отказ Docker могут препятствовать удалению. В таком случае JSON сообщает incomplete cleanup; ручное удаление допустимо только по exact names после проверки label. Docker subprocess имеют конечные timeout. Обычные тесты не создают Docker ресурсы.

## Regression upgrade

`tests/test_data_lifecycle.py` использует MigrationExecutor: текущая заполненная схема → предыдущая `notifications.0001_initial` при сохранении остальных leaf → создание существующей заявки и двух событий через historical models → все текущие leaf. Сравниваются профиль/password hash, результаты, занятия, UUID/status/version/история; finally восстанавливает leaf schema. Это конкретный upgrade notifications0001→0002 (index/default), а не репетиция обновления production релиза или B07→B10. Новых миграций нет.

```sh
TEST_DB_PORT=55432 DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest tests/test_data_lifecycle.py -q
```

## Фактические результаты

Среда: Linux/WSL, Python3.13.14, PostgreSQL17.11 pinned image, Playwright Chromium build/revision1248. Lifecycle успешно прошёл все четыре стадии и cleanup; безопасный JSON — `docs/evidence/Q05/lifecycle-result.json`. Новые regression включают upgrade и safety runner (foreign ownership, remote endpoint, Python `-O`, timeout-after-create, start failure). Полный suite и финальные checks фиксируются в `docs/evidence/Q05/implementation.md` после завершения. Отдельный suite PostgreSQL оставлен основному агенту для независимого ревью; это не ресурс lifecycle. Другие Q/D этим отчётом не закрываются.
