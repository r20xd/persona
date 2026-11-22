# CAT11 — более частые прогулки

- Kind: software, существующий личный кабинет persōna. Taste skill применяется к изменению поведения анимации; палитра/разметка/спрайты прежние.
- Запрос: «продолжи и сделай так чтобы коты появлялись чаще».
- Исполнитель: прежний `/root/cat01`, явно созданный gpt-6.1-sol/low, один writer без делегации.
- Требования: PRD-02/03/04, TECH-03/06, SEC-01; дополнительная функция CAT10, контракт ARCHITECTURE §32 CAT11 и PLAN CAT11.
- Предпосылки: CAT10 accepted49tests, commit9e183d9; doc-only merge AG01 архивная-версия. Основной сайт локально8000. Чужие `.gitignore` и untracked фотографии не трогать.

## Контекст и файлы

Прочитать AGENTS.md, TASK.md, ARCHITECTURE §32, PLAN CAT11, актуальный Taste SKILL.md `/Users/local-user/.codex/plugins/cache/taste-skill/taste-skill/2.5.1/skills/taste-skill/SKILL.md` и motion reference. Read-only: renderer, cat/profile/templates/models/config, CAT10 evidence, tests/ui_qa.py. Разрешено менять только `apps/accounts/static/accounts/cat-cameo.js`, `tests/test_cat_cameo_browser.py`, создавать `docs/evidence/CAT11/implementation.md`. Никаких схем/зависимостей/наград/новых endpoints.

## Контракт

1. Первый выход3–6секунд, повтор20–40секунд start-to-start. Прежние duration6–9секунд, randomrun/hop/character/click unchanged.
2. Версионировать только nextkey: `persona.cat.walk.${owner}.v2.next`; enabledkey прежний. Старый `.next` не должен откладывать появление, прежний disabled остаётся disabled. Не очищать посторонний localStorage.
3. Close/Escape видимого кота назначает новый20–40секунд срок, затем hide/schedule. Naturalend сохраняет ранее назначенный start-to-start срок. Все guards/cleanup/memory fallback неизменны.
4. Навигация не сбрасывает будущий срок. Подавление ввода/диалогов/hidden/reduced сохраняется. Не ускорять renderer/не добавлять таймеры опроса.
5. Обновить реальные Playwrightclock проверки: не ждать старые20секунд после навигации наудачу; проверять именно сохранённый срок, затем advancing его. Helper должен читать точный новый ключ, старый `.next` может сосуществовать. Добавить смысловые проверки старого длинного срока→новый первый выход, сохранённого optout, новой паузы после долгого открытого облачка/close/Escape и границ первого/повторного интервала. При необходимости параметризовать без дублирования сценариев.

## Приёмка и проверки

Критерии1–5 подтверждены фактическим diff и browsertests на360/1440. Имеющиеся игры/профиль/аутентификация не меняются. Выполнить JSsyntax и Ruff/format изменённых Python. Root запустит focused cameo server/browser + sharedshell tests на временной PostgreSQL и посмотрит реальные кадры. Не запускать свою БД/большой suite, не делать commit/push/deploy. Отчёт: фактические изменения/команды/ограничения. Root пишет review, STATE и versioning. Вопросов по контракту нет.
