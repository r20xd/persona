/* All assets and game logic stay local. Rewards are saved only by the CSRF protected endpoint. */
(() => {
  // Scale the whole logical scene to whole physical pixels, including fractional DPR.
  function fitPixels() {
    const dpr = window.devicePixelRatio || 1;
    document.querySelectorAll('.pixel-scene').forEach(scene => {
      const box = scene.parentElement.getBoundingClientRect();
      const scale = Math.max(1, Math.floor(Math.min(box.width * dpr / 104, box.height * dpr / 104)));
      const width = 104 * scale / dpr, height = 104 * scale / dpr;
      scene.style.setProperty('--pixel', `${scale / dpr}px`);
      scene.style.width = `${width}px`; scene.style.height = `${height}px`;
      // Align the global origin, not merely the offset within a fractional CSS layout box.
      scene.style.left = `${(Math.round((box.left + (box.width - width) / 2) * dpr) / dpr) - box.left}px`;
      scene.style.top = `${(Math.round((box.top + (box.height - height) / 2) * dpr) / dpr) - box.top}px`;
    });
    document.querySelectorAll('.cat-unlock-icon img').forEach(image => {
      const scale = Math.max(1, Math.floor(Math.min(80, image.parentElement.clientWidth) * dpr / 32));
      image.style.width = `${32 * scale / dpr}px`; image.style.height = `${32 * scale / dpr}px`;
      image.style.position = 'relative'; image.style.left = '0px'; image.style.top = '0px';
      const box = image.getBoundingClientRect();
      image.style.left = `${Math.round(box.left * dpr) / dpr - box.left}px`;
      image.style.top = `${Math.round(box.top * dpr) / dpr - box.top}px`;
    });
  }
  const pixelResize = new ResizeObserver(fitPixels);
  document.querySelectorAll('.pixel-portrait').forEach(scene => pixelResize.observe(scene));
  window.addEventListener('resize', fitPixels);
  window.addEventListener('scroll', fitPixels, {passive: true}); fitPixels();
  const game = document.querySelector('[data-cat-game]');
  if (!game) return;
  const $ = selector => game.querySelector(selector);
  const items = JSON.parse(document.getElementById('cat-items').textContent);
  const label = id => items.find(item => item.id === id).name;
  const start = $('[data-start]'), pause = $('[data-pause]'), retry = $('[data-retry]');
  const arena = $('[data-arena]'), status = $('[data-game-status]');
  const speech = document.getElementById('cat-speech');
  const calm = $('[data-calm]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  calm.checked = reducedMotion.matches;
  const targets = [...game.querySelectorAll('[data-item]')];
  let attempt, wishes = [], collected = [], swapFrom = '', running = false, paused = false;
  let remaining = 20000, tick = 0, interval, saving = false, finishPayload;
  let generation = 0, finishTimer, shuffleTimer, interactionUntil = 0;
  const transitions = new Set();
  const catSprite = document.querySelector('[data-cat-animated]');
  const catFrames = JSON.parse(document.getElementById('cat-sprite-frames').textContent);
  const catTiming = JSON.parse(document.getElementById('cat-sprite-timing').textContent);
  const extraPoses = ['blink', 'stretch', 'yawn'];
  let catPose = 'idle', poseStart = performance.now(), poseUntil = 0;
  let nextExtraAt = performance.now() + 1800, extraIndex = 0;
  function paintCat(pose = 'idle', frame = 0) {
    if (!catSprite) return;
    const index = Math.max(0, Math.min(frame, catFrames[pose].length - 1));
    window.PersonaCat?.render(catSprite,pose,index,catFrames[pose].length);
    catSprite.dataset.pose = pose; catSprite.dataset.frame = index;
  }
  function resetCat() {
    catPose = 'idle'; poseStart = performance.now(); poseUntil = 0;
    nextExtraAt = performance.now() + 1800; paintCat();
  }
  function beginPose(pose) {
    catPose = pose; poseStart = performance.now();
    poseUntil = poseStart + catFrames[pose].length * catTiming[pose];
    paintCat(pose);
  }
  function catReaction(pose) {
    if (!mayMove() || paused || document.hidden) { resetCat(); return; }
    // Ambient poses never replace an active interaction reaction.
    beginPose(pose);
  }
  function catTick() {
    const now = performance.now();
    if (!mayMove() || paused || document.hidden) { resetCat(); return; }
    if (!running && !(catPose === 'joy' && now < poseUntil)) { resetCat(); return; }
    if (catPose !== 'idle' && now >= poseUntil) {
      catPose = 'idle'; poseStart = now; nextExtraAt = now + 2200;
    }
    if (running && catPose === 'idle' && now >= nextExtraAt) {
      beginPose(extraPoses[extraIndex % extraPoses.length]); extraIndex += 1;
    }
    const elapsedFrame = Math.floor((now - poseStart) / catTiming[catPose]);
    const frame = catPose === 'idle' ? elapsedFrame % catFrames.idle.length : elapsedFrame;
    paintCat(catPose, frame);
  }
  let catTicker = setInterval(catTick, 80);
  const csrf = document.querySelector('[name=csrfmiddlewaretoken]').value;
  const say = message => { status.textContent = message; };
  async function post(url, payload = {}) {
    const response = await fetch(url, {method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf}, body: JSON.stringify(payload)});
    if (!response.ok) {
      let detail;
      try { detail = (await response.json()).error; } catch { /* HTML login/CSRF error */ }
      throw new Error(detail || 'Не удалось сохранить. Проверьте соединение или обновите страницу.');
    }
    if (response.redirected) throw new Error('Войдите снова и начните новый раунд.');
    return response.json();
  }
  function drawWishes() {
    $('[data-wishes]').replaceChildren(...wishes.map(id => {
      const li = document.createElement('li');
      li.textContent = (collected.includes(id) ? '✓ ' : '') + label(id);
      li.classList.toggle('is-collected', collected.includes(id));
      return li;
    }));
  }
  function updateTargets() {
    game.querySelectorAll('[data-item]').forEach(button => {
      button.disabled = !running || paused || collected.includes(button.dataset.item);
      button.classList.toggle('is-collected', collected.includes(button.dataset.item));
    });
  }
  function cancelTransitions() {
    transitions.forEach(animation => animation.cancel()); transitions.clear();
  }
  function mayMove() { return !calm.checked && !reducedMotion.matches; }
  function shuffle() {
    if (!running || paused || document.hidden || !mayMove() || performance.now() < interactionUntil) return;
    // Keep the DOM/Tab order intact and pin the focused target in its current visual slot.
    const movable = targets.filter(button => button !== document.activeElement && !button.disabled);
    if (movable.length < 2) return;
    cancelTransitions();
    const before = new Map(movable.map(button => [button, button.getBoundingClientRect()]));
    const slots = movable.map(button => Number(button.style.order));
    // A nonzero rotation guarantees a visible change without stacking or crossing targets at rest.
    const offset = 1 + Math.floor(Math.random() * (slots.length - 1));
    movable.forEach((button, index) => { button.style.order = slots[(index + offset) % slots.length]; });
    movable.forEach(button => {
      const old = before.get(button), next = button.getBoundingClientRect();
      const animation = button.animate([
        {transform: `translate(${old.left - next.left}px, ${old.top - next.top}px)`},
        {transform: 'translate(0, 0)'}
      ], {duration: 180, easing: 'ease-out'});
      transitions.add(animation);
      animation.onfinish = () => transitions.delete(animation);
    });
  }
  function setCalm() {
    arena.classList.toggle('is-calm', !mayMove());
    if (!mayMove()) { cancelTransitions(); resetCat(); }
  }
  calm.addEventListener('change', setCalm);
  reducedMotion.addEventListener('change', setCalm); setCalm();
  targets.forEach((button, index) => {
    button.style.order = index;
    button.addEventListener('pointerdown', event => {
      interactionUntil = performance.now() + 500;
      // A moving tile keeps the pointer until release, so its own item receives the click.
      if (event.isPrimary) button.setPointerCapture(event.pointerId);
    });
    button.addEventListener('focus', () => { interactionUntil = Math.max(interactionUntil, performance.now() + 300); cancelTransitions(); });
  });
  function updateClock() { $('[data-clock]').textContent = Math.ceil(remaining / 1000); }
  function stop() {
    running = false; paused = false; clearInterval(interval); clearInterval(shuffleTimer);
    cancelTransitions(); resetCat();
    pause.hidden = true; start.hidden = false; start.textContent = 'Начать новые сборы';
    $('[data-pause-cover]').hidden = true; arena.classList.remove('is-paused'); updateTargets();
  }
  function setPause(value) {
    if (!running) return;
    if (!paused && value) remaining = Math.max(0, remaining - (performance.now() - tick));
    paused = value; tick = performance.now();
    if (paused) { cancelTransitions(); resetCat(); }
    pause.textContent = paused ? 'Продолжить сборы' : 'Поставить на паузу';
    $('[data-pause-cover]').hidden = !paused; arena.classList.toggle('is-paused', paused);
    say(paused ? 'Время остановлено. Продолжайте, когда захотите.' : 'Сборы продолжаются.');
    updateClock(); updateTargets();
  }
  pause.addEventListener('click', () => setPause(!paused));
  document.addEventListener('visibilitychange', () => { if (document.hidden) setPause(true); });
  async function saveResult(round = generation) {
    if (saving || round !== generation || !finishPayload) return;
    const payload = {...finishPayload, collected: [...finishPayload.collected]};
    saving = true; retry.hidden = true; start.disabled = true;
    say('Рюкзак собран. Сохраняем награду…');
    try {
      const result = await post(game.dataset.finishUrl, payload);
      if (round !== generation) return;
      speech.textContent = 'Мур. Без тебя я бы точно взял только колбасу.';
      say(result.completed > 4 ? 'Рюкзак собран! Все четыре игрушки уже ваши.' : `Рюкзак собран! Открыто: ${result.reward}.`);
      $('[data-reward-link]').href = `${location.pathname}?wardrobe=${result.completed}#cat-wardrobe`;
      $('[data-reward-link]').hidden = false;
    } catch (error) {
      if (round !== generation) return;
      say(error.message + ' Рюкзак остаётся здесь: можно повторить сохранение.'); retry.hidden = false;
    } finally { if (round === generation) { saving = false; start.disabled = false; } }
  }
  retry.addEventListener('click', () => saveResult());
  start.addEventListener('click', async () => {
    if (start.disabled || saving) return;
    const round = ++generation;
    stop(); clearTimeout(finishTimer); finishPayload = undefined;
    start.disabled = true; retry.hidden = true; $('[data-reward-link]').hidden = true;
    say('Кот выбирает вещи…');
    try {
      const nextAttempt = await post(game.dataset.startUrl);
      if (round !== generation) return;
      attempt = nextAttempt;
      wishes = [...attempt.initial]; collected = []; swapFrom = ''; remaining = attempt.seconds * 1000;
      running = true; paused = false; tick = performance.now();
      resetCat(); extraIndex = 0;
      $('[data-pause-cover]').hidden = true; arena.classList.remove('is-paused');
      targets.forEach((button, index) => { button.style.order = index; });
      shuffleTimer = setInterval(shuffle, 1000);
      start.hidden = true; pause.hidden = false; pause.textContent = 'Поставить на паузу';
      $('[data-idle]').hidden = true; $('[data-targets]').hidden = false;
      drawWishes(); updateTargets(); updateClock();
      game.scrollIntoView({behavior: 'instant', block: 'start'});
      speech.textContent = 'Вот мой список. Кажется, я ничего не забыл.';
      say('Найдите три вещи из списка. Неверная вещь не отнимает время.');
      interval = setInterval(() => {
        if (!running || paused) return;
        const now = performance.now(); remaining = Math.max(0, remaining - (now - tick)); tick = now;
        updateClock();
        if (!remaining) {
          stop(); say('Время вышло. Кот всё равно вам рад — попробуйте ещё раз.');
          speech.textContent = 'Ничего, следующая пара только через вечность. Почти.';
        }
      }, 100);
    } catch (error) { if (round === generation) say(error.message); }
    finally { if (round === generation) start.disabled = false; }
  });
  game.querySelectorAll('[data-item]').forEach(button => button.addEventListener('click', () => {
    if (!running || paused || button.disabled) return;
    const item = button.dataset.item;
    if (!wishes.includes(item)) {
      catReaction('surprise');
      speech.textContent = item === 'sausage' ? 'Колбаса — аргумент. Но сегодня по списку.' : 'Очень нужная вещь. Но сегодня я попросил другую.';
      say('Эта вещь пока не нужна. Посмотрите на пожелания кота.'); return;
    }
    collected.push(item); catReaction('jump');
    if (collected.length === 1) {
      swapFrom = wishes.find(id => !collected.includes(id));
      wishes = wishes.map(id => id === swapFrom ? attempt.replacement : id);
      speech.textContent = `Я передумал! Вместо «${label(swapFrom)}» беру «${label(attempt.replacement)}».`;
      say(`Первая вещь в рюкзаке. Новое пожелание: ${label(attempt.replacement)}.`);
    } else say(`В рюкзаке ${collected.length} из 3 вещей.`);
    drawWishes(); updateTargets();
    if (collected.length === 3) {
      finishPayload = {token: attempt.token, collected: [...collected], swap_from: swapFrom};
      stop(); catReaction('joy');
      // The server's minimum elapsed check also rejects instant forged finishes.
      say('Все три вещи на месте. Застёгиваем рюкзак…'); start.disabled = true;
      const round = generation;
      finishTimer = setTimeout(() => saveResult(round), 2100);
    }
  }));
  window.addEventListener('pageshow', event => {
    if (event.persisted) {
      catTicker = setInterval(catTick, 80);
      saving = false; start.disabled = false; retry.hidden = true; finishPayload = undefined;
      say('С возвращением! Начните новые сборы.');
    }
  });
  window.addEventListener('pagehide', () => {
    generation += 1; stop(); clearTimeout(finishTimer); clearInterval(catTicker);
  });
})();
