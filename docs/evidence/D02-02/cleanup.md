# D02-02 — очистка локального QA

После завершения independent fullsuite root разрешил удалить только retained suite DB. Проверены helper `/tmp/deanery-root-suite-db.py` и вызванный `Rehearsal.cleanup`: выборка по точному compose project, проверка `deanery.d02.owner` перед каждой мутацией, проверка отсутствия каждого удалённого container/volume/network. Служебные значения и сырые логи в отчёт не включены.

Команда: `PYTHONPATH=. .venv/bin/python /tmp/deanery-root-suite-db.py cleanup /tmp/deanery-d02-iyja1e1e/suite-state.json`.

Фактический результат: exit0, `cleanup=complete`. Собственный private state после cleanup отсутствует. Другие QA и пользовательские dev-ресурсы не затрагивались. Собственный TLS runner также завершил cleanup complete (production.json); независимые TLS/imageaudit root сообщили cleanup complete.
