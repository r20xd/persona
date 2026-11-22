# A01–A02: отчёт исполнителя

Дата: 4 ноября 2026. Исполнитель: gpt-6.1-sol / medium (явный запуск родителем).
Статус: передано на независимое ревью; самостоятельно не принято. Commit/push не выполнялись.

## Объём и требования

Создано воспроизводимое основание Django: TECH-04, SEC-02, часть TECH-06.
A01: pyproject, реальный uv.lock, Python 3.13, Ruff/pytest-django и README.
A02: settings base/local/test/production, WSGI, health и безопасные JSON-ошибки,
метаданные запросов и безопасный formatter логов, local Compose PostgreSQL.
**A02 не завершён в части фактического запуска с PostgreSQL и миграций.**
B01 **partial**: только AbstractUser с ролями student/operator и первой миграцией.
Профиля, учебных справочников и operator scope нет; CORE-01 не объявляется выполненным.
UI, вход, бизнес-сервисы, CI, deployment и публикация не входят в блок.

## Файлы

- `pyproject.toml`, `uv.lock`, `.python-version`: согласованные зависимости и tooling.
- `manage.py`, `config/`: layout, настройки, URL и WSGI; admin не подключён.
- `apps/core/`: чтение env, health, ошибки, безопасные логи.
- `apps/accounts/`: custom User и `0001_initial`, AUTH_USER_MODEL установлен до любых migrate.
- `tests/test_foundation.py`: проверки без БД; `tests/test_database.py`: реальные PostgreSQL checks, ожидают сервиса.
- `deploy/compose.local.yaml`: PostgreSQL, обязательный пароль из env, loopback, volume.
- `.env.example`, `.gitignore`: placeholders, исключение env variants/private/backups/keys.
- `README.md`: запуск, WSL integration, проверки, ограничения production.

## Реальная установка и версии

Системный Python оказался 3.14.4. uv 0.12.1 установил Python **3.13.14** в
`/tmp/deanery-python`, cache — `/tmp/deanery-uv-cache`; домашний cache readonly.
Первая sandbox-загрузка не прошла DNS; повтор через штатный require_escalated успешен.
Тот же механизм использован для разрешённой загрузки PyPI зависимостей.
Lock сформирован настоящим `uv sync`, не вручную: Django 5.2.19, psycopg и
psycopg-binary 3.3.8, argon2-cffi 25.1.0, WhiteNoise 6.12.0, Gunicorn 23.0.0,
pytest 9.2.0, pytest-django 4.14.0, Ruff 0.17.3.
Официальные страницы веток просмотрены, но точную установленную версию определил
реальный resolution: https://docs.djangoproject.com/en/5.2/releases/ и
https://www.postgresql.org/support/versioning/ .

Публичный Docker registry с анонимным bearer-token вернул HTTP **200** для
`library/postgres:17.11-bookworm`, manifest digest
`sha256:839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`.
Compose фиксирует тег и digest. Содержимое токена не выводилось/не сохранялось.
Проверка registry не равна успешной загрузке/запуску контейнера.

## Выполненные проверки

Для всех uv-команд:
`UV_CACHE_DIR=/tmp/deanery-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/deanery-python`.

| Команда/сценарий | Фактический результат |
| --- | --- |
| `uv sync --locked` | exit 0; lock не меняется, 18 установленных пакетов проверены |
| `uv run ruff check .` | exit 0, All checks passed |
| `uv run ruff format --check .` | exit 0, 40 файлов formatted |
| `uv run python manage.py check` | exit 0, no issues |
| `uv run python manage.py makemigrations accounts` | exit 0, создана initial User migration; warning: БД недоступна |
| `uv run python manage.py makemigrations --check --dry-run` | exit 0, No changes detected; проверка истории в БД недоступна и даёт warning |
| `uv run pytest tests/test_foundation.py` | exit 0, 24 passed; 6 предупреждений WhiteNoise об отсутствии staticfiles до UI/collectstatic |
| `check --deploy --settings=config.settings.production` с генерируемыми синтетическими env | exit 0; только security.W004, HSTS пока 0 до проверки HTTPS |
| Настоящий HTTP через временный wsgiref на `127.0.0.1:8019` | live 200 `{"status":"ok"}`, ready 503 `{"status":"unavailable"}`; сервер остановлен |
| `docker info --format '{{.ServerVersion}}'` | exit 1: Docker Desktop WSL integration недоступна |

Sandbox запретил bind сокета для HTTP smoke; штатный require_escalated разрешил
временный loopback-сервер. Первый запуск `runserver` без БД остановился на
Django migration consistency check; для независимого health smoke использован
стандартный WSGI server без обхода или изменения production-настроек.

Тесты проверяют fail closed для каждого обязательного env, запрет wildcard и
чужих CSRF origins, secure cookies, отсутствие inherited production DB config,
DB-проверку ready через mock и 503 без текста исключения, запрет health POST,
CSRF, безопасные ошибки, Argon2 и отсутствие default staff/superuser, безопасный
formatter с исключением, содержащим тестовый секрет. Mock ready **не является**
проверкой реального соединения. Реальный HTTP подтвердил именно отказ 503.

## Лицензии

Проверены metadata установленных wheel до передачи результата: Django/asgiref/
pycparser — BSD-3-Clause; pytest-django — BSD-3-Clause (текст лицензии в metadata);
Pygments — BSD-2-Clause; packaging — Apache-2.0 OR BSD-2-Clause;
argon2-cffi/bindings, Gunicorn, WhiteNoise, pytest, Ruff, iniconfig, pluggy — MIT;
cffi — MIT-0; psycopg/psycopg-binary — LGPL-3.0-only. sqlparse поставляет BSD
license в wheel (отдельное поле License-Expression отсутствует).
Эти лицензии допускают использование. Исходники библиотек не копировались в
репозиторий, библиотечные license files сохраняются uv в окружении. Для D02
требуется полный набор notices в распространяемом образе, включая bundled
библиотеки psycopg-binary; это не объявлено завершённым здесь. Assets/CDN не добавлены.

## Ограничения и следующий шаг

Нет работающего PostgreSQL в текущем WSL; postgres/psql также отсутствуют,
системные пакеты не устанавливались. **Не запускались** migrate, PostgreSQL
integration tests, проверка DB constraint фактической записью или persistence
после restart. SQLite не использован. После включения Docker integration:
Compose up → migrate → полный pytest → проверка данных/перезапуска.

Production deployment pending: доверенная сеть Caddy/Gunicorn обязательна для
proxy header; HSTS включается после HTTPS. CSP, throttling, auth UI, operator
scope, бизнес-изоляция, CI и все конкурсные пользовательские сценарии пока не
реализованы. Readiness проверяет подключение, не миграции.
Демо-данные, production secrets и реальные персональные данные не создавались.
Сторонние assets отсутствуют. Полный license inventory распространяемого образа
и dependency audit относятся к следующим этапам.
