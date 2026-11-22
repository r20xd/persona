# Q05 — независимая приёмка

- Постановка: [prompt.md](prompt.md); отчёт Sol/low: [implementation.md](implementation.md).
- Предварительные замечания основного агента: [review-01.md](review-01.md).
- Требования: CORE-01/04/05, TECH-02/03, SEC-01/02, DATA-01, DEMO-01/02.
- **Статус: accepted** в границах локального Q05. Версионирование на момент записи pending; итог commit/push сверяется отдельно.

## Независимые проверки

Основной агент прочитал окончательный runner, QA settings, migration/safety тесты, отчёты, README и фактический diff. Код приложения, зависимости, lock и миграции не менялись. Дополнительные документы основного агента — инвентаризация Q01/Q02, обновление STATE/PLAN, снятие устаревшей неопределённости палитры и подтверждение SHA предыдущего этапа; это не расширение функциональности.

| Область | Результат основной проверки |
| --- | --- |
| Пустая БД / формы | Настоящие migrate/seed, DEBUG=False Gunicorn/WhiteNoise и Chromium, отправка новой заявки и scoped переход оператора, прочтение события и объявления |
| Restart web | При том же SECRET_KEY работает прежняя сессия, свой UUID/статус/история доступны; второй студент получает404 |
| Restart PG | Реальный stop/start PG-процесса с named volume; readiness503 в период недоступности,200 после восстановления; данные/сессия сохранены |
| Dump/restore | Binary pg_dump во временный закрытый stream, pg_restore с exit-on-error в другую БД; сравнение restored и исходной БД с baseline, повтор seed не меняет данные |
| Сравнение | В памяти сопоставляются пользователи/hash (без last_login), профиль, scope, enrollment, grades, занятия/история, заявки/события, уведомления, сроки, объявления/read; hash/пароли/cookies/DSN не выводятся |
| Миграции | Historical models: notifications0001→0002 при сохранённых остальных leaf, существующая заявка и два события, профиль/hash/grades/lesson сохранены; finally возвращает leaf |
| Изоляция QA | Пользовательский .env не загружается, env очищен, локальный endpoint, random names/labels, отсутствие до create, ownership до mount/delete; отдельная временная статика |
| Отказы runner | Новый suite проверяет чужую ownership, inherited secrets, remote Docker, -O, timeout-after-create и start failure. Регистрируется попытка до create, очистка сверяет exact отсутствие. Девять замечаний review-01 устранены |

Команды основного агента:

```text
PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/python scripts/verify_data_lifecycle.py --docker /mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe
→ exit0, ok=true, четыре стадии, cleanup_complete=true

.venv/bin/ruff check .             → exit0, All checks passed
.venv/bin/ruff format --check .    → exit0, 164 files already formatted
git diff --check                  → exit0
DB_NAME=deanery DB_HOST=127.0.0.1 DB_PORT=55432 .venv/bin/python manage.py check
→ exit0, no issues
DB_NAME=deanery DB_HOST=127.0.0.1 DB_PORT=55432 .venv/bin/python manage.py makemigrations --check --dry-run
→ exit0, No changes detected
DB_NAME=deanery DB_HOST=127.0.0.1 DB_PORT=55432 TEST_DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest --browser-channel chromium -q
→ exit0, 152 passed, 1 warning, 75.62s
```

Число файлов Ruff в собственном отчёте исполнителя отличается на1; здесь приведён фактический результат независимой команды. Warning pytest-playwright о будущем pytest10 существовал ранее. UPDATE_EVIDENCE не задавался, исторические PNG не менялись. Последние изменения после прогона — только статусные документы, код заморожен исполнителем до независимого запуска.

Сырой безопасный результат независимого lifecycle: [independent-lifecycle-result.json](independent-lifecycle-result.json). Его exact container `deanery-q05-97cfc3f04be0478f9fbe7f94b0e41765` и volume `deanery-q05-data-97cfc3f04be0478f9fbe7f94b0e41765` удалены самим runner после ownership и проверки отсутствия. Web и private temporary files очищены. Отдельная suite БД на55432 оставлена лишь до завершения проверки/версионирования и будет удалена exact-name/label операцией.

## Решение и границы

Нерешённых замечаний в границах Q05 нет. Подтверждена локальная сохранность при штатном restart и логическом dump/restore. Это не гарантия для SIGKILL runner, отказа daemon/диска или потери узла; такие ситуации могут потребовать ручного cleanup только после ownership-проверки. Не подтверждены offsite encrypted backup, production restore/rollback, расписание backup, публичный сайт, сети РФ, физический телефон и V2. Другие Q/D не объявлены завершёнными.

Сопутствующие [access-matrix.md](../../testing/access-matrix.md) и [integrity-review.md](../../testing/integrity-review.md) честно описывают уже покрытые случаи и остатки Q01/Q02. Следующий полезный блок — Q03/Q04/U03, затем Q06 и production-контур после необходимых согласований.

Разрешён следующий ограниченный шаг исполнителя: точный staged allowlist, `test(Q05): verify restart and isolated database restore`, main/origin, обязательный `атрибуция команды`, без force/amend. Перед push проверить trailer, после — HEAD=ls-remote. Затем удалить только suite container `deanery-q05-suite-7214fd9e1fbf4e51922d7a1bd1d5ab4e` после проверки его label; пользовательскую dev-среду не трогать.
