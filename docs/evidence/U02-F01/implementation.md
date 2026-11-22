# U02/F01/A03 — результат исполнителя

Дата: 4 ноября 2026. Начал прежний исполнитель **gpt-6.1-sol/medium**,
закончил новый исполнитель **gpt-6.1-sol/low** по поручению основного агента.
Родитель ведёт постановку, дизайн-документ и независимое ревью отдельно.
Субагенты исполнителем не запускались, сайт не публиковался.

## Что сделано

- Локальная Django-страница `/preview/` и отключённый макет входа
  `/preview/login/`: главная, фиктивное расписание, сводка учёбы, пример заявки,
  объявления и профиль. PRD-02–04, BRAND-01, DATA-01; это визуальная основа,
  **не выполненные CORE-01–05**.
- Собственные CSS/SVG, системные шрифты, видимый focus, skip link,
  текстовые статусы, disclosures с честными пояснениями будущих сценариев.
  Широкий sidebar заменяется нижней навигацией на телефоне.
- Preview разрешён local/test/preview настройками. Production по умолчанию
  запрещает его и возвращает 404. Вход не принимает пароль: disabled inputs,
  нет формы и отправки. POST к preview отклоняется. Запросы к БД отсутствуют.
- `scripts/preview.sh` запускает Gunicorn только на `127.0.0.1:8000`,
  отклоняет аргументы, не требует миграций/БД. README объясняет режим и ограничения.
- Реальный `uv.lock` обновлён resolver uv; добавлен dev-only pytest-playwright
  0.10.0 и его зависимости, включая Playwright 1.64.1. Lock не создавался вручную.
- CI содержит отдельный PostgreSQL 17 service с disposable паролем,
  `TEST_DB_*`, locked sync, Ruff, Django check, migration check,
  Chromium resources и полный pytest. Отсутствие локальной БД не маскируется skip.

## Выполненные проверки

Окружение uv: `UV_CACHE_DIR=/tmp/deanery-uv-cache`,
`UV_PYTHON_INSTALL_DIR=/tmp/deanery-python`. Браузеры:
`PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers`.

- `uv lock`, `uv sync --locked`: успешно; загрузка пакетов потребовала
  сетевого разрешения за пределами sandbox (обычная попытка дала DNS error).
- `uv run --locked ruff check .`, `ruff format --check .`: успешно.
- `uv run --locked python manage.py check`: без замечаний.
- `pytest tests/test_foundation.py tests/test_preview.py`: 30 passed
  (24 foundation + 6 preview); production отдельно загружается в subprocess,
  обе страницы возвращают 404. Первоначальный template-тест обнаружил
  отсутствующий manifest; test settings переключены на source static storage,
  production manifest storage сохранён.
- `pytest tests/test_preview_browser.py --browser-channel chromium`:
  **2 passed**, реальные Chromium viewport 360×1000 и 1440×1000.
  Проверены якоря меню, переход к макету входа и обратно, отсутствие overflow,
  отключённые поля/отсутствие формы, отсутствие JS errors.
- Четыре screenshot ниже сняты реальным Chromium с `full_page=True`.
  Дополнительно проверены HTTP-ответы HTML/assets (нет ответов 400+) и overflow
  на обеих страницах при 360/1440. Главная визуально просмотрена исполнителем.
- Браузер в sandbox завершался SIGTRAP из-за socket restriction;
  проверки выполнены с разрешением вне sandbox. Временные серверы слушали
  только loopback и остановлены через finally. Публичного размещения нет.

Предупреждения: до collectstatic WhiteNoise сообщает об отсутствии staticfiles;
у pytest-playwright есть deprecation warning fixture base_url для pytest 10.
Текущие проверки проходят; pytest 10 не входит в выбранный диапазон.

## Скриншоты

- [Главная 1440](dashboard-desktop-1440.png)
- [Главная 360](dashboard-mobile-360.png)
- [Вход 1440](login-desktop-1440.png)
- [Вход 360](login-mobile-360.png)

## Лицензии и инструменты

Изменения созданы Codex (модели выше), проверены uv, Ruff, Django, pytest,
Playwright/Chromium; изображения страницы не генерировались. SVG нарисованы
в коде проекта; официальный логотип, сторонние изображения и шрифты отсутствуют.
Лицензии новых dev-пакетов проверены в установленных wheel metadata/license files:
pytest-playwright и Playwright — Apache-2.0; greenlet — MIT AND PSF-2.0;
pyee и python-slugify — MIT; text-unidecode — Artistic License;
typing-extensions — PSF-2.0. License files сохранены в окружении uv,
код библиотек/браузерные бинарники в репозиторий не копировались.
Браузерные ресурсы используются только как QA-инструмент.

## Ограничения

Локальный Docker socket недоступен; системные права и SSH-ключи не трогались.
Полные PostgreSQL-тесты, реальные миграции/Compose, удалённый CI, публикация,
доступность из России, сохранение заявок и изоляция бизнес-данных **не проверены**
и этим этапом не заявляются выполненными. Screenshot/preview не заменяет
сквозной рабочий кабинет. Реальные мобильные устройства, Firefox/WebKit,
полный accessibility audit остаются будущими проверками.
