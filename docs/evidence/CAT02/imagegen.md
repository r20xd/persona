# Три образа кота — imagegen

Инструмент: встроенный image_gen, три отдельных вызова с referenced_image_paths=cat.jpeg, transparent_background=false. Исходник предварительно просмотрен и не изменён. Сгенерированные результаты просмотрены, затем скопированы в проект как800×800 WebP quality88 (временный Pillow через uv --no-project; зависимость приложения не добавлялась). Авторство исходного референса не устанавливалось; использован предоставленный пользователем материал.

## Набор промптов

Общие требования: один квадратный портрет того же круглого серебристого хромированного котёнка из cat.jpeg; сохранить фронтальную сидячую позу, положение головы/лап/хвоста и масштаб для наложения существующих аксессуаров; тёмный navy фон, silver/iceblue/teal/beige-white отражения в палитре persōna, без акцента на purple; polished3Dtoyrender; целые уши/хвост/ступни, без одежды/очков/шапки/шарфа, текста и коллажа.

1. **Соня**: peacefully closed eyes, tiny sleepy yawn, gently drooping eyelids, three tiny sleep bubbles above head. Результат `exec-492da01f-01c8-4f29-9737-7afff27bd0e3.png`, проект `static/images/cat-sleepy.webp`.
2. **Отличник**: attentive wide open blue eyes, confident kind inquisitive expression, tiny proud closed-mouth smile, ears alert; two small floating metallicblue four-point sparkles near ears suggesting cleverness. Результат `exec-383e5e74-5c13-4f79-a9c8-b63cd97b47c6.png`, проект `static/images/cat-scholar.webp`.
3. **Маленький хаос**: playful one-eye wink, other eye large bright blue, happy open mouth with tiny tongue, slightly unruly zigzag fur tuft; three tiny metallic sky-blue lightning-bolt sparkles near ear imply playful chaos. Результат `exec-ed9c74ec-df3c-4818-b5d7-0702c689a7f6.png`, проект `static/images/cat-chaos.webp`.

Исходные PNG оставлены в ~/.codex/generated_images/01a1db2e-bc83-70d0-8b3a-fc21fe0c2be6/. В runtime используются только локальные WebP в репозитории. Секреты/APIключи не требовались, CLI image generation не применялся.
