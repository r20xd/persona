# ADR003 — системная libpq и проверяемый состав серверных образов

Статус: решение для D02-02; фактическая приёмка и результаты — в `docs/evidence/D02-02/`. Оно не означает публикацию сайта или отсутствие всех известных уязвимостей.

## Причина

В исходном app image `psycopg-binary3.3.8` поставлял15 отдельных `.so` с libpq/OpenSSL/Kerberos/LDAP/SASL и другими библиотеками. Python package metadata содержала только лицензию wrapper; обновления системных пакетов не обновляют эти копии. Исходный Caddy image также не содержал необходимых исходных notices Go-компонентов. Аудит базовых образов обнаружил известные CVE вне Python lock.

## Решение

- В production используется `psycopg3.3.8` с `PSYCOPG_IMPL=python` и системной Debian `libpq5=17.11-0+deb13u1`. В dev group остаётся `psycopg[binary]` для обычного запуска в WSL. Изменены только dependency edges/groups; версии всех пакетов lock сохранены. Это разные способы загрузки одного драйвера, без смены Django/PostgreSQL/API. Совместимость production проверяется настоящим TLS путём и миграциями, а не только host tests с binary implementation.
- Python3.13.14 и PostgreSQL17.11 остаются выбранными версиями; production base images переходят на Debian13/trixie по проверенным immutable digests. Caddy обновляется до официального2.11.9-alpine. Образы локальной разработки не изменяются этим решением.
- Stable подписанные Debian/Alpine repositories используются для доступных security updates; sid/edge/testing/неподписанные репозитории не добавляются. PostgreSQL server/client17 закреплены на проверенном minor. В образе сохраняются время обновления, fingerprints package indexes/installed package database и полный package inventory. Неиспользуемые global pip и ensurepip wheels удаляются из конечного app image, app venv не затрагивается.
- APT/APK repositories изменяемы, поэтому закрепление base digest не делает повторную сборку побитно одинаковой. Объект проверки — конкретный собранный image ID/digest и его SBOM. Каждый новый rebuild требует нового аудита; будущий релиз должен развёртывать проверенный immutable artifact, не пересобирать плавающую среду при старте.
- Оригинальные OS copyright/common-license и Python dist-info файлы сохраняются. Добавлен общий source-verified bundle Go LICENSE/NOTICE/PATENTS/AUTHORS и GPLv3 для LGPLv3 notices. Это набор сопроводительных текстов, не перечень исполняемых пакетов каждого image и не лицензия собственного приложения. В bundle нет исходников/бинарников/логотипов зависимостей. Manifest хранит module/version, provenance, file hashes и исключения неприменимых fixtures/assets.

## Диагностика и остаточные риски

Caddy остаётся официальным бинарным release; не создаём fork с произвольными dependency overrides ради нулевого отчёта. Scanner findings сохраняются без ignore-фильтров. Известные остатки оцениваются по первичным advisories и текущим включённым функциям, с повторным review при изменении контура. Контекстная оценка не означает, что зависимость глобально исправлена.

Вместо полного подавления operational logs используются только named logger scopes TLS maintenance/issuance и HTTP faults. JSON free-text message отключён; поля с request/headers/URI/IP/error/trace удаляются по исходникам закреплённых Caddy/certmagic. Из-за stock Caddy handled faults отдельный HTTP logger имеет DEBUG, без глобального debug; сигнал отказа — status502, а не предполагаемый ERROR level. Access log не включается. Проверка формы JSON и уникальных sentinels выполняется на реальном Caddy; при смене версии/source fields требуется повторный аудит.

Trivy используется локально по проверенному checksum, со скачанной публичной базой и offline scan собственных image archives. Docker socket/host home не монтируются, images/исходники/секреты не отправляются в облачный scanner. Неидентифицированные vendored native компоненты и function reachability не покрываются обещанием scanner: file hashes и upstream package/source identity учитываются отдельно.

Основания: [Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html), [Trivy image scanning](https://trivy.dev/docs/latest/target/container_image/), [официальный Caddy release2.11.9](https://github.com/caddyserver/caddy/releases/tag/v2.11.9). Точные pins, состав, исходные находки и повторные проверки сохраняются как факты реализации, а не как требования конкурса.
