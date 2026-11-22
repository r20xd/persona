# Q04/U03 — промежуточное ревью

Статус: **changes requested**, до окончательной проверки движков и независимого regression. Проверены первая версия CSS/forms.js, templates и tests/test_ui_accessibility_browser.py. Предыдущие source замечания — audit-notes.md; согласованный QA fallback — prompt.md.

| № | Наблюдение | Почему важно | Ожидаемое подтверждение |
| --- | --- | --- | --- |
| 1 | Native POST form с унаследованным #main зависает в WebKit remote | Нельзя скрывать несовместимый путь удалением fragment из теста | Изолировать POST/ответ/DOM. Если зависимость от fragment подтверждается, явные canonical action login/request-new при сохранении hidden next/CSRF; реальный skip→ошибка на WebKit |
| 2 | Empty test использует seed student.two с готовой заявкой и проверяет только overflow | Название теста не доказывает честное пустое состояние | Настоящее отсутствие собственных данных, явное объяснение/действие, без вымышленных результатов |
| 3 | detail terminal/stale branch остаётся без новой summary/focus | При409 после начала обработки пользователь не получает общего error focus | Summary также в этом состоянии; без дублирующих summary и якорей на отсутствующие поля, реальная устаревшая отмена/переход |
| 4 | Только scrollWidth проверяется для mobile submit | Кнопка может оставаться под fixed nav при отсутствии overflow | После keyboard/scroll кнопку можно активировать, bounding/hit-test при360/reflow |
| 5 | Reduced motion тест подтверждает лишь matchMedia | Это проверка эмуляции, а не поведения приложения | Computed scrollBehavior=auto при reduce |
| 6 | Input проверяется точным RGB | Это привязывает тест к CSS декларации вместо критерия читаемости | Вычисленный contrast текста/фона>=4.5, активный cursor подходит вводу |
| 7 | Удалён общий refresh link из detail.html; active branch новая summary его не включает | После stale409 у оператора с актуальным in_progress форма остаётся со старым expected_version; повтор даёт409 снова | В summary при detail_url восстановить GET ссылку на актуальную карточку, версию не подменять автоматически. Browser active-stale→focus→freshGET/version; сохранить существующий test_csrf_validation_preserves_text_and_stale_response |

Дополнение network: разрешён route.fetch→abort после фактического commit в QA. Проверить наличие сохранённой заявки в собственном списке и повтор того же submission_key/body с настоящим CSRF без второй записи. Это отдельный сценарий от abort до отправки. Приложение сохраняет native submit; новый fetch/SPA не вводится. Короткая ссылка «Мои заявки» даёт путь восстановления без ложного сообщения об успехе.

Основная палитра/серверные services/schema/auth не меняются. После этих замечаний объём фиксируется: завершить targeted движки, новые screenshots и полный regression, передать writer freeze. Новых UI функций до этого не добавлять. Оценку реального телефона, browser OS zoom и настоящего Safari не подменять desktop Playwright emulation.

## Разбор WebKit и QA окружения

Основной агент независимо проверил WebKit через тот же loopback Playwright server на собственном временном ThreadingHTTPServer: два native fragment POST случая (main focusable false/true) прошли, в обоих реальные методы GET→POST. Handler/server/browser закрыты после проверки, файлы/PG не использовались. Это не доказательство поведения приложения, а изоляция причины.

Исполнитель сравнил sync1 Gunicorn и новый QA helper с threads4: на sync1 route.fetch/native WebKit navigation блокировались, на threads4 loss-after-commit и hash→invalid login прошли с реальным POST200. Родитель принял helper в разрешённой tests области; это исправление QA head-of-line starvation, а не серверного CSRF/HTML дефекта. Canonical form action и focusable main остаются семантическими улучшениями; им не приписывается устранение starvation.

Независимый inspect основного агента подтвердил у `deanery-q04-browser-20261106`: label `deanery.qa=Q04-U03-browser-20261106`, user pwuser, private IPC, privileged=false, CapAdd=null, Mounts=[], только127.0.0.1:53000→3000. Python/app остаются в host QA; контейнер не содержит пользовательских project mounts.

Дополнительно исполнитель подтвердил мобильный submit под fixed nav при focus/scroll. Исправление scroll-padding/margin следует проверить фактическим hit-test при360 и reflow, а не лишь отсутствием горизонтального overflow. Итоговая независимая приёмка ещё не выполнена.
