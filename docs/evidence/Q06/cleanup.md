# Q06 — exact suite cleanup

2026-11-06, после сообщения root о независимом accepted Q06. Выполнен единственный разрешённый cleanup retained suite из `suite-resource.json`.

Перед удалением `docker inspect` подтвердил:

- Name: `deanery-q05-25856a9ba05e412785c6087aa48a3bc2`.
- Label: `deanery.q05.owner=25856a9ba05e412785c6087aa48a3bc2`.
- Image: `postgres:17.11-bookworm@sha256:839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5`, совпадает с `deploy/compose.local.yaml`.
- Binding: `127.0.0.1:55432` → `5432/tcp`.
- Единственный attached volume: `f4e6b14364a98f6fa3d3a071be6d259309964d93095efa3c648e41428d321325`, destination `/var/lib/postgresql/data`, type volume.

Команда `docker rm --force --volumes deanery-q05-25856a9ba05e412785c6087aa48a3bc2` через штатную escalation завершилась exit0 и вернула точное имя.

Последующие отдельные проверки:

- `docker container inspect deanery-q05-25856a9ba05e412785c6087aa48a3bc2` — exit1, `No such container`.
- `docker volume inspect f4e6b14364a98f6fa3d3a071be6d259309964d93095efa3c648e41428d321325` — exit1, `no such volume`.

Exact container и volume отсутствуют. Prune не выполнялся; пять ранее удалённых volumes повторно не удалялись; dev ресурсы, `.env` и SSH не затрагивались. `suite-resource.json` остаётся исторической записью ранее retained ресурса и больше не обозначает доступную suite среду. Commit/push не выполнялись; writer freeze.
