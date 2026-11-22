# B01/B02 — отчёт исполнителя, 2026-11-04

Исполнитель: gpt-6.1-sol / low. Требования: CORE-01, SEC-01/02,
DATA-01, DEMO-01/02, TECH-03/06; минимальный реальный экран профиля F02.

Сделано: справочники Faculty/Program/StudyGroup; StudentProfile с полным ФИО,
курсом1–6 и защищёнными ссылками; уникальный OperatorScope; role validation в
full_clean/сервисах. Отдельные additive миграции academics0001/accounts0002.
Серверный selector профиля принимает только текущего пользователя.

Django auth + DBsessions + Argon2, POST logout/CSRF, безопасный next,
одинаковая ошибка для неизвестного/деактивированного пользователя, no-store.
При восстановлении BFCache реальных приватных экранов внешняя JS перезагружает
страницу. Публичного admin/signup/edit нет. Root показывает реальный профиль;
оператор направлен на честный экран очереди, ещё не реализованной в B09.
Собственные CSS поверх принятой V1 палитры, форма с labels/autocomplete,
полный профиль без фиктивных расписаний/оценок, бренд конкурсного концепта.

provision_accounts создаёт fiction-only студентов разных групп и ограниченного
оператора, пароли только из private env/getpass, validate_password/set_password.
Повтор не изменяет данные; несовместимая существующая запись вызывает ошибку.
Это bootstrap аккаунтов, не B12 seed. purge_auth_attempts удаляет истёкшие
security-счётчики без вывода посетительских данных.

Новая зависимость django-axes9.0.0, MIT: актуальный релиз PyPI30.10.2026;
официальные источники проверены:
https://pypi.org/project/django-axes/9.0.0/
https://django-axes.readthedocs.io/en/latest/4_configuration.html
PyPI заявляет Python3.13/Django5.2. Nested lockout parameters ограничивают
username+IP, 10 ошибок/15мин; AXES_USE_ATTEMPT_EXPIRATION=True.
IP callable читает только REMOTE_ADDR, не XFF. DB handler, logs/failurelog
отключены; обычный safe logger проекта не выводит auth payload.
uv add сначала упал из-за sandbox DNS; authorized escalation успешно установила
Axes и обновила lock. Прочитан установленный код settings/handler/model для
проверки имён настроек и expiry модели.

## Фактические проверки

- uv run ruff check . — exit0.
- uv run ruff format --check . — exit0 (68 файлов на тот момент;
  последующие новые Python файлы также отформатированы).
- uv run python manage.py check — exit0.
- uv run python manage.py makemigrations --check --dry-run — exit0,
  No changes detected; warning consistent history unavailable без PostgreSQL.
- uv run pytest tests/test_accounts_public.py tests/test_foundation.py
  tests/test_preview.py -q — exit0, 31 passed. Preview по-прежнему без БД.
  WhiteNoise предупреждает об отсутствии collectstatic каталога.
- uv run pytest tests/test_accounts.py -q — exit1, первоначальные10 тестовых
  вариантов дали setup errors PostgreSQL connection unavailable; тела DB тестов
  не выполнялись. После добавлен дополнительный session/PROTECT тест, полный
  актуальный DB набор11 вариантов ожидает PostgreSQL. SQLite не применялся.

UV_CACHE_DIR=/tmp/deanery-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/deanery-python
использованы при uv командах. Docker/системные права не изменялись.

## Требуется независимая проверка

Реальные migrate на PostgreSQL17, DB security/provision/session тесты, миграция
с сохранением существующих user; реальный browserlogin/logout/BFCache/360px.
Полный B01/B02 не считается принятым без DB. Опубликованный сайт и РФ
доступность не проверялись. Commit/push не выполнялись. STATE/PLAN/ARCH и
родительские evidence не изменялись.

## Продолжение: реальный PostgreSQL и браузер

Прежняя DB-блокировка снята после обнаружения native Windows Docker CLI:
`/mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe`.
Linux socket остаётся недоступен; систему и права не меняли. Через штатную
escalation создан owned ephemeral контейнер `deanery-b01b02-20261104-accounts`:
`run -d --rm --name deanery-b01b02-20261104-accounts
-e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_USER=deanery
-e POSTGRES_DB=deanery -p 127.0.0.1:55432:5432
postgres:17.11-bookworm@sha256:839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`.
Без host mount/volume; trust применяется только к disposable QA, не dev/prod.
Psycopg под escalation подтвердил PostgreSQL17.11 на127.0.0.1:55432.

`DB_PORT=55432 TEST_DB_PORT=55432` (остальные defaults deanery/127.0.0.1,
password unset), `PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers`, прежние UV env.
`uv run python manage.py migrate --noinput` — exit0, все новые схемы и Axes OK.
`uv run pytest --browser-channel chromium -q` — финально exit0, **46 passed**.
Первый полный прогон45passed/1failed выявил ошибку тестовой fixture cooldown:
expires_at изменили на прошлое, но attempt_time оставался настоящим. Установили
обе отметки согласованно, как при реальном истечении15мин; исправление только
в тесте. Не отключали Axes и не заменяли PostgreSQL.
Прошли реальные DB constraints, cross-account и same-group profile isolation,
login/logout/CSRF, sessionexpiry (session expire_date в прошлом), deactivation,
Axes combination+spoofedXFF+cooldown, provision/idempotency/incompatible flags.

Дополнительный MigrationExecutor-подобный smoke: отдельная disposable БД
`test_deanery_migration`, migrate accounts0001 → существующий User с runtime
password → все новые migrate. PK, passwordhash, role, is_active сохранены.

Реальный Playwright smoke из `/tmp/deanery_accounts_qa.py`: provision дважды,
случайные runtime-only QA passwords в disposable БД (не скриншоты/логи/envfile),
collectstatic, Gunicorn/WhiteNoise на127.0.0.1:8007. Оба студента вошли по форме,
профили изолированы; reload и /profile/ сохраняют данные; POSTlogout и Back
возвращают вход без прежнего ФИО; 360/1440px без overflow и pageerror.
Проверены HTTP200 обеих CSS и computedStyle карточки borderRadius20px.
Первый runserver --insecure smoke дал неоформленный screenshot из-за hashed
static404; при визуальном осмотре это обнаружено, QA переведено на Gunicorn,
финальные screenshots заменены. README реальный запуск исправлен соответственно.
При просмотре mobile увеличен текст значений профиля до16px и усилен цвет
подписи бренда. Окончательные артефакты: login-360.png, login-1440.png,
profile-360.png, profile-1440.png. Пароли нигде не показаны. Все QA webserver
завершены в finally.

По поручению родителя контейнер временно передан ему для независимого review
и повторного suite; не удалён до его просмотра screenshots. Другие контейнеры
не затронуты. Cleanup owned контейнера требуется после этой передачи.
Публичный релиз, Q05 restart persistence и реальный телефон по-прежнему pending.
Родитель выдаёт accepted, исполнитель не принимает собственную работу.

## Cleanup после accepted

Родитель подтвердил независимый suite и визуальный просмотр. По его поручению
native `docker.exe stop deanery-b01b02-20261104-accounts` завершился exit0.
Контейнер был --rm; последующий `docker.exe ps -a --filter
name=deanery-b01b02-20261104-accounts --format '{{.Names}}'` вернул пустой
результат, exit0. Owned QA контейнер и его временные БД удалены. Images,
чужие контейнеры/volumes и системные права не изменялись.
