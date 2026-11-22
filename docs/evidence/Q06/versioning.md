# Q06 — подготовка версионирования

Ревью root: accepted в локальном объёме Q06, см. `review.md`. Независимо:185passed,1existing warning,158.80s; benchmark exit0,20sessions/360reads,p95=178.658ms,cleanup_complete=true; query counts initial/expanded неизменны. Ruff/check/format/diff — exit0. Приложение, схема и lock не изменялись. Exact suite cleanup завершён отдельно, см. `cleanup.md`.

Prechecks: текущая ветка `main`, origin fetch/push `git@github.com:OWNER/REPOSITORY.git`, index пустой, hooksPath `исторический Git hook`. Неизвестных изменений вне согласованного набора не обнаружено.

Согласованный allowlist (26 файлов):

```text
ARCHITECTURE.md
PLAN.md
STATE.md
docs/evidence/Q04-U03/versioning.md
docs/licenses.md
docs/testing/performance.md
docs/third-party/libargon2-LICENSE.txt
scripts/performance_queries.py
scripts/verify_performance.py
tests/test_performance.py
docs/evidence/Q06/audit-dev.json
docs/evidence/Q06/audit-metadata.json
docs/evidence/Q06/audit-runtime.json
docs/evidence/Q06/ci-status.json
docs/evidence/Q06/cleanup.md
docs/evidence/Q06/environment.json
docs/evidence/Q06/implementation.md
docs/evidence/Q06/license-inventory.json
docs/evidence/Q06/license-source-check.json
docs/evidence/Q06/performance-independent.json
docs/evidence/Q06/performance.json
docs/evidence/Q06/prompt.md
docs/evidence/Q06/resource-repair.json
docs/evidence/Q06/review.md
docs/evidence/Q06/suite-resource.json
docs/evidence/Q06/versioning.md
```

План: явный staging только этого набора, равенство staged set allowlist, полный staged diff и diff check, обычный commit с ID Q06 и обязательным Co-authored-by, push main→origin, сравнение HEAD с remote main. Собственный SHA и push на момент создания этого файла **pending**; фактический итог будет только в финальном отчёте после команд. Этот документ после commit не изменяется.

Staged precheck: полный `git diff --cached --check` обнаружил ровно одно замечание: upstream trailing space в `docs/third-party/libargon2-LICENSE.txt:6`. Root принял это единственное исключение ради SHA256-identical notice (`ac36638bcfcedb75441a5daeeaf4ef75b565911712583c272830e9fa7fddb590`). Проверка остальных25путей с исключением только exact license file прошла. Tracked unstaged diff check — exit0. Hook/config/attributes не менялись. Физический телефон, V2, native/OS production license inventory и remote CI этим этапом не закрыты.

Подтверждение в следующем этапе Q01/Q02: commit `архивная-версия` создан с требуемым соавтором и отправлен в `origin/main`. Исполнитель подтвердил exit0 push и совпадение HEAD с фактическим `git ls-remote --heads origin refs/heads/main`; родитель независимо проверил SHA, trailer и чистое дерево. Это результат завершённого Q06, без повторного commit/push или cleanup.
