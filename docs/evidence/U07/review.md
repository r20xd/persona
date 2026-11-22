# Ревью U07

Статус: **accepted**. Версионирование pending, отдельно versioning.md. Ревью — родитель; постановка prompt.md, отчёт implementation.md. Требования PRD-03/04, TECH-06, BRAND-01, LIC-01.

Независимо прочитан diff всех шаблонов/CSS/tests, просмотрен результат imagegen и реальные login360/1440 screenshots. Прозрачная P сохраняет форму пользовательского reference и адаптирована к navy/teal/sky/ivory. Встроенный imagegen и точный prompt — imagegen.md; asset сохранён в workspace. Лицензия пользовательского исходника не предоставлена, исключительные права и готовность лицензирования к сдаче не утверждаются.

Знак заменяет куб в shared/preview brand и favicon; доступное название persōna остаётся текстом, картинки с пустым alt. Крупные фоновые P decorative aria-hidden/absolute/pointer-events none, контент выше. На360px форма и submit помещаются в первый экран, фон заметен, читабельность сохранена. Основная U06 не меняется. Серверная auth/permissions/данные/схема/POST не затронуты.

Независимые проверки:

- `uv run --locked ruff check .` и `git diff --check` — passed.
- PostgreSQL17 + Chromium: tests/test_design_browser.py + test_ui_revision_browser.py + test_preview_browser.py — **10 passed,1 existing warning59.73s**. Проверены360/390/768/1440, overflow, keyboard/focus, logo loaded, decor semantics, filters/сессия и no-JS fallback.
- Сняты и просмотрены docs/evidence/U07/login-360.png и login-1440.png с реального local DB-backed login. Исторические screenshots не перезаписывались.
- Локальный collectstatic —3copied12unmodified40postprocessed, exit0; запущенный ранее нами Gunicorn обновлён HUP, exit0. Адрес127.0.0.1:8000/login/.

Исполнитель отдельно сообщил Django check no issues, preview6passed0.42s; это не подменяет независимые проверки выше. Полный suite и публичное размещение не выполнялись. Вымышленные данные и обязательная одна отметка концепта сохранены. Оригинальные persona.jpeg/palitra.jpeg/.DS_Store вне коммита.
