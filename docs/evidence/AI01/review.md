# AI01 — независимое ревью

**accepted локально** как готовый чат с отключённым по умолчанию API и серверным адаптером для последующего подключения пользователем. Реальная инференция без доступа не проверялась, фиктивные ответы не подменяют API.

Root прочитал assistant.py, settings/envexample, urls/nav, JS/template и целевые tests. Active student gate own_profile/login, CSRF/nativePOST/no-store; история ограничена12сообщениями и owner текущего пользователя, clear толькоPOST. Только typedmessages/context этого чата идут провайдеру; кабинетные данные не добавляются. Успех добавляет валидную паруuser/assistant и PRG, ошибка оставляетdraft и прежнююисторию. Ключ только serverenv/Authorization, не HTML/JS/session, upstreamerrors очищены. URL HTTPS/loopbackHTTPdev, redirects запрещены,10stimeout/read1MiB/reply8000/input2000/max_completion_tokens600; контракт проверен по официальной документации, ссылка imagegen.md. История не обещает сохранение после logout.

Root просмотрел screenshot360/1440: локальный сгенерированныйpixelrobot сочетается с палитрой кота/бренда, форма/стартеры/статусы доступны,8пунктов мобильной навигации помещаются в4×2. Pendingтекст нейтральный «Отправляем вопрос», не заявляет инференцию до подключения. Простые формы работают безJS; JSпоказываетloading, не отправляет ключи из браузера. Никаких новых зависимостей/моделей/миграций. Пользовательские .env/.gitignore не менялись исполнителем; существующее изменение .gitignore исключается изкоммита.

## Независимые проверки после freeze

PostgreSQL17/Chromium: `tests/test_assistant.py tests/test_assistant_browser.py tests/test_design_browser.py` — **29passed,1existingwarning,49.95s**. Проверены disconnected/nooutbound/nofakereply/draft, stubsuccess/error/contextcap/clear, studentisolation/forgedowner/CSRF/methods/roles/XSS, URLboundary, HTTPrequestcontract/redirect/timeout/oversize/malformed/secretleakguard, browser360/1440 и общийdesign360/390/768/1440/narrow. Настоящих платных запросов не было. Ruff/diffcheck passed; warning — прежняяpytestfixture.

НастройкаAPI и полный перезапуск процесса с загруженным.env описаны вREADME. Пользователь добавитпровайдера/модель позже; поддержку иных протоколов адаптер не обещает. Taste применён к рабочему кабинету поархитектуре20; маркетинговыйgate не запускался/PASS не заявлен. Образ/промпт/путь — imagegen.md. Публичной публикации нет.
