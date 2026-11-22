# U05 — фаза A, фактический дизайн-аудит до изменений

Приложение не изменялось. База: архивная-версия. Палитра U04 и пользовательский colors.jpg сохранены. Использованы Taste Skill2.5.1, references/system.md, layout-v4.md и copy-voice.md. Это личный кабинет, поэтому рекомендации по визуальной системе применимы, маркетинговая структура не является целью.

## Что действительно выполнено

Собственная QA PostgreSQL17.11 из pinned local-compose image digest839fbb5a4942a7758dd93e18b42ea5649807491a0545b5eeeb8f0b8bb11857a5. Private state0600 записан до Docker mutation. Volume и network явно именованы и имеют owner labels; verified unique attachment/endpoint принадлежит только ownCID. Собственная БД с fictional seed_demo anchor2026-11-11, собственный STATIC_ROOT, Gunicorn на dynamic loopback port. ready и SELECT1 успешны. Никаких dev5432/8000, host mounts, prune, .env или SSH-ключей.

В живом Chromium156 через обычный вход сняты login/home/local-user/grades/schedule/session/requests/notifications/operator на360/1440; 22 BEFORE PNG в before/, затем два снимка реального keyboard focus. Это новые снимки текущего приложения, не U04 reuse. По одному compact notice проверено на страницах студента.

Sanitized rendered home.html/login.html сохранялись только в private /tmp вместе с public static. Все hidden input values, включая CSRF и digest tokens, очищены; password values пустые. Cookies/учётные данные не переносились. Состояние filter enhancement нормализовано перед повторным исполнением локального filters.js, чтобы не дублировать подсказки. Checker-generated rendered.html после выполнения перенесены обратно в private /tmp: HTML/env в evidence отсутствуют. Проверено отсутствие известных QA credentials в текстовых evidence. Снимки не доказывают серверные действия; browser login и keyboard walk выполнялись отдельно на live app.

## Настоящие Taste scripts и результаты

Node22.22.1, CHROME_PATH=/tmp/deanery-browsers/chromium-1248/chrome-linux64/chrome. Скрипты не модифицировались. Каждый scanner запускался последовательно и в собственном Chrome profile. Для обоих consistency: --root private/public, --widths1440,360, --quick, --page software, --category «Личный кабинет студента», --primary «Заказать справку»/«Войти в кабинет», --out соответствующий before-taste-*.

| Запуск | Фактический результат | Raw evidence |
| --- | --- | --- |
| consistency home | exit1, 55FAIL/34WARN, 74.06s | before-taste-home/report.json, console.txt, crops, invocation.json |
| consistency login | exit1, 21FAIL/10WARN, 47.15s | before-taste-login/report.json, console.txt, crops, invocation.json |
| perf home, widths1440/360, runs3 | exit0, PASS, 0FAIL/0WARN, 27.04s | before-taste-perf/report.json, console.txt, invocation.json |

Агрегат — audit-summary.json. Counts сохранены без удаления нерелевантных находок. GATE PASS не заявляется, GATE OFF не используется вместо аудита.

Quick явно не проверяет: stepped scroll-linked; reveal walk (IntersectionObserver отдельно читается); hover-spill; hidden-visual; loop-pause; forms; reduced-motion; dead-IntersectionObserver walk; hover-move. Эти ограничения есть в raw report.notChecked. Hidden content проверяется quick-методом со scripts off и reduced motion, но это не полноценная проверка reduced-motion поведения. Scanners не являются полным live функциональным прогоном.

Perf статического снимка:1440 —16.5KiB,9requests,FCP/LCP median40/40ms;360 —16KiB,8requests,FCP/LCP36/36ms. На обеих ширинах CLS0.000, blocking0ms, long tasks0, broken requests0,3parsedJSfiles/3.4KiB, CSS7.6KiB, внешних шрифтов/изображений нет. Это local snapshot/CPU relative measurements, не production/server latency или field web vitals. Визуальный редизайн должен сохранить этот небольшой вес.

## Применимые проблемы и приоритеты

1. **Иерархия главной.** На360 первый экран занят заголовком, действиями и длинным radar; ближайшее событие находится ниже. Alerts, отдельный блок изменений и digest имеют одинаковый визуальный вес, повторяя часть контекста. Нужен компактный верхний блок ближайшего события и времени/места, далее приоритеты и полная новая сводка, затем спокойные краткие списки. Не скрывать неподтверждённые digest items или ack за общим collapse.
2. **Общий shell и равные края.** Taste1440 измеряет header left360px при main left254px. Header использует другой контейнер, чем рабочее содержимое. У приложения слева законная sidebar200px: это объясняет часть scanner asymmetry, но header/main misalignment реальна. Нужны общий frame/gutter и общий header partial, единая navigation и predictable account controls.
3. **Размеры и типографика.** Live360 показывает overline9px, nav10px, многие кнопки12px, основной текст14px. Крупные одинаковые заголовки/рамки карточек создают однообразие; семантика time/title/status недостаточно различается. Ввести явную шкалу: основной16px, readable labels/metadata12–14px, отдельные уровни page/section/row headings и сильный nearest-event time. Не подгонять важный текст уменьшением шрифта.
4. **Controls и tap targets.** Taste на360/320 отмечает profile82×39/65×39 и request title link225×17. Native серые logout/filter/status buttons визуально расходятся с primary. Сохранить реальные формы, фокус, ошибки и U04autoGET; оформить единые primary/secondary/text controls, минимум44px для отдельных действий и predictable field sizing. Контраст рамок/текста U04 уже сохранён, его не снижать.
5. **Вход.** Taste1440 empty-area61% в story и51% в panel; live screenshot подтверждает большой пустой navy блок и generic copy «Меньше поиска. Больше ясности». Логин должен прямо объяснять кабинет студента и давать компактную уверенную форму. Brand focus на navy имеет **2.82:1**: исправить светлым focus token на тёмных surfaces. Поля/label/demo instructions и одна concept notice остаются.
6. **Карточки и списки разделов.** Сохранить data/actions, но различить document status/history, discipline results, lesson time/place и notification events собственными хорошо связанными row layouts. Общие surface/border/radius/spacing, без рамки вокруг каждого фрагмента и без новых декоративных нефункциональных controls. На mobile одна колонка и читаемая навигация; unicode symbols заменить последовательными собственными SVG в рамках существующей системы.

## Что нельзя механически считать дефектом кабинета

- hero-fill/hero-screen/section-height/one-section/one-heading/section-air/cta/no-visual/card-visual/text-only/moment-none: scanner требует marketing fullscreen sections, photographs/effects и CTA. В кабинете реальные данные и быстрые действия важнее. Не добавлять hero100svh/изображения/эффекты ради снятия FAIL. Empty-area на login имеет самостоятельную визуальную ценность и приведена выше.
- Часть container-edges/off-grid/flush — следствие проверок landing .wrap/одной полноширинной колонки: sidebar и двухколоночные рабочие карточки допустимы. Общий header/main контейнер всё же исправить.
- heading-scale ругает крупные счётчики/время относительно h2: это не автоматическая ошибка dashboard, но новая шкала должна делать значение цифры понятным.
- Links404 в snapshot ожидаемы: private root содержит HTML snapshots и public static, не Django routes. Формы/серверные действия в таком окружении не подтверждаются. Не менять рабочие href или POST ради snapshot scanner.
- Русский skip-link ошибочно распознан как «не skip link», несмотря на «К содержимому» первым Tab stop. Copy-headline «0words/no category» также демонстрирует языковые/маркетинговые ограничения. Это не основание менять русский интерфейс на английский.
- page/share meta полезны для публичного маркетинга; private noindex app не требует OG image/social copy. Не добавлять шум ради WARN.

## Отдельно проверенные focus-visible FAIL

Home checker отметил невидимый focus для desktop Tab18 «Открыть расписание события» и Tab23 «Справка об обучении ·11ноября». Выполнен настоящий live Tab walk33 с550ms settle на1440; оба элемента видимы и centerHit=true (top453.94/bottom470.94 и453.11/470.11). Evidence before-live-focus.json и before/focus-live-*.png. Это не подтверждённая потеря фокуса; вероятна зависимость scanner от timing smooth scroll. В redesign лучше избегать ненужной smooth scrolling и повторить focus checks. Login brand contrast2.82:1 остаётся применимой находкой.

## Передача root

ФазаA завершена; до follow-up приложение не менялось. OwnQA остаётся для фазыB/root проверки; state /tmp/u05-qa-state.json, helper /tmp/u05-qa.py, private snapshots/public root внутри state.private. Root принимает конкретное направление перед реализацией. Commit/push/deploy не выполнялись.
