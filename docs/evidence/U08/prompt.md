# U08 — убрать фоновую надпись главной

Исполнитель gpt-6.1-sol/low, один writer; требования PRD-03/04. Прочитать AGENTS.md, TASK.md, ARCHITECTURE.md §§21–22, PLAN.md §2 и workflow.

Запрос пользователя «убери надпись persona на главной странице»: убрать именно декоративную надпись за заголовком главной (persona-sculpture), сохранить shared brand/nav, title и P-фон входа U07.

Разрешено: apps/dashboard/templates/dashboard/home.html (удалить декоративный div), static/css/dashboard.css (удалить только относящийся к нему последний CSS блок), tests/test_ui_revision_browser.py (убрать obsolete проверку decoration, не писать новый тест, остальные проверки сохранить), docs/evidence/U08/implementation.md. Не удалять SVG файл, не менять данные/серверные контракты/другие файлы. Без делегации/commit до accepted. Проверить Django preview check/ruff/diffcheck и отсутствие ссылок на persona-sculpture в runtime. Это обратимое небольшое изменение: новых tests не требуется. Отчёт краткий. Родитель независимо проверит diff, соберёт статику/обновит локальный сервер.
