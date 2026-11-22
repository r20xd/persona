# D02-02 — отчёт исполнителя

Статус: работа продолжается; независимая приёмка основным агентом pending. Публикации/commit/push не выполнялись. Требования SEC-02/LIC-01/TECH-03/04/06; исходный HEAD4d1452e.

## Фактический аудит

Официальный Trivy0.76.2 получен из GitHub release после проверки официального checksum. Tar SHA256 `bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf`, binary SHA256 `6a972c69606c7b3ea4c6bdcc6fc9332ea9ad38381624310c1e85cc77345909f3`. Официальная DB schema2 загружена из `ghcr.io/aquasecurity/trivy-db:2`: UpdatedAt2026-11-08T06:39:21Z, DownloadedAt07:29:43Z, SHA256 `931e0ee11580d5df452259b34184bea504d07cd3b1ad50254a2d1b8093d97c18`. Полная metadata — summary.json каждого запуска. Сканирование локальных `docker image save` archives выполняется offline, без socket/mounts/project/home в scanner. Выполнялись vulnerability+license scanners, полные package inventories и CycloneDX, без severity/unfixed suppression. Текущий helper явно отключает implicit config/ignorefile и проверяет binary hash; baseline команды предшествовали этому усилению, файлов `.trivyignore`/`trivy.yaml` в проекте не было.

| Набор | app | PostgreSQL | Caddy | Что измерено |
| --- | ---: | ---: | ---: | --- |
| baseline |293|458|313|Точные D02-01 production images, Caddyfile без QA TLS подмены |
| after |387|400|7|Согласованный переход trixie, pure psycopg/system libpq, Caddy2.11.9; Python base ещё со старыми OS packages |
| after-os-upgrade |217|397|6|Подписанные stable/security OS upgrades |
| final-verified |217|397|6|Финальные production images с проверенными207 файлами notices |

Это количество package/vulnerability instances, не число уникальных CVE. Все наборы завершены scanner и cleanup; raw findings сохранены, никакие CVE не объявлены исправленными только по смене версии. Оставшиеся217 app findings:47HIGH/84MED/86LOW, без fixed version в проверенной DB. PG включает61 Go finding старого gosu stdlib1.24.6; Caddy residual6 относится к Go modules, не к Alpine zlib. Финальная triage и лицензионное решение принадлежат root.

Baseline runtime подтвердил15 отдельных `.so` в `psycopg_binary.libs`, libpq180006, Python SSL3.0.20. Trivy не давал самостоятельного OS coverage этим вложенным библиотекам. После root решения binary extra перенесён в dev group; production closure12, `PSYCOPG_IMPL=python`, системный подписанный Debian libpq5=17.11-0+deb13u1. Глобальный unused pip удалён. Все29 package versions uv.lock неизменны; изменены только четыре runtime/dev dependency edges.

Registry probes подтвердили official tag index digests Python3.13.14-slim-trixie `9662417a...`, PG17.11-trixie `ff871389...`, Caddy2.11.9-alpine `0bbb055b...`; полные pins в Dockerfiles. PG installed/candidate17.11-1.pgdg13+2 одинаковы; server/client packages удерживаются на этой minor. Alpine stable v3.24 предложил zlib1.4-r0. APT index hashes/timestamps сохранены в images и runtime inventory; это mutable signed repository builds, а не обещание побитовой повторяемости. Аудит/выпуск должны привязываться к immutable artifact ID.

## Безопасная диагностика

Caddy named INFO logger ограничен TLS maintenance/obtain; отдельный DEBUG logger — только `http.log.error`, без global debug/access log. Причина: generic `handle_errors` Caddy пишет даже502 на DEBUG; root согласовал сохранение generic body с алертом по техническому status. JSON `message_key=""` подавляет fundamental free text; stock filter отдельно удаляет structured msg/error/request/response/IP/URI/header/trace и остальные dynamic literal fields pinned source. Source audit — logging-source-audit.json (Caddy2.11.9/CertMagic0.25.6). Filter не умеет wildcard allowlist, новые версии требуют повторного аудита источников. Runtime schema должна быть только level/ts/logger/status/duration/err_id; подробный TLS error text намеренно недоступен.

Runner добавляет уникальный sentinel в path/query/Cookie/Authorization/custom header/body/oversized body и проверяет реальные413/403/404/502/DB503. Проверяет отсутствие sentinel/password в app+Caddy logs, непустые operational JSON, TLS maintenance и upstream502, сохранение safe source request events приложения. Raw runtime logs с тестовым вводом в evidence не включаются.

## Проверки и ошибки процесса

- Focused test_image_audit/production/foundation:54passed; Ruff passed.
- Полный host regression после изменения dependency edges:367passed,1warning,170.83s,exit0. Own PG17.11-trixie, фактический SELECT1, generated private credentials, cleanup complete. Host development dependency group использует binary; production pure/system libpq отдельно проверяется настоящим TLS smoke. Aggregate — regression.json. Независимый повтор root описан отдельно ниже.
- Первая TLS попытка дошла до trusted CA и413/403/404, затем не запустила Chromium: временный `/tmp/deanery-browsers` исчез. Это ошибка окружения QA, не успешный browser result. Cleanup complete; locked browser восстановлен; последующие попытки прошли browser-проверки (см. ниже).
- Фактический TLS выявил две ошибки Caddyfile: snippet объявлен после import; default narrow include конфликтовал с автоматически добавленным exclude custom logger. Исправлены порядок snippet и named scopes с default exclude empty namespace. После исправления реальный adapt/validate passed. Следующий TLS прошёл все browser/DB/runtime проверки до новой проверки source logs: Docker CLI выводил application stderr вне stdout-only helper. Исправлен owned reader, захватывающий оба потока, с unit regression. Raw error/runtime logs в evidence не сохранены.
- Offline uv lock initially failed: package cache отсутствовал. Повтор с разрешённой сетью сохранил все версии; не выдавался за успех offline resolution.

- Следующий TLS прошёл функциональные/privacy/source-log проверки, но строгая JSON schema обнаружила три `msg` в unnamed Go standard-log sink. Узкий диагностический probe (cleanup complete) установил, что это статические сообщения smallstep/truststore0.13.0 при установке QA local CA, не клиентские данные. Источники: Caddy2.11.9 `modules/caddypki/ca.go:450`; upstream truststore `truststore_linux.go:19,76`, `truststore_java.go:138`, `truststore_nss.go:128`. Exception для сообщений не добавлялся.
- По решению root generated QA Caddyfile получает только `skip_install_trust` в единственном ожидаемом global block и `tls internal` в единственном site block. Установка CA в container trust не нужна: runner извлекает root.crt и явно доверяет ему в собственном opener. Production Caddyfile/ACME и строгие schema/sentinel/password assertions не изменены. Источник: https://caddyserver.com/docs/caddyfile/options#skip-install-trust . Fail-closed transformation проверена узкой регрессией, включая изменённый/дублированный global/site block; production tests32passed, Ruff check/diff-check passed. Ruff format root выявил две разницы переноса строк; после independent suite разрешённый format-only выполнен. После него45 focused production/imageaudit/notices tests passed, Ruff check всего репозитория passed, Ruff format --check шести затронутых Python/test файлов passed; diff-check passed. Актуальная настоящая TLS репетиция passed, cleanup complete:10 Caddy events,0 unexpected fields,1 TLS maintenance,3 upstream502 events; все sentinel/password и safe app request-log assertions passed. Полный безопасный aggregate — production.json.

## Независимые результаты основного агента

По сообщению root (parent-reported, не собственный повтор исполнителя): fullsuite377passed,1warning,218.21s,exit0, inputs_unchanged=true; aggregate regression-independent.json. Root actual TLS passed с cleanup complete. Root independent image audit completed-with-findings:217app/397db/6Caddy, cleanup complete. Это отдельно от собственного полного прогона367passed и собственного TLS production.json. Исполнитель не присваивает независимую приёмку себе.

## Границы

Финальный notices bundle готов:206 текстов и manifest, source hashes проверены; final-verified audit завершён с217/397/6 findings и cleanup complete. Это residual findings, а не ноль уязвимостей; решение root отражено в docs/operations/vulnerability-assessment.md. Актуальная TLS репетиция passed с cleanup complete; независимая приёмка ещё pending. Caddy adapt/validate на реальном production image passed, ресурсы удалены. Root ведёт primary CVE triage и docs/licenses.md. Нет публичного ACME/размещения, проверки РФ/VPN, гарантий до28ноября, эксплуатационных backup/timers и конкурсной готовности. Исполнитель не принимает собственный результат.
