# PERS04 implementation

Исполнитель gpt-6.1-sol/low, один writer, без делегации. Выполнено явное изменение объёма по ARCHITECTURE §26: каталог виден активным студентам, остальные данные аккаунта/учёбы не раскрываются; запись по-прежнему только собственная.

- Добавлены GET students/student-detail routes, student-only own_profile gate, own detail canonical redirect на /profile/, strict query q<=80/page+duplicate/unknown validation, stable ordering full_name/pk,20perpage, no-store/noindex.
- directory_profiles использует explicit values projection только pk/FIO/course/group/program/faculty; User/Profile model instances не передаются в directory templates. Detail получает отдельно только выбранные persona fields и card display helper. В каталоге не запрашиваются grades/requests/notifications/schedule.
- Добавлены student list/detail templates и directory.css; поиск/пагинация/empty state работают обычным GET без JS. Detail не имеет edit controls; nav «Студенты», card/editor label «Моя persōna», кнопка «Сохранить persōna». Существующий browser persona test label и design nav count обновлены намеренно.
- Existing /profile/ по-прежнему собственный; сервис write, schema, migration, auth не изменены. Новый каталог — разрешённый read-only способ видеть FIO/academic реквизиты и заполненную persona других, включая same/different group. Это не отменяет owner-only редактор.

Проверки:

- Ruff relevant modules/tests — passed; Django preview check — no issues; git diff --check — passed.
- `TEST_DB_PORT=55439 .venv/bin/pytest tests/test_student_directory.py tests/test_persona.py -q` через escalation на disposable PostgreSQL — **26passed6.25s**, exit0. Code frozen до запуска, не менялся во время suite.
- Tests: audience guest/operator/inactive, methods, own redirect, invalid ID, whitelist context/output, same/different group persona visibility и empty, case-insensitive search, pagination20/3 stable tie-break, query validation, escaping, no-store/noindex, forged owner write isolation и CSRF. Отдельные seeded sentinels academic subject/request comment/notification body отсутствуют в list/detail.
- Новый browser test_student_directory_browser.py360/1440: создание своей persona, другой аккаунт ищет ownername, читает цель/progress без edit controls, empty search, собственная persona остаётся пустой. Optional UPDATE_PERS04_EVIDENCE=1 пишет только новые PERS04 screenshots. Browser запускает родитель независимо; исполнитель не дублировал.

Риск mobile nav6пунктов сообщён родителю до browser; shared CSS пока не менялся (вне исходного allowlist). Авторизация detail/сохранение проверяются серверными тестами, не визуальным осмотром. Пользовательская DB/.env/seed не тронуты. Commit/push не выполнялись, собственный accepted не объявлялся.

## Follow-up: narrow navigation

Parent screenshot review found mid-word wrapping with six navigation links. With explicit allowlist extension, `static/css/workspace.css` now uses 9px labels, -.3px spacing and nowrap only at <=390px; labels and accessible names remain complete, desktop unchanged. `tests/test_design_browser.py` keeps containment checks and additionally requires label text to fit one line. Ruff relevant test and git diff --check passed. Browser rerun belongs to parent; code frozen again, no commit/push.
