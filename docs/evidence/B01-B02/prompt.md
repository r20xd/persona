# B01–B02 — постановка и контекст

Пользователь одобрил V1: «визуально все пока нравится, цветовая палитра хорошая, а название в случае чего переделаем ближе к концу. продолжай делать». Палитра/компоновка приняты, название рабочее.

Основной агент gpt-6.1-sol/high передал accounts исполнителю gpt-6.1-sol/low с отдельным контекстом (fork_turns=none): реализовать StudentProfile/OperatorScope, минимальные Faculty/Program/StudyGroup, миграции, безопасный вход/выход с DB sessions/Argon2/CSRF, Axes 10 ошибок за 15 минут на username+IP, личный профиль и начальные реальные страницы по ролям. Preview сохранить отдельной демонстрацией. Пароли provisioning получать только через окружение/интерактивный ввод, повторный запуск не меняет данные и пароль.

Разрешённая область: apps/accounts/, apps/academics/, config, tests, pyproject/lock для django-axes, отдельный accounts.css, README/.env.example и implementation.md этого этапа. Родитель владеет STATE/PLAN/ARCH/AGENTS, дизайном и review. Никаких публичных admin/регистрации/смены паролей, SQLite, реальных данных, private SSH reads, recursive delegation и commit до review. Обязательное соавторство — команда persōna <noreply@persona.example>.

Приёмка: два профиля изолированы, роли ограничены, внешний next и X-Forwarded-For не обходят защиту, CSRF/POST logout/деактивация работают, Axes security tests не отключают механизм. Реальная PostgreSQL-проверка обязательна для полного закрытия этапа; mock не считается её заменой.

Среда: Docker socket недоступен даже после штатной escalation; sudo -n требует интерактивной аутентификации. Пароль sudo не запрашивался. Пользователю асинхронно предложено проверить docker info в новом WSL-терминале; код и независимые проверки продолжаются. Публичный API GitHub для статусов CI вернул rate limit exceeded; успешный CI не заявлен.
