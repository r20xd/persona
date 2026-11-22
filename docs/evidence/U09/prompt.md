# U09 — профиль, шапка и все автофильтры

Исполнитель gpt-6.1-sol/low, один writer. Читать TASK.md, AGENTS.md, ARCHITECTURE.md §§7/19–23, PLAN.md §5, docs/agents/WORKFLOW.md. Требования PRD-02/04, TECH-06, CORE-02/03/04/05.

Запрос пользователя:
1. В профиле убрать целиком нижний .profile-links с шестью действиями; профиль/основную навигацию сохранить.
2. Убрать «Личный кабинет студента» из общей верхней шапки всех вкладок. Операторский label можно оставить. Выравнивание actions справа должно сохраниться после удаления label; не удалять login marketing текст, это не вкладка.
3. Во ВСЕХ GET-фильтрах сразу применять изменение select/checkbox/date без Показать. Пробел: schedule-filter input date, term-filter grades/session ещё не подключены. Сохранить корректный view при date change; семестр и URL/history работают; POST не автоматизировать. После выбора даты событие change сразу вызывает одну GET навигацию. Для невалидной/неполной даты не отправлять. Без JS сохранить рабочий submit через noscript. Кнопки Показать перенести в noscript для всех пяти filter form типов (requests/notifications/schedule/grades/session), чтобы при JS они не вспыхивали/не отображались. Расширить existing filters.js и aria-describedby до input[type=date]. Не включать неизвестные формы автоматически.

Разрешённые записи: apps/accounts/templates/accounts/profile.html,header.html; apps/accounts/static/accounts/filters.js; apps/schedule/templates/schedule/{schedule,session}.html; apps/grades/templates/grades/study.html; apps/requests/templates/requests/list.html; apps/notifications/templates/notifications/feed.html; static/css/workspace.css (только выравнивание header); tests/test_ui_revision_browser.py, tests/test_grades_browser.py (старый clickПоказать заменить expect navigation на select); docs/evidence/U09/implementation.md и новые screenshots. Не менять модели/миграции/сервер/auth/deps/прочие файлы, не делегировать, без commit до accepted.

Проверки: meaningful browser existing ui revision расширить date change day/week с сохранением view, term select grades/session (если один term — создать второй term только QA fixture scoped db), отсутствие visible Показать на всех этих страницах; профиль без .profile-links и без header student label; no-JS fallback по возможности включить schedule/term. Проверять360/1440, CSS alignment, не автоматизировать operator transition POST. Сохранить U09 screenshots при отдельном флаге (не исторические U06). Статика/check/ruff. Родитель даст изолированную БД и независимо прогонит tests; не трогать user DB.

Отчёт: реальные файлы, команды/результаты/ограничения. Не объявлять собственное accepted.
