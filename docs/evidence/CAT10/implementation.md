# CAT10 — редкие прогулки собственного кота

Исполнитель cat01, прежняя назначенная модель Sol/low, без подагентов/замены модели. Прочитаны TASK/AGENTS, architecture31/32, PLAN CAT10, workflow и актуальный Taste2.5.1 с core/motion references. Тип: существующий software-кабинет, небольшой игровой элемент. Сохранены клиентские navy/teal/sky/paper, существующая типографика и функциональная навигация. Новые artwork/иконки/deps/модели/миграции/endpoints не создавались.

## Реализация

Context processor работает только на GET активного student и whitelist читаемых маршрутов; отдельно выдаёт preference config на cat. Один StudentProfile.select_related(studentcat) LEFT JOIN по собственному user_id; отсутствующий профиль исключает payload, отсутствующий кот даёт presentation default без записи. В HTML только whitelist name/characterlabel/quote/renderer и opaque saltedHMAC ownerkey. ORM/чужие сведения/ФИО/учебные данные в payload не входят. GET не создаёт StudentCat. Guest/operator/profile/chat/editors/request-new/POST исключены. Каталожная карточка другого вымышленного студента всё равно показывает только собственного питомца.

Условный base partial подключает один48renderer на eligible странице. Game/profile не получают cameo, их экземпляры renderer не дублируются. Отдельные scopedCSS/JS; game controller/серверные награды/20секунд/12карточек/4игрушки не менялись. Наcat localcheckbox вне POSTформы появляется только при доступном GETconfig и JS. БезJS не показывается неработающее обещание сохранения.

Вstorage только два owner-scoped значения: enabledbool и deadline. Первая прогулка8–18s, следующая90–180s; deadline фиксируется до показа и сохраняется между навигациями/окнами. Run/hop имеют разные реальные координаты/движения6–9s и подходящие кадры существующего renderer. Направление зеркалит изображение; размер48×целое число физических пикселей, origin привязан к devicegrid, DPR1.25 проверен screenshotpixels. Последниеpose/frame кэшируются, одинаковые кадры не перерисовываются каждыйRAF.

Overlay pointer-events:none; только petbutton/bubble интерактивны. Desktopтраектория справа от sidebar, mobileвыше bottomnav; resize ограничивает координаты/bubble. На низком экране bubble ограничивает высоту/скролл; если места недостаточно, показ откладывается. Hover/focus останавливают движение без захвата фокуса при появлении. Click/Enter/Space останавливают прогулку, joy и реплика/«К коту»/скрыть/отключить. Bubbleконтролы44px; Escape/close возвращают фокус из собственного скрываемого элемента на прежний элемент/основнойконтент.

Hidden/reduced/disabled/input/textarea/select/contenteditable/modal подавляют показ. Никакого вечного5sпроверяющегоtimer: suppression очищает timeout, resume по visibility/reduced/storage/focus/dialog/renderer-ready events. Pagehide отменяетRAF/timeout/observer. Pageshow учитывает существующий securityguard: BFcache сначала перезагружает личный кабинет. При blockedstorage cosmeticmemory сохраняет текущую настройку до закрытиястраницы; основнойUI продолжает работать, настройка показывает ограничение.

## Фактические проверки исполнителя

- Owner/projection/query/noGETwrites/exclusions/renderedroutes:3passed.
- Первый live360run и1440hop, координаты/keyboardjoy/44px/Escape/sharedcooldown:2passed,1existingfixturewarning,12.70s. PNG run/hop/clicked сохранены и clicked360 просмотрен; parent также просмотрел и согласовал направление.
- После parentreview улучшены sidebar/lowheight/bubble/DPRgeometry/paintcache и event-basedscheduler; final suppression/storage smoke:2passed в узком3-case запуске, третий обнаружил floatmilliseconds в testclock helper (runtime не ошибка).
- Только fractionalDPR/resize повтор:1passed9.75s. Реальные непрозрачные48gridпиксели в screenshot приDPR1.25 — равномерные3devicepixelблоки; opaque mask зеркалится вместе скотом. Low320×400 bubble/cat вviewport ивышеnav.
- JSsyntax/Ruff/format/diffcheck прошли передfreeze. PostgreSQL55439 disposableQA, существующий Chromium; userdaemon/данные/секреты не трогались.

Исправления тестов документируются честно: loginredirect уже инициирует sharedcooldown, поэтому deterministicsetup очищает только cosmetickeys собственного QAбраузера передпроверкой. Первоначальный fixed9200ms иногда не совпадал с фактическим deadline; helper теперь читает ownerdeadline и виртуально доходит до него. NativeSpace activation требует короткого продвижения virtualclock. BFcachetest учитывает существующий privacyreload и сохранённый deadline, вместо предположения о старом DOM. Это не productiondebugcontrols. Неудачные узкие итерации не объявляются PASS.

Source freeze перед parent broad suite; окончательная независимая приёмка ещё за root. Послеfreeze только evidence. UPDATE_CAT10_EVIDENCE пишет реальныеscreenshots и sanitized actual page.content наclicked360 (csrf заменён review-onlyplaceholder). Канонический snapshot дляTaste будет подготовлен изэтого renderedHTML после независимого запуска. Не выдаём screenshot/static snapshot за POST/securityдоказательство; liveunit/browser проверки отдельны. Полный маркетинговыйGATEPASS исполнителем не заявляется, kit не изменялся; parent ведёт независимый gate/review.

## Actual Taste snapshot shoot

Canonical /private/tmp/cat10-snapshot/rendered-home.html copied from root's live Chromium page.content, CSRF values verified as snapshot-not-a-live-token. Manifest/compressed static files were collected only into /private/tmp/cat10-snapshot/static using test settings and temporary STATIC_ROOT; no DB/user static collection/daemon changes.

One command: `.venv/lib/python3.13/site-packages/playwright/driver/node /Users/local-user/.codex/plugins/cache/taste-skill/taste-skill/2.5.1/skills/taste-skill/scripts/shoot.mjs --url /private/tmp/cat10-snapshot/rendered-home.html --root /private/tmp/cat10-snapshot --w 360 --out docs/evidence/CAT10/taste-rendered-360.png --profile /private/tmp/cat10-taste-shoot --no-tiles`. Exit0, saved360×3335. Output taste-output.txt. Executor viewed the image and reported the following limitation to root rather than claiming visualPASS.

The serialized open bubble/traveller retains inline coordinates from the live900pxviewport; Taste default screenshot viewport height780 differs. JS closure's visible flag is not serialized by page.content, so replaying the captured open state does not reposition it as a live visible cameo would. In this one snapshot shot the cat is under nav. Live900px and320×400 resize scenarios are separately checked with real browser state and screenshots; snapshot is not a geometry/POST substitute. Source/kit and renderedmarkup were not changed to conceal this; no secondshoot or broad rerun by executor. Root owns gate/perf interpretation or a fresh initial-state snapshot.
