# D02-02 — независимое ревью

- Ревьюер: основной агент `gpt-6.1-sol / high`; код — исполнители `gpt-6.1-sol / low` с отдельными областями записи.
- Требования: SEC-02, LIC-01, TECH-03/04/06. Постановки: prompt.md, notices-prompt.md; фактический отчёт: implementation.md и notices/implementation.md.
- Исходный HEAD: `архивная-версия`.
- Статус: **accepted** в границах локального D02-02, с явно сохранёнными остаточными findings и условиями повторной проверки перед публичным релизом.
- Версионирование: pending; публикации сайта нет.

## Фактически проверено основным агентом

| Область | Результат |
| --- | --- |
| Объём | Прочитаны Dockerfiles, изменения dependency groups/lock, Caddyfile, audit/notice/TLS helpers и тесты. Business logic, шаблоны, модели и миграции не менялись. Все29 locked package versions совпадают с исходным HEAD; binary extra перенесён в dev |
| Production closure | Независимая сборка/инвентаризация:12 Python packages, psycopg implementation `python`, libpq170011. Нет psycopg_binary vendor libraries, global pip и ensurepip wheels. App non-root/read-only, сеть/DB-role/секреты проверены отдельным TLS runner |
| Аудит | `independent/summary.json`: completed-with-findings, cleanup complete. App217 (0critical), PG397 (2critical), Caddy6 (0critical). File hashes report/runtime/SBOM проверены. Версии пакетов по Type/Name/Version совпали с final-verified; image tags/IDs у отдельных прогонов различаются. Финальный Caddyfile проверен реальным adapt/validate |
| Источники findings | Прочитаны первичные advisories/distribution trackers для HIGH/CRITICAL групп; оценка сохранена в docs/operations/vulnerability-assessment.md. Нет ignore-файла, severity/unfixed подавления или заявления о нуле CVE |
| Лицензии | Независимо сверены206 исходных текстов и manifest SHA256 `dbe344eb0f8582748997058d10393efa0c76d725d39cc34e570210975d705ff9`;207 bundle files проверены внутри всех3 образов.149 Go archives имеют h1 по HTTPS sumdb,2 stdlib — exacttags, gosu — отдельный exactcommit fallback без заявления о h1. GPLv3 также совпал с системным оригиналом. Исключены4 неприменимых fixture/asset notices с сохранёнными hashes/reasons |
| Реальный HTTPS | `production-independent.json`: passed, cleanup complete. Три роли,360/1440, POST/обработка/сохранение после restart, чужая заявка404, CSRF/headers/static/cookies/DB503/recovery/upstream502/IPspoof проверены |
| Полная регрессия | Независимый root suite377passed,1warning,218.21s, exit0; входные hashes неизменны во время прогона. PostgreSQL17.11/Chromium, собственный изолированный кластер. regression-independent.json. После этого только два переноса format, независимо повторены45focused tests,0.14s; Ruff check all/format6/diff-check exit0 |
| Журналы |10 operational events;0unexpected fields,1TLSmaintenance,3upstream502. Уникальные path/query/header/cookie/auth/body sentinels и QA password отсутствуют; safe source logs приложения сохраняются. Только logger/level/ts/status/duration/err_id. QA truststore installation отключена, строгая схема не ослаблена |
| Сохранность окружения | Allowlist build contexts, собственные уникальные labels/loopback-порты, explicit empty Compose env-file, без host mounts/приватных ключей/production data. TLS/audit cleanup подтверждён. Root suite DB удалена после полного прогона, exact owner/absence checks: cleanup.md |

## Исправления по ревью и границы

Исполнитель устранил ошибки порядка Caddy snippet/import, default namespace exclusion, stdout-only чтения Docker logs и ненужной установки QA CA. Основной агент отклонил расширение допустимой log schema ради static truststore messages: QA доверяет явно извлечённому root.crt, поэтому trust installation не нужна. Production ACME/Caddyfile этим QA преобразованием не меняется. Два format-only переноса исправлены после полного suite; targeted проверки повторены. Нового полного suite после переносов не заявляем.

Тексты сторонних лицензий сохраняются побитно. Полный `git diff --check` может сообщать об исходных пробелах/концах строк только в `docs/third-party/runtime-notices/**`; это разрешённое исключение ради обязательных notices и совпадения hashes. Собственные code/docs проходят проверку без такого исключения; hook/config/attributes не отключаются. Generated raw JSON/SBOM проверяются по схеме, counts/hashes и источнику; их не выдаём за вручную построчно написанный код.

Аудит не доказывает полную symbol/function reachability и coverage каждого native компонента. Контекстное принятие остаточных CVE не исправляет библиотеки; перед публичным релизом нужен свежий scan immutable artifact и сохранение указанных ограничений продукта. Signed mutable OS repositories не дают побитовой воспроизводимости rebuild. Поставка binary artifacts требует применимых source-availability/relinking/notice условий; источник собственного приложения не получает новую лицензию.

D02 — локальная подготовка. Удалённый CI, D03 release/rollback, D04 backups/timers/monitoring, V2, хостинг/публичный HTTPS/РФ/работа до итогов и фактическая сдача остаются отдельными задачами. Не объявляем готовность конкурса или публикацию.
