# B10/B11/F07 — отчёт исполнителя

Результат для независимого ревью; приёмку, commit и push исполнитель не выполнял.

## Реализовано

- `apps/notifications/models.py`, две additive миграции: объявления с ограничениями аудитории/интервала, собственные отметки, UUID-уведомления с allowlist целей и дедупликацией, Deadline с валидацией Assessment/часового пояса и ревизией, timestamp успешной команды. Индексы для ленты/публикации/срока.
- `selectors.py`, `services.py`: фильтрация текущего активного пользователя до counts/ID; all/group/faculty и `[publish_at, expires_at)`; оператор видит только all. Read POST идемпотентны и персональны. Trusted Deadline CRUD проверяет ревизию, блокирует строку и увеличивает ревизию при переносе/отмене. Команда сериализуется через ReminderRun, дедуплицирует recipient/deadline/revision/phase; текущие Enrollment, active student, публикация результата <= now подавляет напоминание только своему студенту. Пропуск timer догоняет overdue без устаревшей upcoming рассылки.
- `apps/requests/services.py`, `apps/schedule/services.py`: событие и уведомление в одной atomic транзакции; сбой создания уведомления откатывает источник. Повтор заявки не создаёт вторую запись.
- views/urls/templates/CSS: `/notifications/`, три независимых списка по 20 (`page`, `news_page`, `deadline_page`), `kind`/`unread`, реальные counts, safe source resolver с повторной проверкой прав (включая operator requests), own Deadline detail и актуальная отмена/дата. GET не отмечает прочтение. CSRF/POST/no-store, plaintext escape, отсутствующие/недоступные цели 404. Пустые состояния, навигация профиля/учёбы/расписания/заявок; локальная CSS.
- Provisioning добавляет вымышленные общие/групповые/факультетские объявления и связанный учебный срок; повтор не меняет прочтение, старые даты, пароли и действия. README содержит команды и семантику фильтров/пагинации.

## Проверки (реальные результаты)

- Изолированный PostgreSQL 17.11, pinned digest из Compose, временный контейнер `deanery-b10-qa`, loopback `55432`, без host mounts, trust только для вымышленных QA данных. После независимой приёмки остановлен только собственный контейнер `deanery-b10-qa` (docker stop, exit 0); из-за --rm удалён. Exact-name docker ps -a вернул пустой список; посторонние контейнеры не затрагивались.
- `TEST_DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest -q --browser-channel chromium`: **133 passed**, 48.57 s, exit 0. Сохранились все прежние 113 тестов; добавлено 18 unit/integration и 2 browser. Один существующий warning pytest-playwright о будущем pytest 10.
- Включены PostgreSQL audience/time matrix, own read/idempotency/CSRF/concurrency, чужие UUID/counts/pagination/filter, XSS, trusted target after scope revocation, active role, request/schedule notify rollback и дедупликация, Deadline validation/stale revision/перенос/отмена, future vs published results, inactive users, repeat/concurrent/missed reminders, additive demo.
- Browser: отдельные `test_browser_*` БД, migrate/provision/collectstatic, Gunicorn `DEBUG=False`, реальный вход студента и оператора → заявка → обработка → уведомление → прочтение события и объявления → Deadline; 360/1440 px, CSS HTTP200/hashed URL/computed border radius, отсутствие горизонтального overflow. Скриншоты `notifications-360.png`, `notifications-1440.png`. Визуально проверен mobile screenshot. Старые PNG, автоматически перезаписанные ранними regression тестами, восстановлены из HEAD. По поручению родителя screenshot записи во всех browser модулях теперь разрешены только при UPDATE_EVIDENCE=1; assertions/DB fixtures не менялись. Финальный полный прогон с guard не изменил исторические PNG.
- `manage.py migrate --noinput`, `makemigrations --check --dry-run` (No changes detected), `manage.py check` (0 issues); Ruff check / format check, git diff --check: exit 0.
- Отдельный preservation smoke в QA DB: до/после отката только notifications migrations к zero и повторного применения неизменны 3 пользователя с хешами, 36 занятий, 10 результатов и 1 заявка (UUID, владелец, статус, версия). Exit 0. Полный suite также сохраняет прежний requests migration regression.
- Ранний sandbox test запуск не имел loopback-доступа: 31 passed/74 connection errors. Повтор через разрешённую escalation дал baseline105passed (без browser); итоговый полный прогон133passed.

## Границы и ограничения

Публикация сайта, настоящий timer, доступность из РФ/эксплуатация до итогов, B12/F08 и итоговая готовность к сдаче не проверялись и не объявляются выполненными. Канал только внутренний; новых библиотек/внешних сервисов/публичных write API нет. Непрочитанные — сумма доступных новостей и собственных событий до пользовательских фильтров. Списки пагинируются независимо, query сохраняет фильтры/другие страницы. Дедлайны не отслеживают реальную сдачу учебной работы; формулировка это явно объясняет. Старые события не переигрываются. Две миграции первой реализации оставлены последовательными; обе независимы от requests/schedule FK.
