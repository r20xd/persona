# U05 — версионирование

Исходный HEAD: архивная-версия. Ветка main; origin git@github.com:OWNER/REPOSITORY.git. Пользователь постоянно разрешил обычные commit/push принятых этапов. Публикация приложения не выполняется.

Независимый root full suite:402passed,1warning,248.15s, source inputs unchanged. После узких CSS-правок размеров кнопок и двух дополнительных assert root независимо повторил design module:5passed,1warning,25.34s, inputs unchanged. Новый полный прогон после этих CSS-правок не заявляется. Django check0issues, migrationcheck No changes detected, Ruff check/format261 и diff-check passed. Подробности — review.md и independent reports.

Commit/push разрешается после итогового accepted, очистки своей QA и staged review root. Добавлять только явный allowlist этапа: обновлённые документы, UI templates/CSS/собственный SVG, два browser test файла и безопасные U05 evidence. Не использовать git add . или -A. colors.jpg остаётся пользовательским reference вне Git/app, .env/ключи/QA credentials/private rendered HTML/дампы/кеши исключены. Backend, migrations, lock и infra не входят в этап.

Сообщение: `feat(U05): redesign student workspace after Taste audit`. Обязательный trailer, отделённый пустой строкой: `атрибуция команды`. Hook исторический Git hook включён, обход не допускается. Перед commit проверить main/origin/base, exact staged set и staged bytes; перед push фактический trailer. Обычный push origin main без force/amend, затем remote refs/heads/main должен совпасть с HEAD.

На момент подготовки собственный commit/push pending. После операций фактический SHA и результат сообщаются пользователю и root; подтверждение SHA в документах включается в следующий содержательный этап без переписывания опубликованного коммита. Ожидаемый остаток рабочего дерева — только нетронутый colors.jpg. При отказе push сохранить локальный commit и честный push pending.


### Точные stdout и нормализация whitespace

Первый staging392paths совпал с reviewed manifest, но cached --check нашёл330trailing-whitespace lines в8generated console.txt. До коммита root разрешил evidence-only нормализацию: точные исходные bytes сохранены детерминированным gzip mtime=0 в соседних console.raw.txt.gz; decompress==original проверено. Читаемые .txt отличаются только удалением spaces/tabs непосредственно перед newline, строки/числа/exit codes/finding values не менялись. report.json/crops и skill scripts не менялись; это не исправление результатов checker. Allowlist/manifest будут расширены root до restage.

| Original console | SHA256 точных исходных bytes |
| --- | --- |
| docs/evidence/U05/after-first-taste-home/console.txt | `62ed4eb1b55690ac595d70199f1ba304f826505fb7b15909105898d4c030159c` |
| docs/evidence/U05/after-first-taste-login/console.txt | `b43e32c5105ca4ceaf190c05972fbb37e42b07384b0f4bb05a8fdbc4e3d2b269` |
| docs/evidence/U05/after-taste-home/console.txt | `f38642ba35b03fc59fa1073ef456ad4fae7575b84febbe90f661daa9d7ae9013` |
| docs/evidence/U05/after-taste-login/console.txt | `c934fd0f3abd93170feded1c8958aef7a2e1d35dcd6eb24d7adf1ff71ee82d3a` |
| docs/evidence/U05/after-taste-perf/console.txt | `3302551ee79cfdd383c784005f3d275e6dbe531663b924a4ebbf719121e7685d` |
| docs/evidence/U05/before-taste-home/console.txt | `2244d16722779bec0a9345da059747626278afceffa7f9c0b35cef031be1bdc2` |
| docs/evidence/U05/before-taste-login/console.txt | `28c5422d4f2fba9e67e19699aa865f4db2b87c067ee1389dd472fbde0d8ced35` |
| docs/evidence/U05/before-taste-perf/console.txt | `9d8985fbfdb46dbde8e1e15c5b0b662af5b08cbd8561366d813c96422ab4036f` |


### Финальный staging proof

После root проверки8gzip archives и whitespace-only нормализации explicit allowlist/manifest расширены до400paths. Повторно проверены main, origin URL и исходный HEADархивная-версия; первый index перед исходным staging был пуст. Hook исторический Git hook включён и executable, обязательный coauthor не обходился. Restage выполнен строго по400-path allowlist: exact staged set, staged bytes и reviewed SHA256 всех400 current files совпали. cached --check теперь чистый, unstaged tracked diff пуст, единственный untracked — пользовательский colors.jpg; его SHA256 совпал с /tmp/u05-colors-stage-before.sha256 до/после. После этой разрешённой записи restaged только существующий versioning.md; exactset/currentbytes/whitespace/остаток снова проверены, остальные399 staged blobs совпадают с root-reviewed manifest. Commit/push не выполнялись; ожидается отдельный staged review root.
