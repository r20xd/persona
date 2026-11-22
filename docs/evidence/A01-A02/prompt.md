# A01–A02 — основание приложения

Пользователь поручил продолжать автономно. Основной агент передал исполнителю foundation отдельный контекст: gpt-6.1-sol, medium, fork_turns=none. Ниже содержание постановки, сокращённое без изменения контрактов.

Создать воспроизводимое основание Python 3.13/Django 5.2 LTS/PostgreSQL 17, настоящий uv.lock, разделённые settings, минимальный custom User до первой миграции, health live/ready, локальный Compose PostgreSQL, README и проверки. Никаких UI/бизнес-функций, SQLite, реальных данных или публичного admin. Production должен явно отказывать при отсутствии обязательной конфигурации.

Разрешённые файлы: pyproject.toml, uv.lock, .python-version, README.md, manage.py, config/, apps/core/, apps/accounts/, tests/, deploy/compose.local.yaml, .env.example, .gitignore и implementation.md в этом каталоге. Родитель владеет продуктовыми документами, планом, состоянием и ревью. Commit/push исполнителю до приёмки запрещены.

Зависимости: Django, psycopg binary, argon2-cffi, whitenoise, gunicorn; dev pytest, pytest-django, Ruff. Проверить uv sync --locked, Ruff, Django checks, отсутствие недостающих миграций, health/config tests; по доступности PostgreSQL — реальные миграции и проверки БД. Недоступность Docker daemon не обходить подменой СУБД; явно сообщать ограничения. Приватные SSH-ключи не читать, recursive agents не запускать.
