# CAT08 — коты в стиле ИИ-помощника

Запрос: «сгенерируй котов по стилю таких же как ии помощник».

Использованы встроенный image_gen и Taste Skill 2.5.1. Перед генерацией просмотрен static/images/persona-assistant.png: он служит референсом стиля и палитры. Три отдельных генерации, transparent_background=true. Изображения просмотрены непосредственно в ответах инструмента: единая пиксельная стилизация, светлая шерсть, navy/teal/sky с небольшими lilac/pink деталями из референса; различимы сонные глаза, внимательный взгляд и озорное подмигивание/поднятая лапа. Это новые растровые исходники, не готовые анимационные кадры игры. Точная сетка48×48 в этих исходниках не заявляется; старый runtime CAT07 сохранён.

Файлы скопированы без изменения, оригиналы оставлены в ~/.codex/generated_images/01a1db2e-bc83-70d0-8b3a-fc21fe0c2be6/:

- static/images/cat-assistant-style/sleepy.png — exec-73e13f0b-43ea-4d88-ad85-4373b690767d.png.
- static/images/cat-assistant-style/scholar.png — exec-a3beade4-5b1f-498b-ac4e-83ddee62795a.png.
- static/images/cat-assistant-style/chaos.png — exec-1e9fc253-31a9-4377-ab28-a6656cc69bd7.png.

## Промпты

Общая часть:

Use case: stylized-concept. Asset: a single original cat mascot for persōna student portal. Transform the attached AI assistant reference into a NATURAL FUR CAT character, using the image strictly as a STYLE and PALETTE reference: the exact same polished cute pixel-art finish, chunky stepped square pixel clusters, deep navy outlines (#2F4156), off-white/cream fur, muted teal (#567C8D), pale blue (#C8D9E6), restrained lilac shadow clusters and tiny pink cheek/ear/paw details. Not a robot, no screen face, no headphones, no antenna, no metallic parts. Large rounded head with triangular ears, soft compact seated body, short paws, curled tail. Front view, full body, centered with generous clear transparent margins, crisp and expressive silhouette. Design on a logical 48x48 pixel-art grid enlarged cleanly for display, no blur or smooth vector curves, no 3D, no painterly texture. No clothing, no glasses, no toys, no book, no text, no labels, no watermark, no ground plane, truly transparent background. All three cats belong to the same coherent character family.

### sleepy

Character 1: СОНЯ / sleepy cat. Soft drowsy closed eyelids, a very small contented smile, slightly lowered ears, relaxed tucked front paws and gently curled tail. Sweet cozy expression, visibly a sleepy character. Keep the complete ears and tail in frame.

### scholar

Character 2: ОТЛИЧНИК / studious cat. Bright attentive open dark navy eyes with small square highlights, alert symmetric ears, neat upright seated posture, front paws carefully together, calm earnest small smile. Express intelligence through face and posture only, no glasses or accessories. Keep the complete ears and tail in frame.

### chaos

Character 3: МАЛЕНЬКИЙ ХАОС / little chaos cat. Cheeky joyful wink, tiny pink tongue in a mischievous grin, one front paw lifted playfully, one ear slightly cocked, lively curled tail. Endearing impish energy while keeping the same seated body proportions. Keep the complete ears and tail in frame.

## Приёмка

Root визуально принял все три результата для запроса на генерацию. Интерфейс, CSS, модели, игровые кадры и анимации не менялись; UI/browser regression suite для новых неиспользуемых файлов не требуется. Вызовов внешнего API пользователя нет. Точный путь и формат проверяются по фактическим PNG, без объявления иллюстраций техническими спрайтами. Эти ассеты можно использовать как источник для следующего этапа адаптации.
