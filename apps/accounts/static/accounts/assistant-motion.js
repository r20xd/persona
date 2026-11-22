/* Decode once; CSS owns every animation frame. The static portrait always remains. */
(() => {
  const portrait = document.querySelector('[data-assistant-motion]');
  const button = document.querySelector('[data-assistant-motion-toggle]');
  if (!portrait || !button) return;
  const motion = matchMedia('(prefers-reduced-motion: no-preference)');
  let ready = false;
  let loading = false;
  let failed = false;
  let paused = false;

  function update() {
    const available = ready && motion.matches;
    portrait.classList.toggle('is-motion-ready', available);
    portrait.classList.toggle('is-motion-paused', paused || document.hidden);
    button.hidden = !available;
    button.setAttribute('aria-label', paused
      ? 'Включить анимацию помощника'
      : 'Приостановить анимацию помощника');
    button.firstElementChild.textContent = paused ? '▶' : 'Ⅱ';
  }

  async function prepare() {
    if (motion.matches && !ready && !loading && !failed) {
      loading = true;
      try {
        const image = new Image();
        image.src = portrait.dataset.motionSource;
        await image.decode();
        if (!image.naturalWidth || image.naturalWidth !== image.naturalHeight) {
          throw new Error('Invalid assistant atlas');
        }
        ready = true;
      } catch {
        failed = true;
      }
      loading = false;
    }
    update();
  }

  button.addEventListener('click', () => {
    paused = !paused;
    update();
  });
  document.addEventListener('visibilitychange', update);
  motion.addEventListener('change', prepare);
  prepare();
})();
