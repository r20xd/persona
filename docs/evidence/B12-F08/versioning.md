# Версионирование B12/F08

Код и документы приняты основным агентом: [review.md](review.md), accepted.
Исполнитель получил отдельное поручение обычного commit/push после приёмки;
публикация приложения этим поручением не разрешена.

Prechecks: текущая ветка `main`, fetch/push remote `origin` —
`git@github.com:OWNER/REPOSITORY.git`. Начальный index пуст.
`core.hooksPath=исторический Git hook`; hook не обходится. Статус содержит только
согласованные изменения этапа. Родитель независимо подтвердил Ruff153,
Django check, migration check, diff-check и145 passed на PostgreSQL/Chromium.

В index включён только точный allowlist из поручения родителя, включая этот
отчёт и файлы review/V2/статуса родителя. Перед commit исполнитель проверяет
полный `git diff --cached`, `git diff --cached --check`, перечень путей и
отсутствие unstaged изменений. Проверка staged завершена перед commit;
сам отчёт заранее включён в commit и после него не переписывается ради SHA.

Команда: `git commit -m 'feat(B12-F08): compose student dashboard and safe demo bootstrap'`
с обязательным trailer `атрибуция команды`.
После commit проверяется фактическое сообщение, затем обычный
`git push origin main` и `git ls-remote origin refs/heads/main`.

На момент записи commit SHA/push/sync — pending. Их фактический результат
будет сообщён в итоговом отчёте сессии; отсутствие SHA здесь не означает
отсутствие последующего commit. Force/amend и изменение remote запрещены.
После сверки удаляется только собственный disposable QA-контейнер
`deanery-b12-qa-20261105`, exact-name отсутствие проверяется отдельно.

## Подтверждение, внесённое на следующем этапе Q05

Итог предыдущей сессии: **pushed**, commit `архивная-версия`, `origin/main`. Исполнитель после push сравнил HEAD и `git ls-remote origin refs/heads/main`: SHA совпали. Основной агент отдельно прочитал сообщение коммита с обязательным trailer и подтвердил чистый status. QA-контейнер удалён, exact-name проверка пустая. Эта запись добавляется новым коммитом, опубликованная история B12/F08 не переписывается.
