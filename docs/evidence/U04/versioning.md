# U04 — версионирование

Основной агент принял результат в review.md. Исходный HEADархивная-версия; ожидаемая ветка main, origin git@github.com:OWNER/REPOSITORY.git. Пользователь авторизовал обычные commit/push законченных этапов; публикации сайта нет.

Проверки: независимый full396passed/1oldcopyassertfailed/1warning215.77s, input hashes неизменны. После этого изменён только устаревший assert согласованного текста готовой заявки; независимо повторён весь requests37passed3.67s. Django check/migrations, canonical+legacy guest/CSRF/operator access, Ruff all/format250/diff-check успешны. Нового full397после tests-only исправления не заявляем. Own QA container/volume/network удалены с identity/absence checks, private state удалён.

Staging только по явному allowlist; сопоставить exact staged set и bytes с проверенным деревом, прочитать фактический diff и cached whitespace check. Пользовательский colors.jpg был untracked до работы, остаётся нетронутым и исключён из commit. Другие неизвестные изменения не включать. Схема/зависимости/infra/TASK не менялись.

Коммит: `feat(U04): refresh palette, navigation and automatic filters`. Обязательный trailer, отделённый пустой строкой: `атрибуция команды`. Hook не обходить; main/origin/base и remote SHA проверить до commit. Обычный push без force/amend, затем remote refs/heads/main==HEAD. При препятствии сохранить локальный commit и честный push pending.

Собственный SHA/push pending на момент подготовки. Фактический результат сообщается после операций; подтверждение собственного SHA попадёт в следующий содержательный этап без переписывания истории. Ожидаемый остаток рабочего дерева после commit — только пользовательский reference colors.jpg.


Staging проверен исполнителем: main, origin URL и исходный HEAD54435f6 подтверждены; исходный index пуст. core.hooksPath=исторический Git hook, executable commit-msg hook прочитан и сохраняет обязательный coauthor. Добавлены ровно67paths из /tmp/u04-stage-allowlist.txt, в том числе14PNG; staged bytes совпадают с рабочими файлами. cached --check чистый, unstaged tracked diff пуст; единственный оставшийся untracked — пользовательский colors.jpg, его SHA256 до/после совпал. После этой записи restaged только существующий versioning.md; exactset/bytes/whitespace повторно проверены. Commit/push ещё не выполнялись, ожидается отдельный staged review root.

Подтверждение в следующем этапе U05: фактический commitархивная-версия отправлен в origin/main, remote SHA совпал с HEAD, coauthor trailer проверен; в рабочем дереве оставался только пользовательский colors.jpg без изменений.
