# K01 — очистка изолированной QA среды

После завершения root проверок основной агент отдельно разрешил удалить только собственный QA проект.

- Helper: `PYTHONPATH=. .venv/bin/python /tmp/deanery-root-suite-db.py cleanup /tmp/deanery-d02-ha1dw5_c/suite-state.json`.
- Проект: `deanery-d02-49be6b41052a4bdf96eeada20dc1f250`.
- Проверка владельца: существующий helper проверяет `deanery.d02.owner` каждого ресурса до удаления и повторный inspect на отсутствие после удаления. Массовые prune, mounts и чужие ресурсы не использовались.
- Результат helper: `{"cleanup":"complete"}`, exit0.
- Независимый read-only listing Docker по точному `com.docker.compose.project`: **0 containers, 0 volumes, 0 networks**, exit0.
- Private directory `/tmp/deanery-d02-ha1dw5_c` отсутствует; temporary state/QA пароль удалены вместе с QA средой.

Код приложения после freeze не изменялся. Commit/push ожидают отдельного Git follow-up.
