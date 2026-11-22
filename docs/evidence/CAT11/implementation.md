# CAT11 — более частые прогулки

Назначенный прежний исполнитель cat01, gpt-6.1-sol/low, без смены модели/подагентов. Прочитаны узкая постановка, AGENTS/TASK, ARCHITECTURE§32/CAT11, PLAN и актуальный Taste2.5.1/motionreference. Существующий software-кабинет: меняется только частота запрошенного пользователем косметического движения, без новой раскладки/палитры/ассетов. Сохраняются pause/keyboard/reduced/hidden/editing/dialog/disable и pointer-events ограничения CAT10.

## Изменения

- Первый deadline3–6секунд, повтор20–40секунд start-to-start. Пробежка/прыжки6–9секунд и renderer не менялись.
- Только deadline key версионирован в persona.cat.walk.{opaqueowner}.v2.next. Прежний enabledkey сохранён; старый longdeadline игнорируется, но не удаляется, прочий storage не очищается.
- Явное скрытие кнопкой или Escape назначает новый20–40секунд deadline, затемhide/schedule. Даже после долго открытого облачка не происходит мгновенного повторного появления. Naturalend оставляет первоначальный start-to-start deadline.
- Scheduling/guards/cleanup/memoryfallback/ownership и серверный код не менялись. Ни новых опросных таймеров, ни ускорения кадров.

## Проверки в diff

Browser helper читает точный owner v2key из безопасной projection, поэтому сосуществующий old.next не путает тест. Clock при setup приостановлен, nativeactivation/RAF при необходимости явно продвигаются. Проверка навигации сравнивает сохранённыйdeadline, ожидает hidden перед ним и actualvisible после него вместо прежнего произвольного20s.

Новые содержательные сценарии:360/1440 с детерминированными разными random проверяют диапазон3–6/20–40s, видимость до/послеdeadline, игнорирование старого180sdeadline, сохранение этого legacyvalue и unrelatedpreference, naturalend без сбросаdeadline и навигацию. Отдельно прежнийdisabled остаётсяdisabled после versionchange и снова включается через настоящийcatcheckbox. Два longbubbleсценарияclose/Escape ждут50virtualseconds, проверяют новую20–40sпаузу и реальное повторное появление.

UPDATE_CAT11_EVIDENCE пишет PNG только в CAT11; snapshot не создаёт. Исторический CAT10evidence не меняется. Прежние motion/DPR/storage/suppression проверки сохранены, helper BFcache тоже читает точный v2key.

## Фактические команды и статус

- `.venv/lib/python3.13/site-packages/playwright/driver/node --check apps/accounts/static/accounts/cat-cameo.js` — exit0.
- `UV_CACHE_DIR=/tmp/persona-uv-cache uv run ruff check tests/test_cat_cameo_browser.py` — All checks passed.
- `UV_CACHE_DIR=/tmp/persona-uv-cache uv run ruff format --check tests/test_cat_cameo_browser.py` — alreadyformatted.
- `git diff --check` — exit0.

Source freeze перед независимым rootbrowserпрогоном. Исполнитель не запускал собственнуюБД/pytest/browser/fullgameпроверки, не менялdaemon/схему/deps/секреты и не делалcommit/push/deploy. BrowserPASS здесь пока не заявляется; root ведёт фактический результат/review. Taste применён к поведению; прежняя раскладка не менялась, новый маркетинговыйGATEPASS не заявляется и kit не правился.

## Tests-only correction after independent review

Root's first focused run:15passed/3failed89.47s; original rawlog independent-tests.txt retained. Two migration/timing failures exposed incorrect testclock input: Playwright's numeric pause_at receives seconds, whereas Date.now() returns milliseconds, moving the test date1000×forward. Corrected only the helper to pass new Date().toISOString(); the olddeadline and currenttime now share real milliseconds. FractionalDPR/lowresize failure read coordinates before the paused browser processed resize; added clock.run_for(100) after set_viewport_size before reading geometry. No application behavior/geometry/cadence changed.

Ruff check/format and diffcheck passed after these tests-only edits. New source freeze; root repeats browserfile only, without re-running already passed sharedshell/server checks. No executor browser/DB run or commit.

Root's second browser run:9passed/1failed61.03s (independent-tests-02.txt retained). All cadence/migration/optout/close cases passed; only paused-clock resize synchronization still read old geometry despite100virtualms. Replaced that test-only synchronization with clock.resume(), a one-time native resize marker registered after the runtime's handler, set_viewport_size and wait_for_function on actual event delivery. No synthetic resize dispatch or application edit. Ruff/format/diff passed; source refrozen for root to repeat only this one case. If actual native event arrives with wrong geometry, this becomes a runtime review rather than weakening assertions.
