# CAT09 — узкое исправление веса ассетов

Статус root: changes requested после успешных36основных и3DPRпроверок. Фактический Taste perf дал2FAIL/7WARN по двум размерам экрана: largest image934KiB icons/persona-mark.png, изображения1697KiB и суммарно до2660KiB. Мастер кота около761KiB станет следующим largest после исправления логотипа. Raw результат сохранён как taste-perf-before.txt; нельзя объявлять его PASS.

Исполнитель тот же cat01 Sol/low, один writer, без субагентов. Требования/все прежние ограничения CAT09 сохраняются. Цель — тот же вид и те же пиксели котов/движения при маленькой загрузке. Не править оригиналы PNG.

## Минимальное решение

1. Добавить dev-скрипт scripts/build_cat_art.py (можно другое ясное имя в scripts), который без БД использует текущие cat_card palette/rig и renderer + существующий Playwright/Chromium в локальном временном HTML. Из каждого CAT08 master получить нынешний подготовленный grid48×48 и экспортировать PNG в static/images/cat-assistant-style48/{character}.png. Это экспорт результата renderer, не свободное перерисовывание и не Python/image-editor правка мастеров. Рядом экспорт96×96копии исходного static/icons/persona-mark.png как static/icons/persona-mark-small.png, сохранив прозрачность/рамку/рисунок, обычное качественное уменьшение для header/favicon. Оригиналы read-only.
2. Скрипт должен работать без миграций/PG, tempсервер содержит только нужные inputs/module/html (не раздавать весь repo/.env), завершать свой browser/server. Использовать уже имеющийся Playwright devdependency, без новых пакетов. Режим --check: сравнить воспроизведённые RGBAпиксели с shipped files, не байты PNG разных Chrome. Команду и ограничения записать. Для получения raw config builder явно отключает native_grid, source указывает master; runtime использует готовый native48.
3. Добавить config.native_grid=true и source new48path; renderer в native режиме не делает повторный crop/scale/centering. Любая палитра/rig/поза должны остаться как в принятом первом варианте. Подготовленные48RGBA кодируются полностью непрозрачными/прозрачными пикселями. Сохранить все пути загрузки/fallback/static profile, и graceful error. Источник по-прежнему CAT08, исторические коты не возвращаются.
4. Только brand.html (brand img) и base.html (favicon) переключить на малый logoPNG. login-persona-art остаётся на большом оригинале, геометрия/цвет/тексты/ссылки/навигация не меняются. Сначала создать assets, затем менять ссылки, чтобы локальная версия не оставалась с отсутствующими файлами.
5. Адаптировать assertions о новых путях без ослабления проверки реальных canvasпикселей. В обычном runtime не должно быть запросов тяжёлых CAT08мастеров/большого logo на /cat/ и /profile/. Зафиксировать размеры файлов/byte saving. Добавить meaningful check компиляции или smoke --check и URL/download-size assertions; не дублировать весь broad suite, root повторит после новой freeze. Нативный48renderer и новый PNG дают идентичный исходный grid и150кадров; допускаются только ранее разрешённые rigисправления, а не новая внешность.

## Дополнительный allowlist

К прежним разрешённым файлам добавлены scripts/build_cat_art.py, static/images/cat-assistant-style48/, static/icons/persona-mark-small.png, apps/accounts/templates/accounts/brand.html и base.html; релевантный небольшой test builder/nativeassets при необходимости. Код/мастера/логотип-original/README/deps/migrations/остальные интерфейсы read-only. Root отдельно ведёт docs/ARCH/STATE.

Дать source freeze после targetedsmoke и --check, потом только evidence/sanitizedsnapshot обновить под новые URLs/assets. Root повторит36релевантных тестов, perf и визуальные проверки; предыдущий successful suite остаётся честным результатом старого варианта. До accepted не commit/push и не менять пользовательский daemon.
