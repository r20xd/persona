# K01 — реализация исполнителем

Модель/усилие заданы основным агентом: gpt-6.1-sol/low, отдельный контекст, один writer, без субагентов. Задание: [prompt.md](prompt.md); согласованный контракт: [attention-and-digest.md](../../ux/attention-and-digest.md). Этап развивает CORE-02–CORE-05, PRD-01–PRD-05, TECH-06 и сохраняет SEC-01.

## Результат

На главной добавлены «Требует внимания» и «Пока вас не было». Радар собирает подтверждённые отрицательные итоги выбранного периода, сроки ±7 дней без опубликованного результата, актуальные изменения занятий и ready/rejected личные заявки. До шести карточек, детерминированный порядок, честный общий счётчик и ссылки на разделы. У сроков без связанной работы нейтральная формулировка; отсутствие оценки не объявляется задолженностью. Изменения содержат реальные старые/новые значения и причину; ссылки обозначают действие.

DigestState и DigestReceipt добавлены собственной additive миграцией dashboard/0001. Первый обычный student login начинает отслеживание; отсутствие профиля сохраняет прежний поток входа и штатную ошибку главной. Первый GET без обычного login не пишет и предлагает POST начала отслеживания. Выборки ограничены актуальными собственными enrollment/group/request источниками; будущие и исторические до начала события исключены. До трёх деталей на категорию и счётчик всей категории. Пустые категории не занимают отдельные секции.

Подписанный Django token живёт 30 минут, связан с user/state и содержит только показанные identities/event timestamps (до девяти). POST требует CSRF и fresh active student/profile, повторно проверяет текущий доступ и точную версию, пишет идемпотентные receipts в транзакции. Новая публикация оценки, поздний commit, две вкладки и повтор старого token не списывают другое событие. Начало не сдвигается. Уведомления и актуальный радар независимы от receipts. Успех — PRG; обработанные 400/403 и успешные ответы — no-store.

## Проверки

Среда: существующая .venv, PostgreSQL 17.11 в отдельном loopback Docker service с owner label. Без dev DB/.env/production сервиса. Credentials хранятся только в private temporary state; в репозиторий и evidence не включены. Первая попытка pytest без escalation завершилась ошибкой подключения; её стандартный подробный traceback вывел временный пароль изолированной QA DB в tool output. Основной агент уведомлён; последующие pytest используют --tb=short. После независимой проверки основной агент должен удалить собственный QA container/volume через owner-checked helper.

Команды с TEST_DB_* из private runner /tmp/k01-run.py, рабочая тестовая БД test_deanery_k01_worker:

- `pytest tests/test_attention.py tests/test_attention_browser.py tests/test_dashboard_demo.py -q --reuse-db --tb=short` — **25 passed**, один upstream pytest fixture deprecation warning. Проверены baseline/history/publication boundaries, user binding, fresh access, CSRF, неверная/просроченная/слишком большая подпись, stale grade publication, limit3/остаток, новое событие после GET, late commit, concurrent tabs/idempotence, group revocation, request operator transitions, независимость радара, приоритет/limit6/total, отменённые/дальние/прошлые сроки и текущая версия отмены/восстановления занятия.
- Additive migration: после seed удалена только новая dashboard schema через MigrationExecutor; снимки всех полей User/ServiceRequest/RequestEvent/GradeResult/LessonChange сравнены до/после применения dashboard/0001. Существующие записи полностью сохранены, новые state/receipt таблицы пусты.
- Started digest GET: **49 запросов до и после** добавления восьми заявок и переходов. Новый тест ограничивает рост и верхний предел55. Существующий force_login budget `<45` оставлен без изменений и прошёл.
- `ruff check` и `ruff format --check` для всех затронутых Python-файлов — успешно.
- `manage.py makemigrations --check --dry-run --settings=config.settings.test` — **No changes detected**, подключение к QA PostgreSQL разрешённым escalation.
- `git diff --check` — успешно.

Реальный Chromium 360/1440 проходит обычный login, новую публикацию отрицательного итога, service-driven отмену занятия, новую заявку и переход оператора, refresh, mark shown, повторный вход и сохранение просмотренности. Проверяются keyboard focus и отсутствие горизонтального переполнения. Новые изображения: attention-digest-360.png, attention-digest-1440.png и viewport варианты в этой папке; исторические screenshots не изменяются. Финальная пересъёмка после сокращения пустого состояния и проверки 403 no-store выполняется отдельным узким browser прогоном; его результат ниже.

Полный suite исполнитель не запускал: после code freeze независимый прогон выполняет основной агент. Физический телефон, публичный хостинг, доставка из России, deployment и конкурсная сдача в K01 не проверялись. Новых зависимостей, CDN, JS, внешнего ИИ, универсального event bus и публикации нет. Commit/push до принятия не выполнялись.

Финальный узкий прогон на замороженном коде: `UPDATE_EVIDENCE=1 pytest tests/test_attention_browser.py tests/test_attention.py::test_invalid_tokens_roles_csrf -q --reuse-db --tb=short` — **3 passed**, тот же upstream warning. Оба fullpage и оба viewport PNG обновлены в K01; 403 no-store проверен. Worker прекратил изменение кода после freeze.

## UI исправления после независимого suite

После root full suite (392 passed, input hashes unchanged; [regression-independent.json](regression-independent.json)) по отдельному разрешению изменены только digest template и снятие фокуса перед screenshot в browser test. Вводный текст упрощён; сообщение об оставшихся событиях показывается только при count > число показанных; у отмены показан один временной слот и реально изменённые поля/статус, а у переноса сохранено старое → новое. Keyboard assertion сохранён, перед снимком focus снят.

`UPDATE_EVIDENCE=1 pytest tests/test_attention_browser.py -q --reuse-db --tb=short` — **2 passed**, один прежний upstream warning, 14.43s. Четыре PNG пересняты. Ruff check, format --check (13 файлов) и git diff --check прошли. Новый freeze; модели, сервисы, зависимости и прочий код после независимого suite не изменялись. Полный suite повторно не запускался; QA DB оставлена для root проверок.

## Независимая приёмка и завершение QA

Основной агент сообщил результаты независимых проверок: полный suite **392 passed**, один upstream warning, 245.15s, input hashes unchanged; после разрешённых UI правок — **2 browser passed**, 13.71s. Django check, ruff all, format --check (13 файлов), diff check прошли. Повторная проверка makemigrations на живой base QA DB дала **No changes detected** без warning; предыдущая попытка root на уже удалённой отдельной test DB сохранена как неуспешная проверка соединения, не скрыта. JSON доказательства принадлежат основному агенту в этой папке.

По отдельному поручению основного агента выполнена owner-checked очистка QA. Helper завершился exit0, повторный listing подтвердил отсутствие контейнеров, volumes, networks проекта и private state directory; [cleanup.md](cleanup.md). QA среда больше не retained. После freeze изменялись только эти документы о результатах; Git операции ещё не выполнялись.
