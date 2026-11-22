# CAT11 — tests-only changes requested

Правильная ISOдата устранила2migrationfailures. Повтор всего browserfile: **9passed/1failed/1existingwarning61.03s**, raw `independent-tests-02.txt`. Все новые timing/navigation/legacy/optout/longbubble сценарии passed, runtime JS прежний.

Остался DPRresize:100ms виртуального времени не гарантировали фактический native resizeevent, позиция всё ещё относилась к900pxviewport. Исполнителю передано tests-only возобновление clock на фазе resize и ожидание настоящего события через одноразовый marker. Не подменять событие synthetic dispatch, не менять app без подтверждённой ошибки. После исправления root повторит только этотcase; остальные9browser и8server/sharedshell уже проверены на неизменном runtimeкоде.

Статус: **changes requested** до подтверждения native resize. Versioningpending.
