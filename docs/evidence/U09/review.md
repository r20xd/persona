# U09 review

**accepted**; versioning pending, отдельно versioning.md. Родитель независимо прочитал фактические шаблоны, JS, CSS и test diff. Постановка prompt.md, отчёт implementation.md. Требования PRD-02/04, TECH-06, CORE-02/03/04/05.

Результат: нижние шесть ссылок профиля удалены; общий student header label удалён, actions справа через margin-left:auto. Date и term формы явно data-auto-filter. GET change select/checkbox/date отправляет обычную форму; пустая/invalid date пропускается. Сохранение view и URL обеспечено формой; POST не включён. Кнопки Показать у всех5типов формы помещены в noscript, поэтому с JS отсутствуют без вспышки. Операторский label и login marketing не входят в requested header removal.

Независимые проверки:

- Ruff всего проекта и git diff --check — passed.
- PostgreSQL17 disposable + Chromium: tests/test_ui_revision_browser.py, tests/test_grades_browser.py, tests/test_design_browser.py — **10passed,1existing warning,66.15s**.
- Реальный locator.fill date вызывает навигацию day/week без submit; view сохраняется. Другой scoped semester в isolated DB (term+offering+enrollment student.one), select обновляет grades/session URL+selected+empty state, переключение обратно работает. Проверены existing requests/notifications/operator filters и отсутствие автоматического POST.
- No-JS:5форм с fallback button, date/term/status/kind корректно применяются. На JS страницах Показать отсутствует; шапка без student label, профиль без profile-links.
- Reflow360/390/768/1440, keyboard/focus, control contrast passed.20PNG U09 сохранены без изменения прежних evidence. Родитель визуально просмотрел profile1440: ссылки убраны, шапка правильно выровнена.
- Настроенный local collectstatic:2copied13unmodified39postprocessed; наш Gunicorn HUPexit0. http://127.0.0.1:8000.

В замечании предварительного review тест даты изменён с ручного dispatch на реальный fill, семестра — с повторного выбора того же значения на другое scoped значение и обратно. Новая QA-запись только в disposable DB, пользовательские данные не затронуты. Сервер/auth/schema/dependencies не менялись. Полный suite и public site не проверялись, это локальное исправление. Одна обязательная маркировка концепта сохранена.
