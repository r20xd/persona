/* An entrance after ordinary tab navigation; no snapshots or navigation hooks. */
(() => {
  if (!matchMedia('(prefers-reduced-motion: no-preference)').matches) return;
  const navigation = performance.getEntriesByType('navigation')[0];
  if (navigation?.type !== 'navigate' || !document.referrer) return;

  let previous;
  try {
    previous = new URL(document.referrer);
  } catch {
    return;
  }
  if (previous.origin !== location.origin || previous.pathname === location.pathname) return;

  const tabPaths = new Set(['/schedule/session/', '/session/']);
  for (const link of document.querySelectorAll('.campus-nav a, .header-profile')) {
    const target = new URL(link.href);
    if (target.origin === location.origin) tabPaths.add(target.pathname);
  }
  if (!tabPaths.has(previous.pathname)) return;

  document.getElementById('main')?.classList.add('workspace-content-arrive');
})();
