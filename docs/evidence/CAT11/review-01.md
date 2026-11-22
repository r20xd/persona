# CAT11 — changes requested

Root independently reviewed11line JSdiff и browser scenarios; границы writer соблюдены. Первый focused suite на временной PostgreSQL17 и реальном Chromium: **15passed/3failed/1existingwarning89.47s**; полный исходный вывод `independent-tests.txt`.

Замечания к тестам:

1. `page.clock.pause_at(page.evaluate('Date.now()'))` передаёт миллисекунды в API, трактующий число как секунды. Виртуальное время получилось примерно1000×обычного; старый180sdeadline оказался в прошлом. Передать корректную ISOстроку/дату, проверить настоящий переход legacy→v2.
2. С приостановленными часами fractionalDPRresize проверял geometry до доставки resizeevent: pety632 при новойnavy262. Дождаться события/продвинуть virtualclock перед assert. Приложение не менять без подтверждённой ошибки runtime.

Пятнадцать других сценариев прошли, включая серверную projection/изоляцию, run/hop click/navigation, optout, suppression, longbubbleclose/Escape и sharedshell. Root просмотрел actual clicked360/hop1440 PNG: кот и облачко в viewport, выше навигации. Шаблоны/CSS/ассеты не менялись. Передано тому же исполнителю для tests-only исправления, затем повтор browserfile; полного игрового suite не требуется.

Статус: **changes requested**, versioningpending. JSsyntax/Ruffformat/diffchecks passed,21sourcehashes сохранялись во время прогона. Taste2.5.1 применяется к заданному поведению, новый layoutGATEPASS не заявлен; прежние общие findings в CAT10 остаются.
