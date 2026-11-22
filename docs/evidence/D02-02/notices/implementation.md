# D02-02-N — runtime notices collector

Требование LIC-01, отдельная узкая область записи. Инструменты: Codex `gpt-6.1-sol / low`, Python stdlib, pytest/Ruff из существующего окружения, официальные публичные Go proxy/sumdb, Go repository tags, GNU canonical GPL. Docker не использовался; исходный код зависимостей не выполнялся и не сохранялся в Git. Архивы обрабатываются в памяти, не извлекаются целиком.

Вход: AFTER `caddy.json` и `db.json` из `docs/evidence/D02-02/after/`. SHA256 обоих входов в bundle manifest. Collector читает только `gobinary` inventories; запись root `caddy` без версии заменена присутствующей module-записью `github.com/caddyserver/caddy/v2 v2.11.9`. Go stdlib: Caddy v1.27.3, gosu v1.24.6. Одинаковые module@version сохраняются один раз; разные версии x/sys остаются отдельными.

Модули получают полный zip через proxy.golang.org. Ожидаемый h1 получен отдельно через HTTPS sum.golang.org lookup; h1 вычислен стандартным Go dirhash по всем файлам ZIP. Сохранены expected h1, URL checksum response, SHA256 response, SHA256 archive и каждого неизменённого текста. Collector не реализует отдельную криптографическую проверку signed transparency checkpoint sumdb: доверие к lookup в этом проходе опирается на HTTPS официального сервиса. SHA скачанного ZIP не выдается за upstream identity proof.

Из ZIP выбираются только LICENSE/LICENCE/COPYING/NOTICE/COPYRIGHT/PATENTS/AUTHORS и варианты с расширением/суффиксом, включая вложенные third-party notices. Проверяются traversal, дубликаты, symlinks, ограничения числа/размера файлов, decompressed-size/notice-size. Выходные каталоги — детерминированный SHA256-префикс module@version. Тексты не редактируются. Версии/URL поступают только из публичных package identities, не из credentials/пользовательских URL. Не читаются .env, ключи или конфигурация сервисов.

Go stdlib LICENSE/PATENTS получены по точным официальным release tags `go1.27.3` и `go1.24.6`; они явно помечены `exact-upstream-tag`, а не module h1. GPL-3.0.txt получен без изменений с canonical https://www.gnu.org/licenses/gpl-3.0.txt для combined LGPLv3 Psycopg notices. Эти SHA256 являются локальными integrity hashes текстов; provenance — указанные точные upstream URLs.

Первый реальный проход: 152 identities; 149 h1-verified modules, 2 stdlib tag records, 1 unresolved gosu v1.19.0 (sumdb 404). 208 текстов module/stdlib плюс GPL. Это не закрытие LIC-01: root отдельно читает оригиналы и оценивает условия, native/OS/Python inventories вне этого collector. Отсутствие license metadata Trivy не заменено автоматическим юридическим выводом.

Проверки: `python -m pytest tests/test_image_notices.py -q` — 7 passed; `python -m ruff check scripts/collect_image_notices.py tests/test_image_notices.py` — passed. Тесты проверяют mismatch h1, traversal, symlink, duplicate archive members, archive-size limit, escaping/collision разных версий. Полный application suite не запускался: приложение/зависимости/схема не изменены.

Для повторной проверки используйте JSON из [финального прогона](../final-verified/). Сеть нужна для публичных источников лицензий.

```sh
.venv/bin/python scripts/collect_image_notices.py \
  docs/evidence/D02-02/final-verified/caddy.json \
  docs/evidence/D02-02/final-verified/db.json
```

Exit 1 означает unresolved/missing-notice; не выдавать его за успешное покрытие. Содержимое текстов byte-exact; подробности и все hashes — `docs/third-party/runtime-notices/manifest.json`. Commit/push не выполнялись.

## Одобренный gosu fallback

Root разрешил конкретное соответствие `github.com/tianon/gosu v1.19.0` из Trivy → официальный upstream tag `1.19`. `git ls-remote https://github.com/tianon/gosu.git refs/tags/1.19` вернул `6456aaa0f3c854d199d0f037f068eb97515b7513`. Источники текста — raw HTTPS URLs, закреплённые этим commit. Collector имеет исключение только для этой пары module/version; другие версии не используют fallback. LICENSE сохраняется byte-exact, необязательный NOTICE фиксируется как отсутствующий при HTTP 404. Полный репозиторий/архив gosu не клонируется и не поставляется.

Manifest явно хранит `verification=official_tag_to_commit_https`, normalized version mapping, commit/tag/source, `expected_h1=null`, `h1_status` с исходным sumdb HTTP 404. SHA256 текста не выдается за h1 или независимую проверку signed checkpoint. Provenance в этом исключении — точный официальный upstream commit по HTTPS, как разрешил root.

После изменения collector: 8 passed, Ruff passed. Восьмой тест запрещает сетевой доступ для неразрешённой gosu fallback identity. Bundle format для image COPY: весь каталог `docs/third-party/runtime-notices/` содержит `manifest.json`, `GPL-3.0.txt` и каталоги `<sha256(module@version)[:24]>/<original-relative-notice-path>`. Исходников/архивов/executables в bundle нет. Dockerfile/context COPY выполняет другой исполнитель после root review.

Повторный проход с gosu fallback: все 152 Go identities собраны — 149 h1-verified modules, 2 Go stdlib tags, 1 gosu exact commit; 209 module/stdlib/gosu текстов. У gosu сохранён LICENSE (11358 bytes, SHA256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`); NOTICE по тому же commit отвечает 404. Все 209 файлов независимо сверены с manifest SHA256 локальным проходом. Повторная загрузка GNU дала временный URLError; предыдущий успешно загруженный canonical GPL текст сохранён без изменений, его SHA256 `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`, 35149 bytes. Это сбой повторной сетевой проверки, а не отсутствие исходного текста.

Отдельный GNU retry также завершился connection timeout. Финальный manifest сохраняет проверенные metadata первого успешного canonical fetch и `collection_history` с обоими последующими сетевыми сбоями. Файл заново не создавался из пересказа или альтернативного источника: его сохранённые bytes независимо совпали с SHA256 первого fetch. Итого final bundle: 152 Go identities, 209 Go notice files + 1 canonical GPL file. Fresh reproduction сейчас может завершиться exit 1 из-за доступности GNU; это явно записанный operational limit, не отсутствие текста. Writer freeze после этого результата; фоновых процессов нет.

## Root review correction: notice selection v2

После независимого root review исправлен слишком широкий filename pattern: `testdata` paths исключаются из выбираемых notices, но все файлы архива по-прежнему входят в h1. Это удалило два fixture-файла: `dario.cat/mergo testdata/license.json` и `grpc-gateway protoc-gen-openapiv3/internal/genopenapi/testdata/license_missing_name.prototext`. По точному разрешению root исключены также `nebula dist/windows/wintun/LICENSE.txt` (Windows-only driver) и `quic-go assets/LICENSE.md` (непоставляемые logo/trademark assets). Корневые MIT LICENSE этих modules сохранены.

Collector применяет эту же политику при новом сборе. Текущий bundle исправлен детерминированным pruning: 152 архива не скачивались заново, expected h1/archive SHA256 и retained file bytes/hashes сохранены. Исключённые source paths, прежние SHA256, sizes и reasons сохранены в `manifest.excluded_notices` и соответствующих component records; history содержит SHA256 прежнего manifest. Ни fixture data, ни Windows/logo asset notices в bundle больше нет.

Проверки после изменения: 9 passed (прежние 8 + риск-тест exclusion/h1/root/nested licenses); Ruff passed. Все 205 оставшихся Go notice hashes и GPL hash сверены; итого 206 текстов. GNU network повторно не использовался: исходный успешный canonical provenance и последующие timeout history сохранены. Root дополнительно сравнил GPL byte-exact с trusted host `/usr/share/common-licenses/GPL-3`. Writer freeze; commit/push отсутствуют.
