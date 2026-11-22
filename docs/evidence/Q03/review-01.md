# Q03 — предварительное ревью

Статус: **changes requested**, до независимого финального прогона. Прочитаны первоначальный history.js, logout/password command diff и новые server/browser tests. Реальный дефект вкладки подтверждён исполнителем до исправления. Родитель выбрал [ADR001](../../decisions/001-session-tab-refresh.md), отказавшись от нового endpoint/contextprocessor в пользу штатного CSRF rotation и memory-only UI проверки.

| № | Место | Последствие | Проверяемое исправление |
| --- | --- | --- | --- |
| 1 | BroadcastChannel constructor/postMessage | Optional API может присутствовать, но бросать SecurityError; fallback не должен давать uncaught exception | try/catch, сохранённые focus/visibility listeners; browser test бросающего constructor |
| 2 | reloadSafely / pageshow.persisted | Сообщение «Сессия изменилась» неточно при обычном восстановлении BFCache с тем же пользователем | Нейтральное «Обновляем кабинет» или отдельный reason; удаление старого DOM и доступная retry-ссылка |
| 3 | location.reload на POST-документе | При ошибке валидации/409/429 браузер может повторить POST или показать resubmission dialog | Только location.replace GET; при смене маркера главная, при persisted прежний GET URL либо главная для POST-документа. Безопасный data-request-method в base, retry тот же GET. Реальный server-invalid POST→A/B switch, отсутствие повторного POST/dialog/новой заявки |
| 4 | security_site default port / env | Default55432 расходился с README/Compose/остальными тестами5432; partial blacklist оставлял лишние service/Python переменные | Default5432, наш55432 только через TEST_DB_PORT; safe allowlist subprocess env и собственный случайный SECRET_KEY |
| 5 | security_site teardown | Ошибка ожидания web могла прервать finally до удаления собственной БД | terminate/wait/kill только своего Popen и вложенный finally для exact-created DB cleanup |

Точное ограничение BFCache: реальная навигация назад/вперёд и регистрация pageshow.persisted отдельно от искусственно посланного события. При persisted=0 нельзя объявлять настоящий BFCache проверенным. При JS disabled серверное CSRF/ownership остаётся обязательным и проверяется HTTP тестом без выполнения JS. CSP/proxy/публичный HTTPS, Firefox/WebKit и телефон этим этапом не закрываются.

Следующий шаг: исправления тем же Sol/low, целевые проверки, полный suite, write freeze и независимый прогон основного агента. После accepted — только отдельное поручение на точный commit/push.
