# Q04/U03 — версионирование принятого этапа

Статус перед commit: **accepted** по [review.md](review.md). Независимые проверки основного агента: Chromium179passed162.21s, Firefox11passed57.66s, WebKit11passed58.25s; Ruff/check/migrations/diff exit0. Аппаратный телефон/системный zoom остаются вне принятого локального объёма.

Prechecks: фактическая ветка `main`; origin `git@github.com:OWNER/REPOSITORY.git`; index пуст; hooksPath `исторический Git hook`. Рабочее дерево содержит только согласованный этап (включая документы основного агента). Секреты/пользовательские .env/dev/ключи не включаются.

Родитель выдал точный allowlist 38 путей. Выполнено явное стадирование через `git add -- <38 paths>` без `git add .`/`-A`; автоматическая сверка staged paths с allowlist подтвердила ровно 38 файлов. Полный staged diff прочитан частями (включая документы основного агента, templates, CSS/JS, новые tests/helper и binary PNG entries); `git diff --cached --check` прошёл. Сторонних staged изменений нет.

Планируемая команда: `git commit -m 'fix(Q04-U03): improve keyboard access and browser form recovery' -m 'атрибуция команды'`. Hook не обходится; фактическое сообщение проверяется перед `git push origin main`. Затем `git rev-parse HEAD` сверяется с `git ls-remote origin refs/heads/main`.

На момент записи SHA **pending**, commit/push/sync **pending**. Итоговый SHA и результат сверки сообщаются в финальном отчёте без изменения файлов после commit.

После сверки (также при push blocker) — только exact ownership/port/image inspect и cleanup собственных QA ресурсов: PG `deanery-q04-20261106`, label `deanery.qa=Q04-U03-20261106`,loopback55432,PG17.11 с его anonymous volume; browser `deanery-q04-browser-20261106`,label `deanery.qa=Q04-U03-browser-20261106`,loopback53000,Mounts[]. После удаления проверить exact отсутствие. Другие контейнеры/образы/dev не трогать.

Подтверждение в следующем этапе Q06: commit `архивная-версия` создан с требуемым trailer и отправлен в `origin/main`; серверный SHA совпал с локальным. QA PostgreSQL и browser-container предыдущего этапа удалены по exact ownership, включая собственный anonymous volume. Это зафиксированный результат предыдущей сессии; повторного удаления в Q06 не выполнялось.
