# Q06: локальная производительность и зависимости

Требования TECH-03/04/06, PRD-02/05, SEC-01/02. Это репетиция localhost, а не проверка опубликованного сайта или гарантия вместимости VPS.

Из корня locked Python окружения:

```sh
.venv/bin/python -m scripts.verify_performance --docker /path/to/local/docker
```

Runner не принимает URL, DSN или существующее имя ресурса. Он проверяет локальный Docker endpoint, создаёт уникальный container с ownership label, pinned PostgreSQL17.11 из compose.local, динамический loopback порт, временную static directory. PGDATA размещён в explicit tmpfs, чтобы image VOLUME не оставлял anonymous volumes. Это warm-read smoke, не VPS disk benchmark. Нет host mounts или named volume; trust разрешён только этой disposable QA БД. При timeout после create cleanup всё равно проверяет ownership и отсутствие ресурса. В finally завершается собственный web и удаляется собственный container. JSON с cleanup_complete=false требует разбирательства; такой запуск не успешен. User .env/dev не читаются. Ошибки выводятся классом и местом, без сообщений, cookies, credentials, SQL или HTML.

Веб: DEBUG=False, Gunicorn23.0.0,2 workers×4threads, WhiteNoise, серверные DB sessions, штатные Argon2 и CONN_MAX_AGE=0. Двадцать отдельных CookieJar получают уникальные серверные сессии через настоящий CSRF login; два вымышленных аккаунта чередуются. Login выполняется последовательно из-за памяти Argon2, измеряется отдельно, включая redirect/render. Чтение проверяет200, точный конечный URL и признак раздела, отклоняет login form. До/после проверяется собственный профиль без чужого имени и404 чужой заявки во всех20сессиях; персональные значения остаются только в памяти.

После120отдельных прогревочных GET идут3раунда×6маршрутов×20readers: barrier перед каждым маршрутом и ThreadPool20. Это360измеренных запросов,60на маршрут. Время включает сеть localhost, очередь, полный ответ и проверку body. p50/p95 — nearest rank ceil(n*p), max сохраняется. Любая функциональная ошибка/неподтверждённый dataset/cleanup failure даёт ненулевой exit. Внутренний ориентир read p95<1s отражается отдельно target_met; превышение само по себе не подменяется функциональной ошибкой. Zero counters относятся только к полностью успешному прогону; при прерывании полного performance результата нет.

Query audit выполняет настоящие server-rendered GET через Django Client, DEBUG=False, execute_wrapper; response.content материализован. Логируются только количество и время запросов, SQL/params не сохраняются. Initial dataset расширяется40курсами/записями/оценками/уроками и40заявками/уведомлениями/объявлениями. Итоговые counts/sizes — в performance.json. Это диагностический fixture, создаваемый ORM только в disposable QA БД, не пользовательский сценарий отправки40заявок.

В initial/expanded число запросов одинаково: dashboard26, schedule7, grades8, session9, requests6, notifications16, operator queue5. N+1 в этой матрице не выявлен. Заявки/уведомления/объявления ограничены paginator20, dashboard slices3/2; у расписания ограничение периода день/неделя и enrollment, у оценок/сессии — выбранный семестр и enrollment. Последние наборы не имеют численного cap: очень большие учебные наборы могут увеличить память/HTML без роста query count. Dashboard/notifications имеют заметную фиксированную цену повторных ownership/role/count queries; сейчас app fix не нужен, при росте нагрузки это кандидаты для отдельного профилирования без ослабления авторизации. Миграции/индексы не менялись.

## Dependency audit

```sh
UV_CACHE_DIR=/tmp/deanery-uv-cache uv export --frozen --no-dev --no-hashes --no-emit-project -o /tmp/q06-runtime.txt
UV_CACHE_DIR=/tmp/deanery-uv-cache uv export --frozen --all-groups --no-hashes --no-emit-project -o /tmp/q06-dev.txt
UV_CACHE_DIR=/tmp/deanery-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/deanery-python uvx --python .venv/bin/python pip-audit==2.10.1 --no-deps --disable-pip --progress-spinner off --format json -r /tmp/q06-runtime.txt
UV_CACHE_DIR=/tmp/deanery-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/deanery-python uvx --python .venv/bin/python pip-audit==2.10.1 --no-deps --disable-pip --progress-spinner off --format json -r /tmp/q06-dev.txt
```

Использован официальный PyPA pip-audit2.10.1, отдельное uvx окружение, source PyPI JSON advisory API (default pypi service). Передаются только публичные package/version. Экспорт уже включает полную lock closure, поэтому --no-deps не скрывает транзитивные зависимости, включая psycopg-binary. Проверка Linux/Python3.13: Windows-only tzdata/colorama исключены markers; это не аудит всех платформ lock. Dev scope включает runtime+dev closure. Аудит актуальной базы ограничен известными опубликованными advisories на момент запроса; отсутствие findings не доказывает отсутствие неизвестных уязвимостей. Network/tool failure отличается от completed/no findings.

Фактические агрегаты и дата запроса: docs/evidence/Q06/performance.json, audit-runtime.json, audit-dev.json и implementation.md. Лицензии проверяются отдельно основным агентом.
