# PERS01 review

**accepted**, версионирование pending (отдельный versioning.md). Ревью — основной агент, независимое чтение фактического кода и собственные проверки. Постановка prompt.md, отчёт implementation.md. Требования PRD-01/02/03/04/05, SEC-01, TECH-03/06, DATA-01; дополнительный объём явно поручен пользователем.

## Принятый результат

В профиле доступна приватная «Моя персона»:4группы выбранных тегов, краткая фраза из собственных ответов, цель и самостоятельно отмечаемые0/25/50/75/100%. Редактор поддерживает частичное заполнение, изменение и очистку, пустое приглашение. Учебные реквизиты остаются read-only. Типы личности, внешние ИИ-вызовы и sharing отсутствуют. Собственный CSS и тексты без новых dependencies/материалов.

StudentPersona — отдельная OneToOne с profile/PROTECT; atomic service проверяет own_profile(actor), блокирует parent row и валидирует типы/коды/размеры/goal/progress. Нет owner/id из HTTP для выбора записи. GET не создаёт данных, POST CSRF/PRG, private no-store, оператор403, прямой ID URL404, методы405. Goal экранируется Django. Invalid form сохраняет введённые ответы; empty goal нормализует0. Схема расширена только новой таблицей через0003, существующие учебные поля не меняются.

## Независимые проверки

- `uv run --locked ruff check .`, `git diff --check` — passed.
- Disposable PostgreSQL17/Chromium: `pytest tests/test_persona.py tests/test_accounts.py tests/test_access_matrix.py tests/test_persona_browser.py tests/test_design_browser.py -q` — **173passed,1existing pytest fixture warning,78.38s**. Код frozen на время прогона.
- Проверены создание/обновление/очистка, validation неизвестных codes/типов/слишком длинной цели/прогресса, XSS, CSRF, GET без writes, PRG/no-store, owner payload/next подмена, same/different group isolation, operator/guest/methods, DB range. Additive migration test заново читает SQL snapshot профилей/passwords до/после down/up (только isolated DB).
- Реальный browser360/1440: selections+goal+50%, save, повторное открытие editor с прежними ответами, invalid server path и сохранение остальных полей, logout/login persistence, second studentempty, keyboard focus и overflow. Existing design проходит360/390/768/1440;4новых PNG сняты и просмотрены, historical evidence не менялись.
- Предварительное review исправило неграмматичный/длинный tagline, fieldset error anchors, первоначально cached migration snapshot и формулировку прогресса. Новый прогон подтверждает итоговый diff.

## Локальное применение и сохранность

Перед миграцией штатный pg_dump custom создал закрытый backup локальной базы вне Git: /tmp/persona-pers01-before-4f5b.dump,140579bytes,mode0600. Содержимое не выводилось. Затем штатно загружен приватный .env без вывода, makemigrations --check --dry-run — No changes detected, accounts0003 — OK. Свежие SQL snapshots существующих users(pk/username/password/role/active/staff/superuser) и полных profile реквизитов до/после совпали. `check` no issues, collectstatic и HUP нашего локального Gunicorn exit0. Адрес http://127.0.0.1:8000/profile/. Новые persona в пользовательской DB не seed-ились.

QA container persona-pers01-qa удалён после suite (exit0), локальные пользовательские DB/server оставлены для просмотра. Backup restore в этом этапе не тестировался. Полный suite/public deployment/CI не выполнялись; локальная приёмка этой функции не означает готовность всего конкурса. Untracked пользовательские .DS_Store/persona.jpeg/palitra.jpeg вне изменений.
