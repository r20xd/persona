# Q01/Q02 — отчёт исполнителя

Исполнитель: gpt-6.1-sol / low, по явному вызову root, без субагентов. Исходный HEAD архивная-версия. Прочитаны TASK, AGENTS, STATE, workflow, ARCHITECTURE §§6–10,13, текущие матрицы и фактические urls/views/selectors/services/tests. Использованы Codex, shell, Python/pytest/Django/Ruff, Docker Desktop native CLI; новых зависимостей/материалов нет.

## Изменения

- tests/test_access_matrix.py: точечные роли/HTTP read/write, точные counts и персональные маркеры, сохранённые effects и отсутствие изменений на отказах, отдельный enforce_csrf всех mutation routes, 405 и выборочные HX negatives. Специализированные существующие тесты сохранены.
- tests/test_integrity_audit.py: два РАЗНЫХ scoped оператора; cancel против обработки; submit retry. Проверены непрерывные версии и согласованные from/to/actor, ровно одно уведомление на каждую winning version, только owner recipient. Использован существующий PostgreSQL race helper с отдельными соединениями/timeouts, без mock locks/sleep. Сбой notify после существующих двух версий сохраняет полные прежние rows/read_at, retry создаёт ровно один новый переход.
- Root обнаружил по коду POST200 read-only для home/profile и разрешил минимальное исправление HTTP-контракта: imports+require_GET в двух views, POST405 regression. Воспроизведение старого200 новым исполняемым тестом не выполнялось; это source finding root, не доказанная утечка.
- Итоговые docs/testing матрицы обновлены точными test names/границами. Приложение вне разрешённого method fix не менялось.

## Проверки исполнителя

Собственный QA ресурс: `q01q02-suite-20261106-access`, container `3e1ab096a6d68003cc6859b39f486aed3df9e78ee289d7528a0c4cbde6732325`, label `owner=q01q02-access-20261106`; image postgres17.11-bookworm digest из compose.local; explicit tmpfs `/var/lib/postgresql/data:rw`, no host mounts; loopback127.0.0.1:55432; own disposable trust. Dev5432/8000 и его контейнер не изменялись. Ресурс оставлен root для review, cleanup только после exact ownership проверки.

Конфигурация всех команд: `TEST_DB_NAME=test_q01q02 TEST_DB_USER=deanery TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=55432` (password empty, собственный trust). PostgreSQL доступен из escalated tools; первая обычная sandbox pytest попытка получила setup network errors, не app failures. Затем:

- `.venv/bin/pytest tests/test_integrity_audit.py -q -x --reuse-db --tb=short`: exit0, 4passed (1.15s).
- Первая matrix проверка выявила ошибочное ожидание comment в request list (список его не отображает); исправлен тест: list проверяет exact count, comment marker — detail. App fix не потребовался.
- `.venv/bin/pytest tests/test_access_matrix.py tests/test_integrity_audit.py tests/test_requests.py tests/test_notifications.py -q -x --reuse-db --tb=short`: exit0, 194passed (13.99s).
- `.venv/bin/python manage.py check --settings=config.settings.test`: exit0, no issues.
- `.venv/bin/python manage.py makemigrations --check --dry-run --settings=config.settings.test`: exit0, No changes detected.
- `.venv/bin/ruff check tests/test_access_matrix.py tests/test_integrity_audit.py apps/accounts/views.py apps/dashboard/views.py`: exit0.
- `.venv/bin/ruff format --check` тех же четырёх файлов: exit0, 4already formatted.

Полный suite оставлен root; remote CI/production/HTTPS/physical phone/BFCache этим этапом не проверяются. Commit/push не выполнялись. Writer freeze после отчёта; итог accepted/changes requested принадлежит root.

Дополнение root review: `test_guest_with_valid_csrf_redirects_to_login` использует настоящий enforce_csrf Client, GET login получает cookie, POST с действительным token на home/profile и все пять защищённых mutation routes возвращает302 login без effects/сессии. Команда `.venv/bin/pytest tests/test_access_matrix.py -k guest_with_valid_csrf -q --reuse-db --tb=short`: exit0, 7passed/135deselected (0.55s). Ruff format/check повторены, exit0. Финально 142 новых matrix cases +4 integrity cases; полный suite root.
