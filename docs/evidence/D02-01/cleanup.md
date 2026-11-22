# D02-01 — завершение cleanup 2026-11-08

Удалены только оставшиеся собственные ресурсы host regression suite. Docker Desktop Linux engine был выключен; выполнен штатный `docker desktop start`. Использован native Windows Docker CLI. Compose не вызывался; пользовательские env/config/секреты не читались.

До удаления выполнены точные `container inspect` и `volume inspect` с ограниченным format:

- container name: `deanery-d02-suite-68769032e02b4fd78756efa47ebe0e65`;
- container ID: `d88e277f2f700153c733ef0fed7e5fecd4392cd5fc744594e5db791b66b059bb`;
- image: `postgres:17.11-bookworm@sha256:665dc7b37ac52a17e298511414c21d23ffa4e6a6ef6225b3e5d59c7afb35e994`;
- owner label контейнера и volume `deanery.d02.owner=68769032e02b4fd78756efa47ebe0e65`;
- единственная публикация: `127.0.0.1:55432` → `5432/tcp`;
- volume: `deanery-d02-suite-68769032e02b4fd78756efa47ebe0e65-data`, driver local, mount `/var/lib/postgresql/data`.

После совпадения identity/owner/image/port/mount выполнены `container rm -f` по полному ID, затем `volume rm` по точному имени. Повторный exact inspect обоих ресурсов вернул соответственно `No such container` и `no such volume`; отсутствие подтверждено, ошибки daemon не принимались за отсутствие.

Никакие prune/broad cleanup не выполнялись. Production default QA уже был очищен ранее и повторно не затрагивался. Пользовательские dev порты5432/8000, чужие контейнеры/volumes/networks/images не менялись.
