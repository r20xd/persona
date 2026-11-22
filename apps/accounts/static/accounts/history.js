(() => {
  const csrfMarker = () => document.cookie.split(";").map((part) => part.trim())
    .find((part) => part.startsWith("csrftoken=")) || "";
  const initialMarker = csrfMarker();
  const requestMethod = document.body.dataset.requestMethod;
  let reloading = false;

  const reloadSafely = (sessionChanged = false) => {
    if (reloading) return;
    reloading = true;
    // Remove stale personal content before any network navigation, including offline failures.
    const message = document.createElement("main");
    message.id = "main";
    message.className = "account-main";
    const heading = document.createElement("h1");
    heading.textContent = "Обновляем кабинет";
    const retry = document.createElement("a");
    const destination = sessionChanged || requestMethod === "POST" ? "/" : window.location.href;
    retry.href = destination;
    retry.textContent = "Повторить загрузку";
    message.append(heading, retry);
    document.body.replaceChildren(message);
    window.location.replace(destination);
  };
  const check = () => {
    if (csrfMarker() !== initialMarker) reloadSafely(true);
  };
  window.addEventListener("focus", check);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") check();
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) reloadSafely(csrfMarker() !== initialMarker);
    else check();
  });
  if ("BroadcastChannel" in window) {
    try {
      const channel = new BroadcastChannel("deanery-auth-state");
      channel.addEventListener("message", check);
      channel.postMessage("check");
    } catch {
      // Optional browser capability: focus/visibility checks remain available.
    }
  }
})();
