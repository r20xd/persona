# CAT10 — прогулки выбранного кота

- Пользователь: «сделай так чтобы выбранный кот иногда пробегал или прыгал на случайной вкладке и на него можно было нажать».
- Исполнитель cat01, Sol/low, один writer без субагентов. Связь: PRD-02/03/04/05, TECH-03/06, SEC-01 и пользовательский CAT10.
- Прочитать AGENTS/TASK, ARCHITECTURE §32 и CAT09 §31, PLAN CAT10 и актуальный Taste Skill. Реальный skill: /Users/local-user/.codex/plugins/cache/taste-skill/taste-skill/2.5.1/skills/taste-skill/SKILL.md.
- Исходная main18c41e2; пользовательские .gitignore/untracked исходники/evidence других этапов не менять.

## Наблюдаемый результат

На home/schedule/session/grades/requests/notifications/students иногда пробегает/подпрыгивает именно собственный выбранный48pixelкот. Нажатие останавливает, радует кота и показывает реплику/«К коту»/скрыть/отключить. Появления редкие, не на каждой навигации; интервал сохраняется между страницами. Первая через8–18секунд, повтор90–180секунд. Точные случайные значения — engineering choice, не конкурсное требование. Cat/profile/login/operator/редакторы/создание заявки/чат не получают автопрогулку. На cat settings добавить локальный checkbox включения прогулок вне server POSTформы, чтобы отключение было обратимым. Никаких наград/психотипов/API/моделей.

## Технический контракт

Контекст-процессор только для активного student/GET и whitelist routes, own StudentProfile/StudentCat по request.user.pk. Один select_related LEFT JOIN по возможности: StudentProfile.select_related('studentcat'), catch missing cat→default, отсутствует profile→нет cameo. Отдать только безопасную presentation projection; не чужую карточку, не ORM/queryset в HTML. Opaque owner key для local preference/schedule (например salted_hmac от собственного user.pk, не SECRET_KEY/служебный ключ). Не записывать вstorage ФИО/имя/характер/учебные данные, только bool/время. Между разными аккаунтами настройки разделены. GET не создаёт cat. Не добавлять endpoints/модели/deps.

Переиспользовать CAT09 renderer/малыеPNG. На eligible странице единственный #cat-renderer-config и renderer node; на cat/profile cameo отсутствует, game/profile существующие scripts не дублируются. Cat-route получает только config для toggle; не ломать existing game. Отдельный CSS/JS cameo, базовый шаблон подключает условно. Global pointer-events:none, кликабельная только маленькая button/облачко. RAF/timer movement физически меняет координаты, run/hop отличаются, не просто data attributes. Изображение отражается по направлению, step/canvaspixel smoothing не теряется. Кот внутри viewport с учётом mobile nav/safe area, контент/скролл вне кота доступны.

Не перехватывать фокус при появлении. Focus/hover останавливают движение, click/Enter/Space открывают реакцию/облачко с44pxконтролами. Esc/close скрывают, при закрытии собственного сфокусированного элемента корректно вернуть фокус. После естественного завершения скрыть; не оставлять вечный animation timer. Hidden/reduced-motion/input-editing/dialog suppress/hide; pagehide очищает timers/RAF, BFcache/resize корректны. Storage errors не ломают основной UI. На320/360не должно бытьoverflow и перекрытия mobile nav, не запускать на формах отправки заявок/редакторах.

## Владение файлами

Разрешены новый apps/accounts/context_processors.py (или узкий cameo module рядом), config/settings/base.py только регистрация processor, apps/accounts/templates/accounts/base.html только conditional cameo include, новые cameo partial/CSS/JS, cat.html только toggle control, cat.py только presentation helper если нужен, cat-renderer.js только действительно необходимый совместимый reuse (предпочтительно без изменения), релевантные новые tests/test_cat_cameo.py и tests/test_cat_cameo_browser.py; docs/evidence/CAT10/implementation.md и sanitized screenshots/snapshot. Root ведёт ARCH/PLAN/STATE/prompt/review. Assets/renderer rig/game/controller/server rewards/deps/migrations/остальные UI read-only. Не редактировать пользовательские файлы/.env и не запускать userdaemon. До accepted не commit/push.

## Проверки

Unit/PostgreSQL: два аккаунта с разными cats, eligible GET содержит только собственный, прямой переход к чужому каталожному профилю не подменяет own cat; guest/operator/no-profile/excluded routes не получают payload/assets; GET сохраняет counts/записи, no new writes; конфигурация не раскрывает User/private data. Query overhead ограничить и проверить, если выбранный подход может вызвать deferred-field N+1.

Real browser deterministic random + clock (без production debug query/button): дождаться показа/движения на360/1440, обе траектории, собственные name/character, клик/клавиатура и joy/реплика/переход, close/Escape/focus/44px, shared cooldown при navigation/reload, disable/re-enable checkbox на cat, reduced/hidden/typing suppression, storage failures, resize/BFcache cleanup, вне элемента pointer-events пропускают клики. Профиль/игра остаются прежними, без double-renderer. Сохранить живые screenshots. Tests должны проверять canvas/координаты/реальные действия, не только marker attributes. Не добавлять медленные ожидания90сек, использовать virtual clock. Root запускает широкий targeted suite после source freeze; исполнитель smoke/Ruff/JS и визуальный первый screenshot. Не дублировать broad suite. Подготовить обезличенный rendered snapshot для Taste shoot/check, canonical /private/tmp, без настоящего CSRF/session/password. Не объявлять непроверенные результаты PASS.

Сообщить source freeze до длительных проверок, root выполнит независимое review. Commit/push только по ограниченному follow-up, required coauthor trailer по AGENTS.
