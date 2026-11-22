# Q05 — версионирование принятого этапа

- Приёмка: `docs/evidence/Q05/review.md`, accepted после независимого lifecycle и regression.
- Предварительные проверки:152passed/1existing warning; Ruff check/format164; Django check/makemigrations/diff--check exit0. Код после приёмки не менялся.
- Проверенная цель: ветка `main`, remote `origin`, `git@github.com:OWNER/REPOSITORY.git`.
- До staging индекс пуст; чужих staged changes нет. Staging — только18 явных путей из поручения основного агента, включая этот файл. Перед commit читается полный staged diff и выполняется `git diff --cached --check`.
- Hook `исторический Git hook` активен через local core.hooksPath; hook не обходится. Сообщение `test(Q05): verify restart and isolated database restore` с trailer `атрибуция команды` проверяется в фактическом commit до push.
- Команды: `git add -- <18 explicit paths>` → `git diff --cached` / `git diff --cached --check` → `git commit -m ... -m 'Co-authored-by: ...'` → `git log -1 --format=full` → `git push origin main` → `git rev-parse HEAD` и `git ls-remote origin refs/heads/main` → `git status --short`.
- Commit SHA: pending на момент записи; фактический SHA будет передан в итоговом отчёте без изменения файлов после commit.
- Push/sync: pending на момент записи; успех подтверждается только совпадением local HEAD и remote refs/heads/main в итоговом отчёте.
- После сверки Git запланирован exact cleanup suite container `deanery-q05-suite-7214fd9e1fbf4e51922d7a1bd1d5ab4e` только после сверки label `deanery.q05.suite=deanery-q05-suite-7214fd9e1fbf4e51922d7a1bd1d5ab4e`: `docker rm --force --volumes <exact-name>` и inspect exact отсутствия. Никакие пользовательские dev-ресурсы не затрагиваются.

Файл намеренно фиксируется до commit; итоговые SHA/push/cleanup сообщаются отдельно, чтобы не создавать самоссылочное обновление коммита.

## Подтверждение, внесённое на следующем этапе Q03

Итог Q05: **pushed**, commit `архивная-версия`, `origin/main`. Исполнитель сверил HEAD с `git ls-remote origin refs/heads/main`: совпали; основной агент прочитал обязательный trailer и подтвердил чистый status. Suite container удалён после проверки exact label, отсутствие подтверждено. Подтверждение добавляется следующим коммитом без переписывания опубликованной истории.
