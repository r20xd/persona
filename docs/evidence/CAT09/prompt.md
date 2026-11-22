# CAT09 — новые коты на сайте

- Запрос: «подключи новые анимации и измени сайт» после генерации трёх CAT08 котов в стиле ИИ-помощника.
- Исполнитель: cat01, gpt-6.1-sol/low, один writer без делегации. Root: архитектура/постановка/независимое ревью.
- Требования: PRD-03/04, TECH-03/06, пользовательские CAT07–CAT09. TASK.md и AGENTS.md обязательны; контракты ARCHITECTURE §27–31, PLAN CAT09.
- Вход: main архивная-версия, принятые новые1254×1254RGBA PNG static/images/cat-assistant-style/{sleepy,scholar,chaos}.png. Мастера не менять. Пользовательская .gitignore и прочие untracked не входят в задачу.

## Результат и метод

В игре и собственном профиле виден именно новый кот выбранного характера; старые рисованные CAT07 коты не используются в нормальном runtime. Реализовать локальный canvas48×48 renderer существующего artwork: crop прозрачных полей, nearest sampling, binary alpha и фиксированная небольшая palette с navy/teal/sky/cream и малым pink/lilac как в мастерах. Это отрисовка ассета, не изменение PNG и не генерация новых растров вручную. Сохранить узнаваемую мордочку, силуэт и характер. Достаточные поля для прыжка/хвоста, кот по центру,4игрушки32×32 рядом. Integer physical sizing и device-aligned origin сохранить.

Использовать существующую state machine7состояний и длительности. Кодовый rig разделяет голову/тело/хвост/при необходимости лапы с аккуратным перекрытием швов; головы/хвосты двигаются относительно тела. Дыхание, реальные моргание/зевок через локальные face overlay/masks, приседание/прыжок/приземление, радость, потягивание, удивление различимы. Можно адаптировать параметры каждого характера по мастер-координатам. Показ одной новой статичной картинки поверх старых анимаций или только дрожание неизменной картинки недостаточны. PNG не редактировать Python/image editor; canvas код — renderer сайта. Новых ImageGen вызовов/пакетов не нужно.

Профиль рисует один static кадр; без JS/если image/renderer не готов — обычный img с alt. При загрузке никаких пустых/прыгающих областей и unhandled errors; загрузка не блокирует Start/повторные раунды. Canvas role=img/доступное имя, декор не участвует в a11y tree. Metadata безопасно через json_script. Можно отдельный модуль cat-renderer.js перед cat.js, профиль получает только renderer/fitting, никаких игровых animation timers. Готовность и redraw согласовать с async loading.

Действующие20секунд,12переставляемыхкарточек, API попыток/награды, persistence, CSRF/owner, wardrobe и игрушки сохраняются. Автопозы только во время игры; wrong→surprise/correct→jump/win→joy, input priority; pause/hidden/calm/reduced reset/freeze, pagehide cleanup. Без изменения моделей/миграций/зависимостей/остальных разделов/ИИ-чата/пользовательских картинок и .env.

## Владение

Разрешены apps/accounts/cat.py (только presentation), apps/accounts/static/accounts/cat.js и новый cat-renderer.js, cat_portrait.html/cat.html (только подключение), static/css/cat.css; релевантные tests/test_cat.py, tests/test_cat_browser.py, tests/test_cat_pixels.py/новый renderer browser test; docs/evidence/CAT09/implementation.md и обезличенные изображения/snapshot. Исторические генераторы/157PNG/read-only, новые мастера/read-only, models/services/deps/.gitignore/read-only. Root отдельно ведёт ARCHITECTURE/PLAN/STATE/prompt/review. Не коммитить до accepted и ограниченного follow-up.

## Приёмка и проверки

Root увидит3характера на360/1440 в игре/профиле и узнает в них CAT08, а не CAT07. Для7поз canvas pixels должны изменяться, особенно отдельно head/tail и выражения; проверять пиксели, не только data-pose.48×48canvas, ограниченная palette/alpha0/255; screenshot physical blocks uniform приDPR1/1.25/2. Все игрушки помещаются, нет швов/оторванных частей/обрезки. Профиль/idle до Start/paused/calm/reduced/hidden не меняют canvas; active игры меняют. Несколько раундов и persistence работают без browser/networkerrors. Проверить noJS fallback и failed image не ломает игру. Не ослаблять существующие проверки без замены эквивалентным наблюдаемым контрактом.

Ruff/format/JSsyntax и focused smoke выполняет исполнитель; затем source freeze и root запускает полный релевантный PostgreSQL/browser suite на отдельной БД. Не дублировать широкий browser suite. Старые PNG тесты можно сохранить как historical; текущие canvas свойства доказать real browser. Taste Skill прочитать и применить; подготовить sanitized Django snapshot для Taste shoot/gate, path canonical /private/tmp во избежание ошибки CAT07. Никаких настоящих CSRF/session/password в screenshots/docs. Исполнитель не принимает сам результат.
