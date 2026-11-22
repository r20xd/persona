# U15-A · Личные дедлайны

Исполнитель: Codex, gpt-6.1-sol / low. Применён актуальный taste-skill:design-taste-frontend (SKILL.md и copy/copy-voice/system/layout-v4/sections). Сохранены палитра, навигация и компоненты существующего кабинета. Новый пользовательский сценарий — добавить задачу с московской календарной датой, завершить и вернуть в работу обычными HTML-формами.

## Фактическая реализация

- `PersonalDeadline`: UUID, владелец StudentProfile, обязательные title/due_date, nullable completed_at; additive migration 0003, архивные Deadline и уведомления сохранены.
- `/deadlines/` GET/POST: активная студенческая роль и own_profile; создание PRG, server validation, ошибки рядом с полем с Django error id/aria-describedby; never_cache; CSRF middleware. Активные/выполненные списки отдельно по 20; focused own target из уведомления виден независимо от страницы.
- `/deadlines/<uuid>/state/`: явные completed=yes/no, owner scoped lookup, transaction + row lock, повтор не меняет completed_at. Чужой UUID 404, гость login, оператор 403.
- Вкладка sidebar/bottom nav (6 видимых мест), whitelist анимации вкладки в base.html. CSS использует palette vars; мобильный form/list stack; 44px+ кнопки.
- Старый detail route, фильтр и блок учебных сроков удалены из runtime; общий selector скрывает kind=deadline или target_type=deadline, поэтому read/open legacy 404. Исторические модели/сервисные операции оставлены для архивных регрессий, не подключены к runtime.
- Обе demo-команды перестали создавать учебные сроки. Объявления сохранены.
- `send_deadline_reminders`: только незавершённые личные задачи активных студентов, today/overdue по Europe/Moscow, уникальный recipient/deadline/phase; дедуп и блокировка ReminderRun. Старые уведомления не изменяются. Schedule/request target handling сохранён.

## Проверки

На отдельном локальном PostgreSQL 17: `pytest tests/test_deadlines.py tests/test_notifications.py -q --reuse-db` — **21 passed**, 3.03s. Покрыты owner/role/CSRF, escaping, дата и ошибки, повторный вход, завершение/возврат и идемпотентность timestamp, московская граница даты, today/overdue/future/completed/inactive suppression, legacy read/open/detail, повторная рассылка и параллельные напоминания, pagination/focused target, объявления и schedule/request регрессии.

Ruff по notifications, двум server suites, notifications browser suite и prepare_demo_window — passed. `makemigrations --check --dry-run` — No changes detected. После финальных шаблонных изменений повторно `pytest tests/test_deadlines.py -q --reuse-db` — **3 passed**, 0.66s. Независимая приёмка основным агентом.

Добавлен browser round trip 360/1440 в `test_notifications_browser.py`; старый deadline_page удалён из UI revision browser test. Browser/collectstatic и screenshots не запускались исполнителем во избежание коллизии с приёмкой основного агента. Визуальная приёмка, skill gate и screenshot evidence остаются основному агенту; GATE не запускался исполнителем. Нельзя считать это подтверждением мобильной визуальной проверки.

Исправления ИИ: исходная попытка использовала 760px breakpoint для шестой вкладки; исправлено на существующий breakpoint 850px. После ревью добавлены ограниченная пагинация и focus, устранены лишние landmarks и hardcoded цвета. Существующие старые тесты ожидали рассылку архивных сроков — изменены только затронутые ожидания, архивные validation/revision проверки сохранены.

Commit/push/публикация исполнителем не выполнялись. Реальные персональные данные, секреты и пользовательские файлы не использовались.

## Независимое ревью: матрица доступа

Основной агент обнаружил пять устаревших ожиданий маршрута `/deadlines/<uuid>/` в полной серверной suite. В разрешённом follow-up `test_access_matrix.py` переведён на реальную PersonalDeadline и `/deadlines/?focus=<uuid>`: гость 302, владелец 200, оба чужих студента 404, оба оператора 403. Snapshot теперь включает личные задачи, а owner response проверяет приватное название. Новый GET/POST список исключён из общей проверки read-only POST 405 с пояснением: создание и CSRF проверяются в `test_deadlines.py`. Отдельно GET и POST старого маршрута дают 404 без эффекта. Неиспользуемый шаблон `notifications/deadline.html` удалён.

Фактическая проверка: `pytest tests/test_access_matrix.py -q --reuse-db` на том же изолированном PostgreSQL — **143 passed**, 10.54s. Ruff check/format указанного файла — passed. Browser и прочие файлы в этом follow-up не запускались и не менялись.

## Browser follow-up

Основной агент запустил Chrome: обе новые проверки personal deadline round trip прошли на 360/1440 px; старый notification round trip падал из-за удалённой ссылки главной. Тест переведён на основную навигацию «Уведомления»; удалено ожидание открытия архивной учебной задачи, вместо него проверяется отсутствие старого блока и ссылки. Остальные шаги сценария сохраняют объявления и изменение статуса заявки.

По screenshot review основного агента заголовок формы изменён на «Новая задача» (CTA сохранён «Добавить задачу»), между active/completed секциями добавлен scoped отступ 24px. Ruff browser-теста passed. Повторный browser запуск выполняет основной агент; исполнитель его не запускал.
