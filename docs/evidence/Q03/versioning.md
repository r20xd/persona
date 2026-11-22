# Q03 — версионирование принятого этапа

Статус перед commit: accepted по review.md; SHA/push пока pending. Итоговый SHA и результат push/cleanup сообщаются в финальном отчёте, без изменения файлов после commit.

Предварительные проверки: текущая ветка main, origin fetch/push git@github.com:OWNER/REPOSITORY.git, index пуст; core.hooksPath=исторический Git hook. Независимое ревью:168 passed,109.76s; Ruff/format/check/migration consistency/diff успешны, synthetic deploy check только ожидаемыйW004.

Stage разрешён только для25 файлов из поручения родителя (документы требований/статуса/ADR/evidence,10 файлов приложения,3 файла тестов, security-review). После staging прочитать полный staged diff, сверить точный список и git diff --cached --check. Чужих staged изменений до staging нет.

Команда commit:

```text
git commit -m "fix(Q03): refresh stale account tabs without resubmitting forms" -m "атрибуция команды"
```

После commit проверить фактический trailer, выполнить обычный git push origin main, сверить HEAD с git ls-remote origin refs/heads/main. Force/amend и обход hook запрещены.

Cleanup после push: только container deanery-q03-20261105, предварительно проверить label deanery.qa=Q03, loopback55432 и PostgreSQL17.11; затем rm --force --volumes и exact отсутствие. Пользовательские dev-процессы, контейнеры, .env и ключи не затрагивать.

## Подтверждение, внесённое на следующем этапе Q04/U03

Итог Q03: **pushed**, commit `архивная-версия`, `origin/main`. Исполнитель сравнил HEAD и `git ls-remote origin refs/heads/main`: совпали. Основной агент прочитал обязательный trailer и чистый status. Собственный PG удалён после проверки label/порта/версии и exact отсутствия. Запись вносится следующим коммитом, история Q03 не переписывается.
