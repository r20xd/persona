# Q04/U03: браузеры и доступность

Проверки выполняются на собственном PostgreSQL17 и DEBUG=False Gunicorn/WhiteNoise (--threads4) с отдельными случайными DB/static root/SECRET_KEY. Фикстура ui_site в tests/ui_qa.py (жизненный цикл из Q03) очищает ресурсы в finally; веб-порт выбирается динамически. Пользовательская .env не используется subprocess приложения.

Целевой модуль: `tests/test_ui_accessibility_browser.py`. Он проверяет путь двух студентов и оператора на 360/390/768/1440 CSS px; текстовый статус, сохранение и запрет чужой карточки; длинный неразрывный комментарий; клавиатуру, реальное перекрытие skip link, focus ошибок и controls; reduced motion; сетевой сбой до отправки и потерю ответа после сохранения с безопасным повтором submission_key.

Проверка reflow использует viewport720×500 как эквивалент области1440×1000 при200%. Это не управление системным zoom. Минимальная ширина360 проверяется отдельно. Реальные Safari/iOS/Android, аппаратный телефон и системный zoom остаются непроверенными. Это ограниченный аудит, не сертификация WCAG.

Подтверждённые дефекты: активный login input наследовал cursor:not-allowed и слабый цвет из preview; кнопки/select/textarea не получали общий focus; login error не имел aria/error focus; request/operator errors не имели focus summary; desktop nav перекрывала focused skip link. Hit-test подтвердил ещё перекрытие focused submit нижней навигацией; mobile scroll-padding/scroll-margin исправляют его. Skip targets main имеют tabindex=-1. Исправления сохраняют палитру, disabled preview и native POST/CSRF.

Native формы не блокируют submit программно и не рисуют искусственный success/loading. При потере сети браузер показывает собственный error document; восстановление — открыть кабинет/«Мои заявки» и проверить сохранение. Подсказка добавлена под формой. Lost-response тест реально отправляет POST через route.fetch и скрывает ответ; затем находит сохранённую карточку и повторяет исходное тело с CSRF/submission_key через authenticated HTTP context.

## Воспроизведение

```bash
DB_PORT=55432 TEST_DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser-channel chromium -q
DB_PORT=55432 TEST_DB_PORT=55432 PLAYWRIGHT_BROWSERS_PATH=/tmp/deanery-browsers .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser firefox -q
DB_PORT=55432 TEST_DB_PORT=55432 Q04_PLAYWRIGHT_ENDPOINT=ws://127.0.0.1:53000/ .venv/bin/pytest tests/test_ui_accessibility_browser.py --browser webkit -q
```

Для новых PNG добавить UPDATE_EVIDENCE=1 только к целевому модулю; исторические evidence не обновлять.

Host WebKit требует отсутствующие gtk4/gstreamer/libsoup runtime. Согласованный fallback — официальный browser-only server Playwright1.64.1, соответствующий uv.lock, с loopback tunnel `expose_network='<loopback>'`. Python3.13, pytest и приложение остаются на host. Контейнер без mounts/hostnetwork/socket/privileged, под pwuser, с --init/--shm-size=1g, loopback mapping53000→3000. Image digest: `mcr.microsoft.com/playwright@sha256:2f05f8a734509a7b3f26a912639488ee08f58a7b292d14d62271bcff9038768f`.

```bash
docker run -d --name deanery-q04-browser-20261106 --label deanery.qa=Q04-U03-browser-20261106 --init --shm-size=1g --user pwuser --workdir /home/local-user -p 127.0.0.1:53000:3000 mcr.microsoft.com/playwright@sha256:2f05f8a734509a7b3f26a912639488ee08f58a7b292d14d62271bcff9038768f /bin/sh -c 'npx -y playwright@1.64.1 run-server --port 3000 --host 0.0.0.0'
```

Перед созданием проверить свободный порт/уникальное имя; перед cleanup inspect exact name, label и mounts. Удалять только свой container (`docker rm -f deanery-q04-browser-20261106`), затем проверить его отсутствие. Образы и чужие ресурсы не удалять. Текущий server оставляется родителю для независимого rerun.

QA-контур: default Gunicorn sync1 мог блокироваться browser preconnect, в том числе route.fetch и WebKit POST после hash navigation. На том же приложении с --threads4 оба сценария проходят; это starvation тестового контура, не дефект fragment/CSRF. Старые fixtures не менялись.

Новые PNG сняты только Chromium, как viewport captures после реальных assertions. Screenshot helper не меняет исторические PNG.
