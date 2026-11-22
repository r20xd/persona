# CAT04 — пиксельные коты и игрушки

Пользователь поручил полностью поменять котов: Маленький хаос из cat_little_chaos, Соня/Отличник из нового парного листа; анимация дыхания/прыжка в игре, статичная картинка в профиле; исключить одежду, генерировать пиксельные игрушки в палитре сайта рядом с котом.

Исполнитель gpt-6.1-sol/low, один writer без субделегации. Read TASK/AGENTS/архитектура27/PLAN16/taste skill+refs. Основной агент создаёт4игрушки imagegen, архитектуру/evidence и независимую приёмку. Разрешены cat.py/modelconstraint/аддитивная0005/JS/CSS/cattemplates, техническая копия исходных sheets в static, тесты cat/browser и необходимые migrationrestoration, implementation evidence. Не менять остальные данные/зависимости/секреты.

Коты именно из пользовательских кадров, через runtimeclip/SVGviewBox/backgroundposition/Canvas source rects, исходники не редактировать; не заменять другими сгенерированными котами. Видимые кадры без подписей/рамок. Idle/jump/joy в игре, остановкаpause/hidden/calm/reducedmotion; профиль неизменно статичен. Изображение игрушки рядом на условном полу, без надевания/наложения на тело. yarn/ball/mouse/fish со старых4слотов, аддитивная миграция сначала снимает прежнее ограничение, переводит значения, затем новое; обратимость и сохранность name/character/completed. Сохранить12карт/1секунду/45секунд, CSRF/currentuser/no-store/repeatguards.

Критерии:3характера точныекадры, загрузка4PNG и сохранениевыбора, animationframediff/jump/pause/reduced, статичный профиль после ожидания,3раундаподряд, migrationforward/reverse/currentstate; mobile360/desktop1440. Freeze перед независимым запуском, не commit/push до accepted.
