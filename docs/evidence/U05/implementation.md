# U05 — реализация визуального редизайна

Принятый baseline и фаза A: audit.md, audit-summary.json, before-taste-*/report.json, before/. Направление root: design-direction.md. Работа выполнялась одним исполнителем без субагентов; приложение оставалось Django Templates, без новых dependencies, fonts/CDN, внешних изображений или изменений backend/schema/URLs.

## Что изменено

- Actual app отделён от legacy preview.css в новый читаемый workspace.css. Общие brand/icon/header/navigation partials, единая ширина1120/gutters, desktop sidebar232px, шапка80px; operator получает собственные разрешённые разделы. Header не делает дополнительных SQL-запросов. На /login/ shell не показывается даже для authenticated user: поведение LoginView не менялось.
- Навигация — собственные SVG из campus.svg, единое семейство primary/secondary/quiet buttons44–48px, системная типографика body16, metadata≥11. Focus на тёмных surfaces светлый; scroll-behavior:auto, reduced-motion сохраняется. Одна общая compact concept notice стала спокойной строкой без отдельной рамки.
- Главная: ближайшее реальное событие перемещено перед radar/digest и целиком помещается в первом экране360. Контрастная navy панель с датой/временем, дисциплиной, местом, преподавателем и настоящим переходом. Radar компактнее; digest сохраняет все отрисованные identities и явную POST ack-кнопку без закрытого accordion. Read-only повторный блок изменений размещён в details; источники/полные действия в расписании доступны. Вторичные сведения сгруппированы в поддерживающие summaries, без выдуманных графиков/прогнозов.
- Расписание/сессия: общие tabs и filter toolbar, time/place hierarchy и строки занятий, заметные изменения/отмены, исходная история в details. Grades: summary strip, course/work rows и опубликованные итоги с прежним смыслом0/ожидания/зачётов. Requests/operator: единые фильтры, статусы, формы и timeline истории; полный UUID доступен в list disclosure и на карточке, secondary metadata не доминирует. Notifications: различимые sections и unread accent, реальные read/open действия сохранены. Profile: identity panel/dl и группа рабочих ссылок.
- Login: конкретный заголовок о кабинете, три настоящие возможности с собственными SVG, компактная форма. На desktop заполнена композиция, на mobile форма/action помещаются в первый экран. Повторный login-panel-note удалён по review; общая отметка концепта и инструкции о demo credentials сохраняются.
- Палитра U04 и цвета errors/warnings сохранены. Пользовательский colors.jpg не менялся и не используется как asset. Preview остаётся архивным U04 интерфейсом с честными ограничениями.

## Фактические проверки перед freeze

Собственный pinned PostgreSQL17.11 и собственные temporary browser DB/static roots. Playwright Chromium156/v1248, Python3.13.14/Django5.2.19 из lock. Все live проверки использовали fictional accounts; пользовательские dev5432/8000 и настоящие данные не использовались.

1. Первый targeted run design+U04+K01+Q04:20passed/1failed. U04 test считал поздний GET общего SVG на странице operator после select как неожиданный запрос. Добавлен `wait_for_load_state('networkidle')` до очистки массива наблюдений; строгий `requests==[]` после select сохранён, автоматический POST не появился.
2. Повтор всего targeted набора: **21passed,1upstream warning,103.61s**. Включены tests/test_design_browser.py, test_ui_revision_browser.py, test_attention_browser.py, test_ui_accessibility_browser.py. Это live login/day-week-session/grades/request/operator/status/account isolation; U04 autoGET+checkbox+Back+JSoff; K01 digest events и ack persistence; keyboard/errors/reflow/network retry/conflicts. Старые функциональные и negative asserts не удалялись.
3. Root попросил bbox nav labels сверх scrollWidth. Проверка обнаружила настоящий overflow при equal cells/nowrap: на360 «Успеваемость»74.83px при cell70.39, «Уведомления»71px при cell70.41. Мобильные cells изменены на intrinsic flex width с min44 и естественным CSS wrap fallback, без wbr и без уменьшения11px.
4. Финальный повтор design module после этого узкого CSS исправления: **5passed,1upstream warning,24.85s**. Новый test проверяет span и настоящий text Range внутри anchor на360/390 с допуском1px, в том числе при активных разделах. Фактический отдельный nav-label-bounds.json: на320/360 все5 labels внутри cells, font11px, mincell44. На360 длинный label74.83px/cell88.23; на32074.83/cell79.80.
5. Design module проверяет hierarchy/nearest firstscreen, header/main content-edge alignment≤1px, horizontal overflow, общий notice ровно1, SVG nav, contrast control borders≥3/text≥4.5, profile target44×44, authenticated login без shell, immediate Tab visibility, reduced motion, narrow320 и reflow720×500.
6. `manage.py check`:0issues; `makemigrations --check --dry-run`:Nochanges на существующей own app DB. Ruff check passed; Ruff format --check:260files already formatted; git diff --check clean.

App/tests freeze передан root после5passed. Root запустил один independent fullsuite с hash guard; до его результата готовность полного прогона не заявляется. После freeze исполнитель меняет только evidence и private snapshots, не приложение/тесты.

## Визуальное ревью и evidence

Early4PNG home/login360/1440 root просмотрел и принял направление; затем schedule360/requests1440/grades1440 также приняты. По замечаниям исправлены orphan arrow в CTA ближайшего события, искусственный nav wbr, metadata<11, authenticated login chrome и повторная login подпись. Новые/переписанные CSS отформатированы обычными rules/properties.

Финальные44AFTER PNG в after/: login/home/local-user/grades/schedule/session/requests/notifications/operator ×360/390/768/1440 плюс home/notifications full-page на каждой ширине. Before/early не перезаписывались. Финальные home360/home1440 визуально просмотрены исполнителем: событие в первом экране, desktop CTA в одну строку, навигация читаема и не пересекается. Raw final scanner comparison приведён в следующем разделе.

## QA и ограничения

До разрешённого cleanup собственная среда сохранялась для root. Во время проверок использовались private state /tmp/u05-qa-state.json0600; helper /tmp/u05-qa.py (run даёт allowlisted own app/TEST_DB environment); обновление только своего app через /tmp/u05-refresh.py. Предварительный /tmp/u05-cleanup.py был подготовлен для review; окончательное удаление выполнил /tmp/u05-final-cleanup.py с дополнительными guards, описанными ниже. До cleanup state содержал credentials и не включался в Git/evidence.

Snapshot HTML очищен от всех hidden values/паролей, cookies не переносились, публичная статика copied только из собственной сборки. Raw HTML находится только в private /tmp, scanner-generated rendered.html после каждого run также переносится туда. Scanners не подтверждают server actions. Quick skips и marketing/snapshot false positives изложены в audit.md; fullscreen hero/photos/moments не навязываются рабочему кабинету. Публичная сеть/телефон/production latency здесь не проверялись. Commit/push/deploy не выполнялись.

## Независимый full suite и финальная узкая коррекция

Root full suite до последних tap-size поправок: **402passed,1upstream warning,248.15s** (wall248.52s), inputs_unchanged=true. Raw regression-independent.json/txt. После этого root разрешил только `.brand min-height44` и `.attention-card .dashboard-item>a min-height44` вместо36, плюс meaningful height asserts в существующем design module. Никакого расширения scope приложения не было.

Собственный уже запущенный финальный design module: **5passed,1warning,24.80s**. Root независимо повторил модуль после узких правок: **5passed,1warning,25.34s**, inputs_unchanged=true; design-final-independent.json/txt. Полный suite повторно не запускался и не объявляется прогоном идентичных финальных source bytes. Ruff check/format(261files)/diff-check успешны перед финальным freeze.

Первые AFTER consistency reports не уничтожены: after-first-taste-home (55FAIL/39WARN) и after-first-taste-login (19FAIL/12WARN). По ним устранены применимые tap-size WARN brand43px/radar36px. Финальные отчёты находятся в after-taste-*; проверка perf отложена до окончания root full/design, чтобы не сравнивать CPU timings под нагрузкой. App/tests после финального freeze не изменяются.

## Финальные настоящие AFTER scanners и сравнение

Финальные scans выполнены последовательно на новых собственных Chrome profiles, с теми же baseline flags/widths1440,360 и тем же fictional app DB/seed anchor. Checker scripts не менялись, проваленные правила не отключались. Сводка machine-readable — comparison.json; исходные report.json/console.txt/crops/invocation.json сохранены полностью.

| Проверка | BEFORE | Финальный AFTER |
| --- | --- | --- |
| Home consistency |55FAIL/34WARN,exit1 |55FAIL/35WARN,exit1,75.02s |
| Login consistency |21FAIL/10WARN,exit1 |19FAIL/12WARN,exit1,44.01s |
| Home perf,3runs,1440/360 |PASS,0FAIL/0WARN |PASS,0FAIL/0WARN,exit0,19.50s |

Общий счётчик FAIL не является оценкой личного кабинета. Значительная часть по-прежнему относится к marketing fullscreen sections/hero/photos/CTA/moments, шаблонной .wrap структуре и сравнению viewport без sidebar. Snapshot-only routes отсутствуют на static checker server; это не сломанные Django ссылки. Русский skip-link/heading word parser имеет известные ограничения. Quick skipped checks перечислены без изменений в каждом report.notChecked и audit.md. GATE:PASS не заявляется.

Подтверждённые improvements: actual header/main левые content edges были360/254px, стали316/316px; live tests допускают≤1px на всех разделах. Ближайшее событие теперь целиком в первом экране360; новая nav bbox проверка исключает пересечение labels на320/360. Старые home focus-visible2FAIL и login brand contrast2.82:1FAIL исчезли; **focus-visible PASS** в обоих финальных reports. Пограничный brand43px и radar actions36px из первого AFTER исправлены до44. Login empty-area61%/51%FAIL заменены одним43%WARN у чистой панели формы. Разные native-gray/primary controls заменены общей системой, тексты и источники сохранены.

Отдельно остаётся **focus-ring FAIL** на `main:focus {outline:none}` в обоих reports. Это неинтерактивный программный landmark `tabindex=-1`, на который ведёт skip-link, вне обычной Tab цепочки. Его focus state/scroll target проверены live; реальные интерактивные controls сохраняют контрастные outlines и immediate visibility. Этот finding не скрывается и не объявляется PASS, дополнительная CSS-правка ради scanner root не требовал. Остающийся tap-size WARN32×32 относится к коротким inline source links в тексте radar footnote; основные отдельные radar действия/brand/profile имеют44px.

Perf final после окончания root тестов, host CPU2/2%:1440 —15.5KiB/9requests, FCP/LCP44/44ms (spread40..108);360 —15.1KiB/8requests, FCP/LCP36/36ms (36..40). На обеих ширинах CLS0.000, long tasks0, blocking0ms, broken requests0. CSS5.3KiB против baseline7.6KiB; JS прежние3files/3.4KiBparsed. Нет внешних font/image dependencies/WebGL. Разницу44vs40ms desktop не трактуем как реальную регрессию/ускорение: это локальный CPU timing внутри baseline spread, не production field metrics. Mobile page height3.8screens vs3.9, desktop2.5 vs2.3; увеличение desktop высоты ради читаемой иерархии не скрывается. DOM165nodes vs133.

Финальные screenshots after/ обновлены после tap-size правок; before/ и early/ сохранены. Private rendered HTML из финальных consistency runs снова перенесён из evidence в собственный private folder. Изменений app/tests после финального freeze не было. Безопасный scan evidence на три известных QA secrets и exact cleanup завершены, результат приведён ниже.


## Финальный cleanup и передача

После завершения root проверок и final scanners выполнен разрешённый /tmp/u05-final-cleanup.py: **exit0**. До удаления363evidencefiles всех типов проверены на три известных QA secrets; совпадений нет, HTML/env artifacts отсутствуют. Значения секретов не выводились.

Own CID/image/owner/project labels, named volume/network labels и unique attachment/endpoints подтверждены; остановлен только свой Gunicorn по PID/cmdline/port, app loopback port проверен закрытым. Own container/volume/network удалены, отсутствие проверено. После path/realpath/UID/mode safeguards удалены exact private folder и private state; отсутствие подтверждено. Полный безопасный aggregate — cleanup.md. Пользовательские ресурсы/colors.jpg не изменялись, prune/force/deploy не выполнялись.

App/templates/static/tests после финального code freeze не менялись; остаются только согласованные source changes и evidence. Результат готов к root accepted/staging review. Commit/push пока не выполнялись.


## Сохранение точного stdout при staging

Cached whitespace check выявил trailing spaces в табличном stdout восьми Taste console.txt. По решению root точные исходные bytes каждого console сохранены без потерь рядом в детерминированном `console.raw.txt.gz` (gzip mtime=0); decompress==original проверено. В читаемых console.txt удалены только spaces/tabs непосредственно перед newline, все строки/значения/exit codes сохранены. Это форматирование вывода для Git; findings не исправлялись. report.json/crops и skill scripts не менялись. SHA256 оригинальных stdout записаны в versioning.md.
