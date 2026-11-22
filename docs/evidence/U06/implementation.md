# U06 — implementation

Исполнитель: gpt-6.1-sol / low (явный вызов родителя), один writer, без делегации. Прочитаны постановка, TASK.md, AGENTS.md, релевантные разделы ARCHITECTURE.md/PLAN.md и WORKFLOW.md. Просмотрены persona.jpeg и palitra.jpeg.

Изменения:

- Название `persōna` в brand, title, login и preview; исторические документы не переименованы.
- Общая палитра workspace/preview: navy #2F4156, teal #567C8D, sky #C8D9E6, beige #F5EFEB, white. Navy сохранён для основного текста и границ полей ради контраста; teal выделяет активный раздел (white/teal 4.503:1).
- Собственный `static/icons/persona-word.svg`: системная serif-типографика с многослойными контурами/градиентом, полупрозрачный стеклянный эффект по визуальному референсу. Референсы не включены в runtime, внешних шрифтов/изображений/зависимостей нет.
- Декор — абсолютный фон главной с `aria-hidden`, пустым alt и `pointer-events:none`; отдельной строки/высоты не добавляет. На телефоне opacity ниже.
- Сохранены существующие U04: Успеваемость отдельно, сессия в Расписании; GET auto-filters заявок, оператора и уведомлений; fallback submit без JS. Серверные выборки, POST и защита не изменены.
- Сохранена одна общая отметка «Конкурсный концепт · Неофициальный сервис»; убраны два лишних упоминания вымышленности в preview. Ограничения ввода реальных данных и выдачи настоящих документов сохранены.

Проверки до браузера:

- `.venv/bin/ruff check tests/test_ui_revision_browser.py tests/test_design_browser.py tests/test_preview_browser.py` — passed.
- `.venv/bin/python manage.py check --settings=config.settings.preview` — no issues.
- `.venv/bin/pytest tests/test_preview.py tests/test_image_audit.py -q` — 10 passed (0.71s).
- `git diff --check` — passed.

Браузерные проверки и скриншоты: ожидается подготовка родителем disposable PostgreSQL/Chromium. Пользовательская БД не использовалась. Preview не выдаётся за DB scenario.

Commit/push не выполнялись, независимое ревью — родителю.

## Follow-up после независимого screenshot review

Родитель сообщил реальные результаты первой независимой проверки: browser 10 passed / 1 warning (58.38s), server 107 passed (20.49s). На screenshot `home-360.png` оставались повторы маркировки из seeded данных; декор был слишком бледным. Родитель расширил постановку/allowlist на demo-команды и узкий тест.

Выполнено:

- Новые study fixtures получают названия без пометок `(вымышленные данные)`, `(вымышленный)`, `(концепт)`; announcement body — без повторной конкурсной маркировки. Персонажи остаются вымышленными.
- `provision_study_demo` совместим и со старыми, и с новыми известными labels term/teacher/rooms; старые значения не переписывает. Неизвестные несовместимые fixture values по-прежнему отклоняются.
- Добавлена отдельная atomic/idempotent `refresh_demo_labels` с общим advisory demo lock. Обновляет только фиксированные коды term/teacher/rooms/трёх announcements и только при точном совпадении старого текста. Даты, ID, связи, пароли, история заявок/уведомлений и пользовательские тексты не изменяются. Команда не включена в seed автоматически.
- Для существующей базы оператор может явно выполнить `.venv/bin/python manage.py refresh_demo_labels` с корректной окружением приложения; для повторного seed это не обязательно благодаря совместимости. На пользовательской БД исполнитель команду не запускал.
- После просмотра screenshot фон усилен до opacity .4 desktop / .24 mobile; viewBox собственного SVG уплотнён, чтобы слово читалось в имеющейся фоновой области, без изменения потока.

Проверки follow-up:

- Ruff check/format разрешённых Python-файлов — passed.
- Первый sandbox запуск `TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=55439 TEST_DB_USER=deanery TEST_DB_PASSWORD='' .venv/bin/pytest tests/test_demo_labels.py -q` — 2 setup errors: loopback `Operation not permitted`.
- Тот же запуск через штатный `require_escalated` на disposable PostgreSQL родителя — **2 passed, 3.98s**. Проверены повторный refresh, сохранение IDs/связей/дат, customized labels и чужой code, а также повторный seed со старыми labels.
- Итоговые расширенные server/browser проверки обновлённого diff выполняет родитель независимо; их результаты следует брать из review, а не предполагать из прежнего прогона.
