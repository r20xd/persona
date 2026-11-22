# U02/F01/A03 — ревью

Статус: accepted для визуального preview и конфигурации CI. Пользовательская оценка V1 ожидается; полные F01 (HTMX) и A03 (успешный удалённый pipeline) не объявляются завершёнными.

Основной агент gpt-6.1-sol/high прочитал код preview, настройки/маршруты, shell launcher, шаблоны, CSS, CI и тесты. Независимо выполнил locked sync, Ruff lint/format, Django check и 30 foundation/preview тестов — успешно. Реальный production subprocess подтвердил 404 обоих preview-маршрутов. Поля входа disabled; нет формы отправки, данных БД и ложного сохранения.

Браузерная проверка родителя: PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest tests/test_preview_browser.py --browser-channel chromium — 2 passed на 360/1440. Первая попытка без browser-path дала отсутствие executable; после указания реального каталога прошла. Есть предупреждение pytest-playwright о будущей несовместимости fixture с pytest10; текущий lock использует pytest9.

Просмотрены реальные dashboard-desktop-1440.png и dashboard-mobile-360.png: цельная композиция, читаемые карточки, mobile одна колонка и нижняя навигация. Фиксированная навигация на full-page screenshot остаётся на границе исходного viewport — это артефакт полноразмерного снимка, не горизонтальное переполнение. Есть также скриншоты входа.

CI сконфигурирован с отдельным PostgreSQL17 и тестовыми временными доступами; успешный remote run пока не проверен. Локальный Docker socket недоступен даже при штатном escalation; системные права не менялись. UI review не заменяет DB-тесты и настоящее ядро кабинета.

История моделей достоверна: первая часть preview начата sol/medium, завершение и проверки исполнителя — sol/low; родитель Sol/high. Новые коммиты должны содержать обязательное соавторство, local hook включён. Для просмотра после завершения QA запустить bash scripts/preview.sh по README; QA-серверы остановлены, публичного размещения нет.
