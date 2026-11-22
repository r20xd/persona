# U07 implementation

Исполнитель gpt-6.1-sol / low, один writer, без делегации. Постановка U07 и действующие правила проекта учтены; главная U06 не изменена.

- `persona-mark.png` скопирован byte-for-byte из предоставленного родителем generated_images asset; оригинал сохранён. Источник — пользовательский persona.jpeg, обработка — imagegen родителя. Дополнительная обработка/генерация исполнителем не выполнялась; лицензия пользовательского исходника не выдумывается.
- Изображение P подключено вместо куба в shared brand (sidebar/mobile/login), preview brand и favicon. Старый sprite не изменён, остальные иконки продолжают работать.
- На login и preview/login добавлен absolute слой с двумя крупными полупрозрачными P, aria-hidden, пустые alt, pointer-events:none. Слой не занимает высоту; контент расположен выше. На телефоне одна P, существующие размеры формы и первого экрана сохранены.
- Добавлены meaningful browser assertions загрузки logo, decor accessibility/pointer-events; существующие design проверки reflow и кнопки входа остаются.

Фактические проверки:

- `.venv/bin/python manage.py check --settings=config.settings.preview` — no issues.
- `.venv/bin/ruff check tests/test_design_browser.py tests/test_preview_browser.py` — passed.
- `.venv/bin/pytest tests/test_preview.py -q` — 6 passed (0.42s).
- `git diff --check` — passed.

Браузерные проверки и screenshots выполняет родитель независимо на disposable PostgreSQL/Chromium. Исполнитель их не дублировал. Auth, models, filter/POST contracts и зависимости не изменены. Commit/push не выполнялись.
