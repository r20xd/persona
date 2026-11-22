# U10 — знак persōna за персонажами

Тот же назначенный исполнитель cat01/Sol-low, без делегации. Прочитаны узкая постановка, проектные правила/контракты и актуальный Taste2.5.1 с system/backgroundsreferences. Kindsoftware, существующая палитра/типографика/раскладка сохраняются; пользователь явно попросил собственный прозрачный брендовый знак.

Только дваCSS: cat.css добавляет isolatedstack для существующего .cat-portrait и статичный ::before с small96PNG, inset6%, opacity.20, z0, pointer-events:none; прежний cat-art получаетz1. Это общий портрет всех3характеров/профиля/каталога; cameo не затрагивается. assistant.css добавляет relativeisolatedclippedstack и аналогичный ::beforeopacity.16; существующийimg явноz1. Никаких отрицательныхzindex, геометрических изменений, новых DOM/Tabstops/labels/текстов/движения. Персонажи/игрушки полностью поверх декора; CSSфон обрезан своимпортретом.

Используется существующий ../icons/persona-mark-small.png без правки/генерации. Backend/templates/renderer/игра/ИИадаптер/ассеты/deps/модели untouched. Добавлено24строки CSS, gitdiffcheckexit0. Sourcefreeze перед независимымrootQA/Taste; собственные тесты/БД/сервер не запускались, тесты не добавлялись, commit/push/deploy не делались.

Визуальную различимость/opacity и regression root проверяет реально на360/1440 и3характерах. До этого не заявляется screenshot/GATEPASS. Старое требование одинаковых screenshotblocks под прозрачными пикселями не описывает новый декоративныйфон: foregroundcanvas grid/palette/alpha не менялись, но фон намеренно получает мягкий PNGзнак. Проверять непрозрачные nativeпиксели отдельно от нового background. Kit не правился; финальные фактические визуальные результаты/ограничения — rootreview.
