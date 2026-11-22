# K01 — версионирование

Результат принят основным агентом: review.md. Исходный HEAD `архивная-версия`. Пользователь ранее разрешил обычный commit/push законченных этапов в main→origin/main; публикация сайта не выполняется.

Полный независимый suite392passed,1warning,245.15s с неизменными входными hashes; затем только минимальные UI copy/условия показа и blur для новых screenshot. Финальные независимые2browserpassed13.71s, Django check, makemigrations check без warning на существующей собственной QA DB, Ruff all/format13/diff-check успешно. Миграция additive; прежние записи сохранены. Own QA cleanup complete/absence verified.

Перед commit проверить ветку/remote/base HEAD/индекс/hook и exact staged allowlist, отсутствие секретов/чужих изменений, соответствие staged bytes проверенному дереву. Добавляются только файлы K01 и root docs с обновлённой архитектурой/приоритетом работ/подтверждением прежнего D02-02 SHA. Зависимости/infra/TASK не меняются.

Сообщение: `feat(K01): add personal attention radar and visit digest`. Обязателен отделённый пустой строкой trailer `атрибуция команды`, hook не обходить. Обычный push без force/amend, remote SHA должен совпасть с HEAD. Если push неуспешен, сохранить локальный commit и сообщить pending.

На момент подготовки собственный SHA/push pending. Фактический результат сообщается после commit/push; подтверждение SHA войдёт в следующий содержательный этап без переписывания истории.

## Фактическая подготовка индекса

По отдельному поручению основного агента выполнен staging без commit/push. Проверены: ветка `main`, origin `git@github.com:OWNER/REPOSITORY.git`, исходный HEAD `архивная-версия`, изначально пустой индекс и `core.hooksPath=исторический Git hook`. Через штатный escalation выполнен `git add --` с каждым явным путём из согласованного allowlist `/tmp/deanery-k01-stage-allowlist.txt`.

Множество staged путей точно совпало с allowlist: **32 файла**, без повторов. `git diff --cached --check` прошёл; незастейдженных изменений и untracked файлов после добавления нет. Этот же versioning.md дополнен фактическими результатами и повторно добавлен отдельно; новых файлов вне allowlist не создано. Commit/push ожидают отдельного follow-up после root проверки staged bytes.

Подтверждение в следующем этапе U04: фактический commitархивная-версия отправлен в origin/main, remote SHA совпал с HEAD, дерево было чистым, coauthor trailer проверен.
