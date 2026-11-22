# PERS01 implementation

Исполнитель gpt-6.1-sol / low, один writer, без делегации. Прочитаны постановка и действующие contracts accounts/проектные правила. Реализована приватная «Моя персона» внутри профиля, отдельная от учебного StudentProfile.

Изменения:

- StudentPersona OneToOne/PROTECT, четыре JSON списка фиксированных codes, цель до160, прогресс и updated_at. Additive migration `apps/accounts/migrations/0003_studentpersona.py`; DB Check0–100.
- `persona.py`: нейтральные options, строгая service validation list/codes/count/goal/progress, короткий deterministic tagline до3частей через явные phrase maps. Никаких типов личности/AI inference.
- PersonaForm с accessible checkbox groups, goal/progress; atomic save_persona заново получает own_profile(actor), блокирует parent row, игнорировать owner не требуется — его нет в service signature. Пустая цель нормализует progress0. Сохранение полностью пустой карточки возвращает приглашение.
- GET /profile/ и GET editor не создают записей. GET/POST /profile/persona/ только active student, CSRF, no-store, explicit POST/PRG, ошибки200 с ответами. Параметры owner/id/next не определяют объект или redirect. Учебный профиль read-only, POST /profile/405 сохранён.
- Profile card + editor и локальный persona.css: tags, goal/progress, empty invitation, «Видно только вам», keyboard focus, без JS. Shared header/shortcut links/auth/schema существующих моделей не менялись.

Тесты:

- `tests/test_persona.py`: create/update/clear, GET no writes, validation, XSS escaping, PRG/no-store, same/different group isolation, forged payload, role/guest/CSRF/methods, DB range; MigrationExecutor down/up и fresh SQL/ORM snapshot IDs/full_name/course/group/password.
- `tests/test_persona_browser.py`: 360/1440 selections/goal/progress/save/edit restore, server invalid maxlength path, logout/login persistence, second accountempty, overflow/focus; отдельный UPDATE_PERS01_EVIDENCE=1 пишет только новые PERS01 screenshots. Browser оставлен родителю.

Фактические команды/результаты:

- `.venv/bin/ruff check apps/accounts tests/test_persona.py tests/test_persona_browser.py` — passed.
- `.venv/bin/python manage.py check --settings=config.settings.preview` — no issues.
- `git diff --check` — passed.
- Migration generation через preview settings создала0003; предупреждение sandbox при проверке history подключения5432 (Operation not permitted), пользовательская DB не читалась/не изменялась.
- `TEST_DB_PORT=55439 .venv/bin/pytest tests/test_persona.py -q` через штатный escalation: первый прогон13passed4.90s. После его завершения (не одновременно) усилен migration snapshot и изменена микрокопи; повтор на финальном diff — **13passed4.80s**.
- `TEST_DB_PORT=55439 .venv/bin/python manage.py makemigrations --check --dry-run --settings=config.settings.test` через escalation — **No changes detected**.

Предварительные замечания родителя учтены: грамматический tagline/maps, короткая микрокопи, summary ссылки checkbox errors на fieldset ID вместо пустого id_for_label, fresh snapshot migration вместо cached instances, victim snapshot перед forged POST. Скрытые рассуждения/токены не записывались.

Код заморожен до независимого review. Пользовательские .env/DB не тронуты; новые данные seed не добавлены. Full/browser suite и публичное размещение исполнителем не выполнялись. Собственное accepted/commit/push не объявлялись.
