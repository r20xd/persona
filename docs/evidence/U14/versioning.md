# U14 — версионирование

Принятый U14 сохранён коммитом `архивная-версия` и отправлен в `origin/main`. После push живой `git ls-remote origin refs/heads/main` подтвердил тот же SHA. Проверены ветка/remote, активный `исторический Git hook`, фактический/staged diff, staged diff --check и точный allowlist из 14 файлов. Обязательный trailer соавторства подтверждён в фактическом сообщении перед push. `.gitignore` и посторонние файлы не включались. Проверки и границы приёмки — в [review.md](review.md). Эта запись оставлена untracked post-commit evidence для следующего содержательного коммита.
