# Q06 — независимое ревью

- Ревьюер: основной агент, роль Sol/high. Исполнитель кода запущен явно как `gpt-6.1-sol / low`, `fork_turns=none`; восстановление среды выполнено таким же исполнителем после перезапуска сессии.
- Постановка: [prompt.md](prompt.md), отчёт: [implementation.md](implementation.md).
- Требования: TECH-03/04/06, PRD-02/05, SEC-01/02, LIC-01 в описанных границах.
- Решение: **accepted, локальный объём Q06**. Версионирование отдельно, до commit — pending.

## Что проверил основной агент

| Область | Независимая проверка | Результат |
| --- | --- | --- |
| Объём | Прочитаны все три новых Python-файла, docs/evidence и методика. Сверены Git status/diff и lock | Приложение, настройки, схема, зависимости и lock не меняются; добавлен QA runner, измерения и документация |
| Подлинность нагрузки | Прочитаны CSRF login, CookieJar/sessionid uniqueness, 20-worker barrier, warmup, URL/body validation, pre/post isolation | Двадцать отдельных реальных серверных сессий; login200/redirect/неверная страница отвергаются; Argon2 не ослаблен |
| Регрессии | `PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=55432 TEST_DB_USER=deanery TEST_DB_NAME=test_deanery TEST_DB_PASSWORD='' .venv/bin/pytest -q` | **185 passed, 1 warning, 158.80s**, exit0; warning прежний, из pytest-playwright о будущем pytest10 |
| Измерение | Независимый `python -m scripts.verify_performance --docker <native Windows Docker CLI>` после окончания полного suite | exit0; 120 warmup, 360 measured GET, p50=70.091ms, p95=178.658ms, max=241.171ms; login p95=93.132ms; 0 ошибок/5xx/неожиданных redirects; target_met=true |
| Query audit | Прочитаны initial/expanded sizes и полный GET через execute_wrapper с materialized templates; повторён своим запуском | Counts initial→expanded: dashboard26→26, schedule7→7, grades8→8, session9→9, requests6→6, notifications16→16, operator5→5 |
| Защита QA | Прочитаны наследуемые clean environment, ownership-before-delete и timeout-after-create cleanup; проверен tmpfs вместо anonymous PG volume | Только собственные loopback web/PG, входных production DSN/URL нет, ошибки без secret messages. Независимый runner завершил web и подтвердил отсутствие своего контейнера: cleanup_complete=true |
| Обычные проверки | Независимо Ruff, format check новых файлов, Django check, diff check | Tracked unstaged diff check exit0; полный staged diff check: единственное замечание upstream trailing space в libargon2-LICENSE.txt:6 принято root ради SHA256-identical notice; остальные25путей passed. Ruff/format/Django exit0. Исполнитель отдельно выполнил migration consistency check: no changes detected |
| Advisory audit | Прочитаны результаты и metadata PyPA pip-audit2.10.1, сопоставлены версии с lock/installed metadata | Runtime13 и runtime+dev26 Linux packages, включая psycopg-binary; 0 известных advisories, оба запроса completed/exit0. Родитель проверил отчёты, повторный сетевой advisory audit не запускал |
| Лицензии | Родитель проверил installed versions и SHA256 всех 51 перечисленного license/notice файла 26 дистрибутивов; дополнительно прочитал 4 точных sdist после SHA256 verification | Реестр 28 пакетов, включая 2 Windows-only; libargon2 notice сохранён без изменения; отмечены LGPL/Artistic и native/OS границы. См. license-inventory.json, license-source-check.json и docs/licenses.md |
| Assets | `rg` по static, app static и templates; перечень исходных CSS/JS/SVG | Нет CDN, webfonts или сторонних изображений; SVG namespace не является fetch. UI не изменён |
| CI | Read-only unauthenticated GitHub Actions API для исходного SHAa14c5b5 | HTTP403, статус **unverified**, не выдан за успешный CI; ci-status.json |

## Замечания и исправления

Первоначально QA container наследовал image VOLUME и оставлял anonymous PG volumes. Исполнитель заменил mount на explicit tmpfs и повторил прогон; это исправление очистки, а не оптимизация приложения ради цифры. Пять ранних volumes уже удалены предыдущим исполнителем по его отчёту. Сохранившиеся reconstructed ownership/mount records и container IDs прочитаны родителем; исходные raw daemon events после перезапуска недоступны, поэтому родитель не утверждает независимое наблюдение тех удалений. Удаления не повторялись, broad prune не применялся. См. resource-repair.json.

После ревью документации закреплена точная версия audit tool в командах воспроизведения; исправлено описание provenance cleanup evidence. Ошибки прежних запусков из-за отсутствующего браузерного cache и исчезнувшего временного Python отражены как ошибки среды. Их успешные повторы подтверждены. Обязательных незакрытых замечаний к текущему коду нет.

## Границы принятого результата

Это localhost warm-read smoke на WSL2/AMD Ryzen7 9800X3D, 16 logical CPU/~16GB и tmpfs. Длительность измеренной фазы 2.385s, dataset намеренно небольшой. Это не sustained soak, disk benchmark, одновременный вход 20 Argon2 или гарантия production capacity VPS2vCPU/4GB. Неизменное число SQL-запросов не ограничивает размер HTML/памяти: grades/session/schedule ограничены учебным периодом и enrollment, без численного cap; fixed dashboard/notifications queries оценены в методике. Ослабление авторизации или преждевременный app refactor не нужны.

Публичный сайт, доступность из РФ, полный native/OS состав production-образа и его условия распространения, HTTPS/proxy/CSP, аппаратный телефон и V2 не подтверждены этим этапом. Итоговый LIC-01 и готовность к сдаче не объявляются закрытыми. Следующий полезный блок — итоговая матрица Q01/Q02; production D02 и публикация проходят свои проверки и V2.

## Версионирование

После финальной проверки документации основной агент передаёт точный allowlist исполнителю. Только обычные commit/push в `main`/`origin`, с trailer `атрибуция команды`, без обхода hook. Перед отправкой проверяются staged diff, отсутствие секретов/чужих изменений; после отправки — фактическое совпадение HEAD с `git ls-remote origin refs/heads/main`. Результат — [versioning.md](versioning.md). До такой сверки состояние Git не называется pushed.

Собственная suite-БД удаляется после независимых проверок отдельно от автоматического cleanup нагрузочного runner; exact inspect/cleanup и результат — [cleanup.md](cleanup.md).
