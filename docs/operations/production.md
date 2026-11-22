# Локальная репетиция production-контура (D02-01)

Это контур для будущего размещения и собственная локальная проверка, не опубликованный сайт. Публичный TLS, доступ из России, срок работы, release/rollback, backups и полный native/OS license/CVE audit ещё не подтверждены. HSTS намеренно 0 до проверки публичного HTTPS; `check --deploy` предупреждает W004.

Для существующего размещения используйте [инструкцию по обновлению и восстановлению](update-recovery.md).

## Сборка

Из корня проекта на Linux Docker Engine/Compose v2:

```sh
docker build -f deploy/Dockerfile -t deanery-app:reviewed .
docker build -f deploy/Dockerfile.postgres -t deanery-postgres:reviewed .
docker build -f deploy/Dockerfile.caddy -t deanery-caddy:reviewed .
```

Все upstream images закреплены version+digest в Dockerfiles. Перед релизом нужно обновить и проверить их аудит; pin не обещает отсутствие будущих уязвимостей. App устанавливает только runtime-зависимости из неизменённого `uv.lock`; collectstatic выполняется offline build settings и сохраняет manifest. `.dist-info/licenses` и libargon2 notice остаются в образе. Runtime uid/gid 10001, корень read-only, временные файлы только в ограниченном tmpfs; Gunicorn 2 workers × 4 threads. Миграции выполняются отдельно от workers.

## Приватная конфигурация и порядок запуска

Создать приватную копию `deploy/production.env.example` вне репозитория, с доступом только владельцу. Заменить все заглушки независимыми случайными секретами и точными доменами. В том же файле задать `APP_IMAGE`, `POSTGRES_IMAGE`, `CADDY_IMAGE` с проверенными immutable image references, `SITE_DOMAIN` и `DJANGO_TRUSTED_PROXY_CIDRS`. Пароль bootstrap роли PostgreSQL должен отличаться от пароля app роли. Не использовать реальные вузовские данные/доступы. Не печатать `docker compose config`, env, cookies или SQL dumps в терминал/CI/evidence.

Оператор явно задаёт путь (ни одна пользовательская `.env` автоматически не используется):

```sh
export COMPOSE_DISABLE_ENV_FILE=1
export DEANERY_CONFIG=/absolute/private/path/production.env
docker compose --env-file "$DEANERY_CONFIG" -f deploy/compose.production.yaml up -d db
docker compose --env-file "$DEANERY_CONFIG" -f deploy/compose.production.yaml ps db
# Дождаться healthy; затем выполнить однократно:
docker compose --env-file "$DEANERY_CONFIG" -f deploy/compose.production.yaml run --rm app python manage.py migrate --noinput
# Bootstrap запросит три вымышленных демопароля через getpass (не передавать в argv):
docker compose --env-file "$DEANERY_CONFIG" -f deploy/compose.production.yaml run --rm app python manage.py seed_demo
docker compose --env-file "$DEANERY_CONFIG" -f deploy/compose.production.yaml up -d app caddy
docker compose --env-file "$DEANERY_CONFIG" -f deploy/compose.production.yaml exec app python manage.py check --deploy
```

Не выполнять это на публичном сервере до приёмки следующих этапов. `up db` инициализирует app роль только на пустом собственном volume; повторный запуск не сбрасывает данные. Если старый volume не содержит app роли, остановиться и разработать отдельную проверяемую миграцию роли: нельзя переключать приложение на bootstrap superuser. App роль имеет LOGIN/NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOREPLICATION, владеет своей БД/схемой для миграций; PUBLIC не получает CREATE в public schema. Bootstrap secret передаётся только DB container, а не app/Caddy.

## Сети и доверие

Только Caddy публикует TCP80/443; app8000 и PostgreSQL5432 не имеют host ports. Backend internal объединяет app/DB; frontend internal — только app/Caddy; edge даёт Caddy исходящий доступ для будущего ACME. Контейнеры не монтируют исходники, env или SSH с хоста: конфиги входят в отдельные небольшие images, данные — в named volumes.

Выбрать свободную небольшую private subnet для frontend без пересечения с другими сетями Docker/хоста. Единственная переменная `DJANGO_TRUSTED_PROXY_CIDRS` задаёт и frontend subnet, и список доверия Django. CIDR `/0` запрещён. Для этого Compose используется один IPv4 CIDR; parser приложения поддерживает несколько точных IPv4/IPv6 CIDR для явно согласованных других контуров.

Caddy перезаписывает X-Forwarded-Proto и X-Real-IP своим реальным scheme/peer, удаляет клиентские Forwarded и X-Forwarded-For. Никакого CDN/upstream proxy перед Caddy сейчас нет; при добавлении требуется новый trust review. Axes читает один валидный X-Real-IP только при доверенном REMOTE_ADDR, иначе использует peer. REMOTE_ADDR глобально не меняется. `SECURE_PROXY_SSL_HEADER` безопасен лишь при сохранении сетевой изоляции и единственном peer Caddy. Loopback HTTP разрешён только двум точным health URL; приватные страницы HTTPS-only. Readiness проверяет настоящий SELECT1 в БД.

Caddy задаёт CSP self без inline/eval/CDN, security headers, body cap64KiB и таймауты. У него нет публичного admin API; access logging не включён. Операционные JSON события ограничены `tls.cache.maintenance`, `tls.obtain` (INFO+) и `http.log.error` (DEBUG+ только для этого logger): Caddy пишет успешно обработанные generic error handler ошибки на DEBUG даже при HTTP502. Поэтому алерт для upstream fault строить по `logger=http.log.error` и `status>=500`, а не только по уровню. Глобальный debug не включён. Stock filter удаляет динамические поля, JSON encoder с `message_key ""` не выводит потенциально приватный текст сообщения. Остаются только level/ts/logger/status/duration/err_id. Уровень и logger TLS сохраняют сигнал жизненного цикла/ошибки без подробного текста; это осознанное ограничение диагностики. Публичные ACME/renewal и мониторинг остаются D04. При обновлении Caddy/CertMagic повторить source audit ключей и реальный privacy smoke: filter не поддерживает wildcard allowlist. Приложение пишет только route/status/request-id/duration без query/body/cookies/traceback. HttpOnly включён у session cookie; CSRF cookie намеренно читается JS для ADR001, но Secure/SameSite=Lax сохраняются.

## Воспроизводимая собственная QA

```sh
PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers uv run python scripts/verify_production.py --docker docker
# Для локального Docker Desktop из WSL:
PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers uv run python scripts/verify_production.py --docker docker.exe
```

Runner явно передаёт Compose пустой env-file (`NUL` для native Windows CLI, `/dev/null` для Linux), исключая autoload пользовательской `.env` даже через WSL/Windows границу. Runner не принимает URL/DSN/существующий project/volume: он создаёт unique project с owner labels, строит 3 images из allowlist tar через stdin, генерирует секреты и не читает `.env`. Docker endpoint должен быть local unix/npipe. Production Compose преобразуется в JSON в памяти; QA overlay заменяет только environment собственными данными, image tags собственными сборками, resource names/labels, Caddy80/443 на loopback high ports и Caddy TLS на private internal CA. Production automatic TLS остаётся неизменным. CA не устанавливается в host trust store. Python SSL проверяет chain+hostname с явно скопированным публичным CA certificate; browser context ignore_https_errors разрешён только для этой private QA, не является проверкой публичного сертификата.

Runner проходит реальные TLS формы трёх ролей, operator POST, сохранение после restart, чужой UUID404, 360/1440 smoke, local manifest static, CSP/script errors, session cookies/CSRF, 2tab CSRF rotation, spoofed IP/Axes, HTTP XFP redirect, oversized413, DB stop503/recovery, runtime closure и deployment checks. Затем удаляет только проверенные owner-label ресурсы своего unique project и подтверждает отсутствие. Ошибка выводит только phase/type, без exception calllog. `--retain` оставляет ресурсы и приватный `/tmp/.../state.json` mode0600 для немедленного независимого review; это не результат cleanup, failure никогда не становится passed. Файл содержит QA credentials — не копировать в evidence и удалить вместе с собственными ресурсами после review. Не использовать broad prune.

## Аудит точных артефактов

Методика — [image-audit.md](image-audit.md). Production использует Python3.13.14/PG17.11 на trixie и Caddy2.11.9 на стабильном Alpine3.24. Runtime psycopg работает через системный Debian libpq5 (`PSYCOPG_IMPL=python`); binary extra остаётся только в dev group. Сохраняются package copyright/common licenses и dist-info notices. Поддержка pip не нужна production runtime, глобальный pip удалён.

APT/APK upgrades берутся из подписанных текущих stable/security repositories; это намеренно не обещает побитовую воспроизводимость будущей сетевой сборки по одному Dockerfile. APT timestamps/index SHA и фактический package closure сохраняются в image/inventory. PG server/client17 packages удерживаются на проверенном17.11; minor upgrade требует нового решения и аудита. После сборки аудит относится к точному immutable image ID/digest. Для развёртывания использовать проверенный артефакт, не пересобирать его незаметно из изменившегося репозитория пакетов. Наличие SBOM или успешное завершение scanner не закрывает остаточные CVE/лицензионные вопросы автоматически.

Локальный TLS runner добавляет `skip_install_trust` только в generated QA config: собственный CA извлекается в opener явно, поэтому установка CA в trust stores контейнера не нужна. Production Caddyfile и ACME этим не изменяются. Трансформация отклоняет неожиданный или неоднозначный global/site block; строгая JSON schema логов и проверки отсутствия приватных sentinel/password остаются обязательными. Источник опции: https://caddyserver.com/docs/caddyfile/options#skip-install-trust .
