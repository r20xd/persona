# Q05 — предварительное ревью

Статус: **changes requested**. Проверен первый черновик scripts/verify_data_lifecycle.py и tests/test_data_lifecycle.py. Это промежуточное решение, окончательная приёмка — review.md после исправлений и независимого выполнения.

| № | Место | Риск / требование | Исправление и проверка |
| --- | --- | --- | --- |
| 1 | Rehearsal.execute: docker run → container_created | Docker может создать контейнер и вернуть ошибку при запуске/публикации порта; флаг ещё False, cleanup пропустит свой ресурс | Отдельные create/start, регистрация успешно созданного ресурса до start; тест отказа запуска и очистки |
| 2 | volume create / mount / cleanup | volume create идемпотентен: при коллизии имени возможно подключение существующего volume. Exit0 удаления сам по себе не подтверждает отсутствие ресурса | Проверка exact отсутствия до создания и ownership сразу после, до mount; очистка только точных собственных ресурсов, сверка отсутствия |
| 3 | Docker subprocess environment/context | У пользователя могут быть DOCKER_HOST/context на удалённый daemon; локальный QA не должен автоматически создавать ресурсы там | Проверить effective локальный endpoint, исключить невалидированные overrides. Отказ до мутаций для remote; meaningful test |
| 4 | collectstatic / settings | Общий repo/staticfiles может обслуживаться пользовательским dev-web | Отдельный temporary STATIC_ROOT через узкий QA settings wrapper, общий для collectstatic и собственного web; cleanup после остановки web |
| 5 | stop_web | Уже завершившийся web-процесс не должен давать ложный отказ cleanup | Учитывать poll/ProcessLookupError; работать только с собственным Popen |
| 6 | test_previous_schema_upgrade_preserves_existing_student_request | Строка anchor_date, переданная через keyword call_command, обходит argparse date parser | Передать datetime.date или CLI option; реально выполнить тест |
| 7 | main / assert проверки | Python -O удаляет assert вместе с HTTP-вызовами и сравнением данных | Отказ до мутаций при not __debug__ либо явные проверки без assert; safety test |
| 8 | pg_dump / pg_restore subprocess | Raw subprocess обходят очищенный Docker env и могут выбрать другой daemon | Один и тот же проверенный Docker environment у всех вызовов |
| 9 | create timeout / interrupt | Daemon мог создать ресурс до timeout, когда created flag ещё False | Регистрировать попытку до command; cleanup различает exact отсутствие/своё владение/чужое владение; timeout-after-create test |

Сильные стороны черновика: явный safe env приложения, loopback, уникальные ownership labels, полный браузерный путь, сохранённая сессия после перезапуска и restore, сравнение данных в памяти, временный binary dump без вывода, отдельная БД назначения. Их нужно сохранить при исправлениях.

Миграционный тест notifications0001→0002 описывать точно: это обновление предыдущей схемы с additive index/default, а не доказательство произвольного rollback релиза. Полноценная эксплуатация, offsite encrypted backup, авария узла, SIGKILL runner и production restore за пределами Q05.

Завершить проверку только после повторного выполнения lifecycle, критических отказов очистки, PostgreSQL migration test и необходимого regression suite. Пользовательский .env/БД/процессы не использовать.
