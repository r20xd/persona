# CAT05 — очистка качества пиксельных листов

Инструмент: встроенный image_gen,2отдельныхedit-вызова с referenced_image_paths исходноголиста, transparent_background=false. Оба исходника предварительно просмотрены. Оригиналы не перезаписывались.

## Промпты

Общее точное задание обработки: precision restoration cleanup of PROVIDED PIXEL ART SPRITE SHEET, preserve exact1536×1024canvas, every original sprite center/boundingbox/scale/pose, row-columnlayout/text/background/frame; remove fuzzy soft halos, noisy antialiasing/speckles, clean intentional squarepixelclusters and sharp steppedoutlines, clear facial pixels/pawpads/ears. Faithfulcleanup, not redesign: no added/removed/shifted/enlarged cats, original animation source rectangles stillwork; classic handplaced32/64pixel aesthetic, no smoothvector/3D/photo.

1. `cat_little_chaos.png`: preserve happy lavenderwhite roundkitten, closed smile/tongue,4idle/jump/joyframes and8directions. Результат `exec-a4a58768-f5a5-413c-b910-232bb558f196.png` скопирован в **static/images/pixel-chaos-clean.png**.
2. `Соня и Отличник_ пиксельные коты.png`: leftSonya sleepyclosedeyes, rightScholar blackglasses; preserve bothidentities/colors/poses/4frames/8directions. Результат `exec-aa7d27a8-aaef-468f-bc1b-8fd03b6a4f88.png` скопирован в **static/images/pixel-duo-clean.png**.

Исходные generatedPNG находятся в ~/.codex/generated_images/01a1db2e-bc83-70d0-8b3a-fc21fe0c2be6/. ФинальныеPNG скопированы без ресайза/перерисовки Python;1536×1024подтверждено. Старые user/source/static-sheet файлы сохранены. Новые листы — производная обработка, не идентичная исходным пикселям. Визуально просмотрены полные листы; края/лица стали чище, кадры сохранили расположение. Проверка в приложении описывается в review.md.

Контрольbrightbboxпервогоidle в используемыхокнах: chaos244/480/368/601 (offset0,+0.5sourcepx), sleepy183/390/278/478 (+0.5,-1), scholar950/390/1044/478 (0,-1). Это сохраняет практически симметричный визуальный центр при ранее исправленных координатах. Нового внешнегоruntimeсервиса и dependency нет; CLI/APIключи не использовались.
