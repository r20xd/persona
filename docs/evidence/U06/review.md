# Ревью U06

- Ревьюер: основной агент, независимое чтение diff и проверки.
- Постановка: prompt.md; отчёт: implementation.md.
- Требования: PRD-02/03/04, CORE-02/03/04/05, BRAND-01, TECH-06.
- Статус: accepted. Версионирование: pending, отдельный versioning.md.

Проверен фактический diff шаблонов/палитры/декора, provisioner compatibility и refresh command. Буквы aria-hidden, не участвуют в потоке/кликах; SVG оригинальный, без внешних материалов. Картинки пользователя — только reference и не входят в commit. Общая отметка концепта обязательна по TASK.md и оставлена один раз. Пункты 3–5 были реализованы U04 и независимо подтверждены; не выдаются за вновь написанную логику.

Независимые проверки родителя:

- Ruff всего проекта, Django preview check и git diff --check — passed.
- Серверный focused suite accounts/grades/schedule/requests/notifications/preview/image notices — 107 passed20.49s (до изменения demo defaults).
- Первый UI suite ui_revision/design/preview — 10 passed1warning58.38s. Первая попытка до завершения установки Chromium дала10setup errors (executable missing), это ограничение подготовки, затем устранено.
- После окончательных demo/default/decor изменений: tests/test_demo_labels.py + test_dashboard_demo.py + test_ui_revision_browser.py + test_design_browser.py — 20 passed1warning71.65s. Проверены реальные GET select/checkbox, отсутствие видимой Показать с JS и fallback без JS; session navigation; контраст controls; reflow360/390/768/1440 и keyboard; повторное seed; idempotent refresh, связи и custom text.
- Визуально просмотрены реальные home360/1440 screenshots; финальный home360 с более заметными буквами и без лишних seeded пометок. Скриншоты U06 сохранены, исторические не переписывались.
- В настроенной локальной БД штатной командой обновлено7 точно известных labels, collectstatic:4copied10unmodified40postprocessed. Приватный .env использован без вывода. Локальный Gunicorn:127.0.0.1:8000.

Безопасность: серверные scoped выборки/POST/auth/schema не изменены. Команда refresh atomic + общий demo lock, условие code AND exact old text; не переписывает user text/историю заявок/пароли/дату/аудиторию. Оба legacy/new labels совместимы с повторным provision. Полный suite на этом этапе не запускался; достаточные focused проверки выше. Warning — существующий pytest fixture deprecation. Публичный сайт/доступ из России не проверялись и публикация не выполнялась.

Сохранены untracked пользовательские .DS_Store, persona.jpeg, palitra.jpeg вне этапа. Приёмка не означает конкурсную готовность или отправку.

После проверок временный контейнер persona-u06-qa удалён штатно (`docker rm --force persona-u06-qa`, exit0). Пользовательский local server/DB оставлены для просмотра.
