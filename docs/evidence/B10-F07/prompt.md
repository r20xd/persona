# B10/B11/F07 — уведомления и сроки

Пользователь: «продолжай». Основное ядро входа/расписания/успеваемости/заявок уже реализовано и проверено113tests. Следующий блок по STATE — объявления, личные уведомления и дедлайны. Исполнитель notifications запущен явно gpt-6.1-sol/low, fork_turns=none; основной агент gpt-6.1-sol/high.

Требуются Announcement/AnnouncementRead/Notification, аудитории all/group/faculty и окно публикации, отметки прочтения только своего, приватная лента с ограниченными counts/pagination. Оператор видит только общие объявления. Ссылки на объект повторно проверяют его доступность, не используют произвольный URL. Все записи — plaintext; нет внешней почты/push/LLM.

Deadline связан с offering и опциональной Assessment того же курса, хранит московский aware due_at, отмену и revision. Повторяемая send_deadline_reminders создаёт upcoming<=24h и overdue, не дублируется при повторе/параллельном запуске, не отправляет устаревшее upcoming после срока, учитывает перенос/отмену и опубликованный результат конкретного студента. Отсутствие результата не объявляется доказательством несданной работы. Успешный запуск фиксируется для эксплуатации.

Изменения ServiceRequest и Lesson интегрируются с Notification внутри тех же транзакций, по стабильным UUID/version. Notification failure должен откатить источник и событие. Повторная отправка заявки и старые версии не создают новых уведомлений. Целевые UUID — мягкие ссылки с allowlist, без FK на requests/schedule, чтобы не ломать изолированные migration smoke старых модулей.

Область: apps/notifications/, узкие изменения services/навигации requests/schedule/accounts, config, notifications.css, tests, README и implementation/4PNG здесь. Родитель владеет prompt/review/acceptance, STATE/PLAN/ARCH/AGENTS. Нет новых зависимостей, recursive agents, публикации, private SSH reads и системных изменений. Commit после review, обязательный coauthor команда persōna <noreply@persona.example>.

Приёмка: PostgreSQL17, аудитории/публикация/истечение/read isolation/CSRF/XSS/цели/фильтры; атомарность и дедупликация источников; сроки/revision/suppression per student/missed runs и concurrency. Полный предыдущий suite, реальные миграции, сохранность прежних данных, Chromium360/1440 с CSS200/computed style/no overflow и реальным пользовательским сценарием.

QA только в собственном временном PostgreSQL через native Windows Docker CLI, loopback55432 без host mounts. Перед независимым suite передать контейнер родителю, не запускать pytest параллельно; после приёмки удалить только свой ресурс и остановить серверы.
