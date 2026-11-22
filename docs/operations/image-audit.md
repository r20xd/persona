# Локальный аудит production images

D02-02, SEC-02/LIC-01/TECH-03/04/06. Аудит не публикует образы и не обращается к системам вуза. Временные image archives и cache остаются в собственном `/tmp`, scanner не получает Docker socket, bind mounts, проект или домашний каталог.

Используется официальный [Trivy 0.76.2](https://github.com/aquasecurity/trivy/releases/tag/v0.76.2). Перед распаковкой `trivy_0.76.2_Linux-64bit.tar.gz` проверить SHA256 по официальному `trivy_0.76.2_checksums.txt`: `bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf`. SHA256 извлечённого Linux amd64 binary: `6a972c69606c7b3ea4c6bdcc6fc9332ea9ad38381624310c1e85cc77345909f3`; helper отказывается запускать другой binary. Каталог scanner/cache не добавлять в Git.

Базу загрузить отдельно, затем сканировать offline:

```sh
/tmp/deanery-trivy/trivy image --cache-dir /tmp/deanery-trivy-cache \
  --db-repository ghcr.io/aquasecurity/trivy-db:2 --download-db-only \
  --no-progress --skip-version-check
.venv/bin/python -m scripts.verify_image_audit \
  --docker /mnt/c/Users/local-user/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe \
  --scanner /tmp/deanery-trivy/trivy --cache /tmp/deanery-trivy-cache \
  --output docs/evidence/D02-02/independent
```

Для Linux Docker заменить `--docker` на его локальный executable. Helper отклоняет remote endpoints, создаёт только уникальные собственные labeled images/контейнеры, проверяет ownership перед удалением и подтверждает отсутствие после удаления. Он не читает `.env`/SSH, не использует Compose для audit и не запускает чужой image. Сборка использует allowlist контекста, production Caddyfile без QA TLS подмены. Контейнеры инвентаризации работают без сети, mounts и capabilities с read-only rootfs.

`summary.json` фиксирует точные image IDs, хеши exported archives, report/SBOM/runtime inventory, build inputs, scanner binary, schema/time/hash DB. `*.json` содержит полный Trivy report, `*.cdx.json` — CycloneDX, `*-runtime.json` — фактические notices/native library hashes и Python closure. Archives/cache/raw runtime logs в evidence не сохраняются. Сканирование явно отключает implicit `trivy.yaml` и `.trivyignore`, выполняется `vuln,license`, без severity/unfixed suppression. Findings не выдают за сбой scanner; `completed-with-findings` означает успешное измерение с замечаниями, а не безопасность образа. `failed` и ненулевой exit означают неполную проверку/cleanup; нельзя трактовать это как отсутствие CVE.

Сводка baseline D02-01 находится в `docs/evidence/D02-02/baseline/summary.json`. Финальный и независимый отчёты доступны в каталоге D02-02. Последующие наборы связываются с точными Dockerfiles/lock. При повторной проверке используйте новый каталог output.

Trivy распознаёт OS/Python/Go package metadata и известные уязвимости своей базы; он не гарантирует обнаружение каждой bundled native library. Отдельная runtime инвентаризация выявила 15 библиотек `psycopg_binary.libs` baseline, которые не имеют самостоятельного coverage в OS package scan. Python `ssl.OPENSSL_VERSION` относится к Python-linked SSL, не к вложенному SSL wheel. `libpq_version` — фактически выбранная библиотека psycopg. `argon2_version` — версия алгоритма, не доказательство версии vendored libargon2. Wrapper version и notice hash проверяются отдельно.

Scanner license labels не являются юридическим заключением. Notices сохраняются в исходных пакетах; полнота текстов для Go/native closure требует отдельного реестра и ревью. UNKNOWN и остаточные CVE требуют явной оценки по первичным upstream/distribution advisories, включая статус false-positive или ограниченную применимость. Доступность из РФ, публичный TLS/ACME, эксплуатация до итогов и конкурсная готовность этим аудитом не проверяются.
