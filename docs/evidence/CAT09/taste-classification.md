# Taste — классификация текущего snapshot

**GATE: OPEN 33 (rounds used up)**. Полные данные: taste-gate.txt, taste-gate-summary.json, taste-consistency-report.json. Gate:33открытых FAIL/31WARN после дедупликации; raw consistency:42FAIL/33WARN. Formal waivers:0, kit не менялся. Для ограниченного visual patch существующего кабинета задан1автоматический review round после двух ручных визуальных исправлений; это OPEN, не PASS и не site-wide приёмка. Итоговая оптимизация веса ассетов и её perf фиксируются отдельно.

Тип — gaming внутри рабочего кабинета. Сохранены палитра persōna, текущие UI/шрифты/радиусы/навигация и главная кнопка «Начать сборы». Изображения — собственные CAT08 мастера, игрушки проекта; сторонние фотографии и новые факты/названия/контакты не добавлялись. Shader/3D отсутствуют, живой moment — персонаж. Голос — короткие добрые русские реплики без штрафов; прежние тексты сохранены. Snapshot обезличен и не доказывает POST; live tests отдельные. Perf первого варианта потребовал реального исправления веса изображений — prompt-performance.md, без объявления прежнего FAIL успешным.

## Все открытые FAIL

| № | Check | Место | Решение/причина в границах CAT09 |
| --- | --- | --- | --- |
| 1 | hero-fill | main#main > div.cat-layout > section.cat-companion "Пиксель" | Рабочая игра сразу показывает питомца и управление; fullscreen marketing hero не входит в задачу. |
| 2 | row-gap | section#cat-wardrobe > form.cat-settings > button.button.button-primary "Сохранить кота" | Существующая кнопка формы на desktop занимает левую колонку; это не новая ошибка renderer. |
| 3 | card-layout | section#cat-wardrobe > div.cat-unlocks "Клубок Открыто" | Четыре однотипные игрушки — одна функциональная коллекция, единый шаблон намеренный. |
| 4 | cta | main#main > h1 | Начать сборы — реальная кнопка в игровой панели, а не CTA в заголовке. |
| 5 | focus-ring | main:focus | Существующий main:focus в workspace.css не менялся; замечание остаётся открытым для отдельного a11y-review. |
| 6 | moment-none | (the page) | Новый moment — анимированный игровой персонаж; маркетинговый dealt section не добавлялся. |
| 7 | hero-screen | main#main > p.overline "МАЛЕНЬКИЙ ПЕРЕРЫВ МЕЖДУ ПАРАМИ" | Заголовок кабинета не является отдельной полноэкранной секцией; прежняя раскладка сохранена. |
| 8 | hero-screen | main#main > h1 "Кот в рюкзаке" | Заголовок кабинета не является отдельной полноэкранной секцией; прежняя раскладка сохранена. |
| 9 | section-height | main#main > p.account-intro "20 секунд, три вещи и один очень самосто" | Формы/игровые панели имеют высоту по содержимому, не маркетинговые экраны. |
| 10 | section-height | section#cat-wardrobe "ЛИЧНЫЕ КОШAЧЬИ ДЕЛАИмя, характер и игруш" | Формы/игровые панели имеют высоту по содержимому, не маркетинговые экраны. |
| 11 | section-air | main#main > h1 "Кот в рюкзаке" | Плотность существующего кабинета сохранена; отдельный h1/intro не считается feature section. |
| 12 | section-air | main#main > p.account-intro "20 секунд, три вещи и один очень самосто" | Плотность существующего кабинета сохранена; отдельный h1/intro не считается feature section. |
| 13 | one-section | main#main > div.cat-layout "{"character": "chaos", "source": "/stati" | Две рабочие панели намеренно видны вместе на desktop; быстрое начало игры важнее screen-per-section. |
| 14 | one-section | h2#wardrobe-title "Имя, характер и игрушки" | Две рабочие панели намеренно видны вместе на desktop; быстрое начало игры важнее screen-per-section. |
| 15 | one-section | section#cat-wardrobe "ЛИЧНЫЕ КОШAЧЬИ ДЕЛАИмя, характер и игруш" | Две рабочие панели намеренно видны вместе на desktop; быстрое начало игры важнее screen-per-section. |
| 16 | one-heading | h2#game-title "Что берём в рюкзак?" | Имя питомца и заголовки игры/формы семантически различны и остаются видимыми вместе. |
| 17 | one-heading | h2#wardrobe-title "Имя, характер и игрушки" | Имя питомца и заголовки игры/формы семантически различны и остаются видимыми вместе. |
| 18 | container-edges | header.account-header "persōnaЦифровой деканат Мой профиль Выйт" | Шапка, sidebar и внутренние отступы рабочих карточек сохранены; это не одноосный landing. |
| 19 | container-edges | section#cat-wardrobe "ЛИЧНЫЕ КОШAЧЬИ ДЕЛАИмя, характер и игруш" | Шапка, sidebar и внутренние отступы рабочих карточек сохранены; это не одноосный landing. |
| 20 | container-edges | main#main > div.cat-layout "{"character": "chaos", "source": "/stati" | Шапка, sidebar и внутренние отступы рабочих карточек сохранены; это не одноосный landing. |
| 21 | container-edges | a.skip-link "К содержимому" | Шапка, sidebar и внутренние отступы рабочих карточек сохранены; это не одноосный landing. |
| 22 | container-edges | aside.workspace-sidebar "persōnaЦифровой деканат Ваше пространств" | Шапка, sidebar и внутренние отступы рабочих карточек сохранены; это не одноосный landing. |
| 23 | container-edges | section.cat-play > div.cat-game-heading > div > p.overline "СБОРЫ НА ПАРУ" | Шапка, sidebar и внутренние отступы рабочих карточек сохранены; это не одноосный landing. |
| 24 | container-edges | h2#game-title "Что берём в рюкзак?" | Шапка, sidebar и внутренние отступы рабочих карточек сохранены; это не одноосный landing. |
| 25 | container-edges | main#main > div.cat-layout > section.cat-play "СБОРЫ НА ПАРУЧто берём в рюкзак?20 с Лов" | Шапка, sidebar и внутренние отступы рабочих карточек сохранены; это не одноосный landing. |
| 26 | row-lines | div#id_toys "Клубок Мячик Игрушечная мышка Игрушечная" | Вложенная checkbox group имеет собственные внутренние отступы; сохранена native форма. |
| 27 | nav | header.account-header > div.header-inner > div.mobile-brand > a.brand "persōna Цифровой деканат" | Существующий двухстрочный бренд и компактная шапка сохранены; навигация работает в live tests. |
| 28 | no-visual | main#main > div.cat-layout > section.cat-companion "Пиксель" | Canvas-питомец/игра/формы являются продуктовым UI, не feature sections с 25% photograph coverage. |
| 29 | no-visual | main#main > div.cat-layout > section.cat-play "Что берём в рюкзак?" | Canvas-питомец/игра/формы являются продуктовым UI, не feature sections с 25% photograph coverage. |
| 30 | no-visual | section#cat-wardrobe "Имя, характер и игрушки" | Canvas-питомец/игра/формы являются продуктовым UI, не feature sections с 25% photograph coverage. |
| 31 | cta | main#main > p.account-intro | Начать сборы — реальная кнопка в игровой панели, а не CTA в заголовке. |
| 32 | hero-fill | main#main > div.cat-layout > section.cat-play "Что берём в рюкзак?" | Рабочая игра сразу показывает питомца и управление; fullscreen marketing hero не входит в задачу. |
| 33 | container | page | Django workspace использует свои контейнеры, не класс .wrap; геометрия проверена live. |

## Все сохранённые WARN

| № | Check | Место | Почему оставлен |
| --- | --- | --- | --- |
| 1 | flush | section.cat-play > div.cat-game-heading > div > p.overline "СБОРЫ НА ПАРУ" | Сохранены отступы рабочих карточек, не стыки маркетинговых секций. |
| 2 | flush | main#main > div.cat-layout > section.cat-play > p.account-note "Без ежедневных заданий: кот рад вам в лю" | Сохранены отступы рабочих карточек, не стыки маркетинговых секций. |
| 3 | flush | section#cat-wardrobe > div:nth-of-type(1) > p.overline "ЛИЧНЫЕ КОШAЧЬИ ДЕЛА" | Сохранены отступы рабочих карточек, не стыки маркетинговых секций. |
| 4 | copy-headline | main#main > h1 "Кот в рюкзаке" | Сохранено пользовательское название игры; категорию и аудиторию задаёт кабинет. |
| 5 | heading-scale | h2#cat-name "Пиксель" | Имя кота и заголовок панели имеют разные роли; текущая иерархия сохранена. |
| 6 | off-grid | h2#cat-name "Пиксель" | Внутренние отступы двухколоночных карточек сохранены. |
| 7 | off-grid | h2#game-title "Что берём в рюкзак?" | Внутренние отступы двухколоночных карточек сохранены. |
| 8 | off-grid | h2#wardrobe-title "Имя, характер и игрушки" | Внутренние отступы двухколоночных карточек сохранены. |
| 9 | section-gaps | main#main > div.cat-layout > section.cat-companion / main#main > div.cat-layout > section.cat-play | Соседние рабочие панели стоят в grid, не перекрываются; live canvas/layout tests прошли. |
| 10 | section-gaps | main#main > div.cat-layout > section.cat-play / section#cat-wardrobe | Соседние рабочие панели стоят в grid, не перекрываются; live canvas/layout tests прошли. |
| 11 | links | aside.workspace-sidebar > div.sidebar-brand > a.brand "persōna Цифровой деканат" | Изолированный статический snapshot не содержит Django routes; реальные переходы проверены отдельно. |
| 12 | links | aside.workspace-sidebar > nav.campus-nav > a:nth-of-type(2) "Расписание" | Изолированный статический snapshot не содержит Django routes; реальные переходы проверены отдельно. |
| 13 | links | aside.workspace-sidebar > nav.campus-nav > a:nth-of-type(3) "Успеваемость" | Изолированный статический snapshot не содержит Django routes; реальные переходы проверены отдельно. |
| 14 | links | aside.workspace-sidebar > nav.campus-nav > a:nth-of-type(4) "Заявки" | Изолированный статический snapshot не содержит Django routes; реальные переходы проверены отдельно. |
| 15 | links | aside.workspace-sidebar > nav.campus-nav > a:nth-of-type(5) "Студенты" | Изолированный статический snapshot не содержит Django routes; реальные переходы проверены отдельно. |
| 16 | links | aside.workspace-sidebar > nav.campus-nav > a:nth-of-type(6) "Кот в рюкзаке" | Изолированный статический snapshot не содержит Django routes; реальные переходы проверены отдельно. |
| 17 | links | aside.workspace-sidebar > nav.campus-nav > a:nth-of-type(7) "Помощник" | Изолированный статический snapshot не содержит Django routes; реальные переходы проверены отдельно. |
| 18 | links | aside.workspace-sidebar > nav.campus-nav > a:nth-of-type(8) "Уведомления" | Изолированный статический snapshot не содержит Django routes; реальные переходы проверены отдельно. |
| 19 | label-centre | aside.workspace-sidebar > nav.campus-nav > a:nth-of-type(6) "Кот в рюкзаке" | Текущая подпись ссылки согласована с иконкой sidebar; навигация не менялась. |
| 20 | one-screen | main#main > div.cat-layout > section.cat-companion "Пиксель" | Рабочие панели не расширяются до fullscreen. |
| 21 | font-load | main#main > h1 "Inter" | Существующий fallback font stack не менялся; загрузка нового шрифта не требуется для котов. |
| 22 | skip-link | a.skip-link "К содержимому" | Первый Tab действительно ведёт на существующую ссылку «К содержимому» → #main; эвристика ожидает иной текст/#top. |
| 23 | page-meta | head "Кот в рюкзаке · persōna" | Приватный noindex кабинет, существующие metadata не расширялись. |
| 24 | share-meta | head | Приватный noindex кабинет не предназначен для social sharing; существующий head сохранён. |
| 25 | form-fields | header.account-header > div.header-inner > div.header-actions:nth-of-type(2) > form | Сохранена серверная native форма/ошибки; cat name не является ФИО для autocomplete=name. POST проверен live. |
| 26 | form-fields | input#id_name | Сохранена серверная native форма/ошибки; cat name не является ФИО для autocomplete=name. POST проверен live. |
| 27 | form-fields | section#cat-wardrobe > form.cat-settings | Сохранена серверная native форма/ошибки; cat name не является ФИО для autocomplete=name. POST проверен live. |
| 28 | section-air | main#main > div.cat-layout / section#cat-wardrobe | Плотность существующего кабинета сохранена; отдельный h1/intro не считается feature section. |
| 29 | nav | div.header-inner > div.header-actions > form > button.button.button-quiet "Выйти" | Существующий двухстрочный бренд и компактная шапка сохранены; навигация работает в live tests. |
| 30 | orphan | main#main > p.account-intro "20 секунд, три вещи и один очень самосто" | Существующий русский intro и переносы сохранены. |
| 31 | copy-em-dash | (the copy) | Три тире в существующих русских репликах/подписях оставлены; тексты не переписывались ради лимита2. |

Инструмент сообщил PASS для assets/empty-visual, spill/off-viewport, collide/tap-size, контраста и видимости контента. Его формы/reduced-motion/hover и часть scroll-walk не проверялись; границы записаны в JSON. Реальный game/profile, POST, reduced/calm/pause/hidden, размеры360/1440 и DPR1/1.25/2 проверяются отдельным suite. Эти границы не заменяются формальным waiver.
