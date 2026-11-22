/* Native details remains usable without scripts. */
(() => {
  const menu = document.querySelector('[data-workspace-menu]');
  if (!menu) return;
  const summary = menu.querySelector('summary');
  function close(restoreFocus = false) {
    if (!menu.open) return;
    menu.open = false;
    if (restoreFocus) summary.focus();
  }
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.open) {
      event.preventDefault();
      close(true);
    }
  });
  document.addEventListener('click', event => {
    if (!menu.contains(event.target)) close();
  });
  const desktop = matchMedia('(min-width: 851px)');
  desktop.addEventListener('change', event => { if (event.matches) close(); });
})();
