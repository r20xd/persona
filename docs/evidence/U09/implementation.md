# U09 implementation

Исполнитель gpt-6.1-sol/low, один writer, без делегации. Удалены нижние profile-links и student header label; header-actions сохраняют правое выравнивание margin-left:auto. Login marketing и operator label сохранены.

Все пять типов GET-фильтров (включая operator requests) явно отмечены data-auto-filter; Показать помещены в noscript. filters.js обрабатывает select/checkbox/date, не отправляет пустую/невалидную дату, включает date в aria-describedby. POST и scoped серверные выборки не изменены.

Existing browser suite расширен: date fill day/week, view в URL, другой scoped semester и обратное переключение grades/session, пустые состояния, отсутствие Показать/student header/profile links, no-JS date/term fallback. Второй semester создаётся только в disposable ui_site через psycopg с offering/enrollment student.one; application DB не используется. Screenshots переключены на отдельный UPDATE_U09_EVIDENCE и U09 paths; исторические PNG не перезаписываются. Старый grades click Показать заменён select с ожиданием навигации.

Фактические проверки: Ruff двух изменённых test modules passed; Django preview check no issues; git diff --check passed. Browser прогон и QA выполняет родитель независимо. По rg других явных click Показать в browser tests нет; ссылки «Моё расписание/Заказать справку» остаются на dashboard, явных stale profile-links assertions вне изменённого suite не найдено. Commit не выполнялся.
