# CAT04 — пиксельные игрушки и пользовательские кадры

Коты не генерировались заново: используются неизменённые листы cat_little_chaos.png и «Соня и Отличник_ пиксельные коты.png», показанные пользователем. Runtime отображает исходные прямоугольники idle/jump/joy без подписей и рамок. В static находятся технические копии pixel-chaos-sheet.png и pixel-duo-sheet.png.

Игрушки созданы встроенным image_gen четырьмя отдельными вызовами, transparent_background=true, referencecat_little_chaos.png только как pixel-styleguide. Общие требования промптов: один отдельный предмет рядом с котом, без кота/листов/рамок/подписей/фона; classic64×64game sprite, видимые квадратные пиксели, ступенчатые края, no blur/antialiasing/3D; палитра ONLY #2F4156/#567C8D/#C8D9E6/#F5EFEB/white; прозрачный квадрат с отступами и маленькой пиксельной тенью, читаемый в32px.

1. **Клубок** — округлый teal yarn с lightblue thread detail/navyoutline и завитком нити. `exec-731006a8-d66e-4f23-9c08-b9ac79226be5.png` → static/images/toy-yarn.png.
2. **Мячик** — округлый toyball с чередующимися beige/teal/sky панелями, whiteglint, navyoutline. `exec-08720af7-3579-436e-a7d2-f1f15145ac82.png` → static/images/toy-ball.png.
3. **Мышка** — fabricmouse3quarter sideview, beige тело, большие skyblue уши, navyглаз/нос и teal завитой хвост. `exec-db9ddaca-801e-40bc-bcdc-81ccbbe702c3.png` → static/images/toy-mouse.png.
4. **Рыбка** — skyblue plushfish, teal хвост/плавники, beigeполоса, navy стежки/глаз, горизонтальный силуэт. `exec-14f51db0-554f-4e81-99d8-e38d6303b34a.png` → static/images/toy-fish.png.

Все результаты просмотрены. Для web размер приведён к256×256 nearest-neighbour с сохранением RGBA/прозрачного canvas и пиксельных граней (временный Pillow через uv --no-project, не dependency приложения). Размеры файлов18–30KiB. Оригинальные generatedPNG сохранены в ~/.codex/generated_images/01a1db2e-bc83-70d0-8b3a-fc21fe0c2be6/. CLI/APIключи для генерации не использовались. Лицензия пользовательских исходников отдельно не предоставлялась, её наличие не утверждается.
