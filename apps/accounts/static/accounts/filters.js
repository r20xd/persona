"use strict";

// Only explicitly marked read filters participate; mutation forms remain manual.
let filterNumber = 0;
for (const form of document.querySelectorAll("form[data-auto-filter]")) {
  if (form.method.toLowerCase() !== "get" || !form.requestSubmit) continue;
  form.addEventListener("change", (event) => {
    if (!event.target.matches("select, input[type=checkbox], input[type=date]")) return;
    if (event.target.matches("input[type=date]") &&
        (!event.target.value || !event.target.validity.valid)) return;
    // Filter forms contain only filter controls, so all pagination resets to one.
    form.requestSubmit();
  });
  for (const button of form.querySelectorAll("[data-filter-submit]")) button.hidden = true;
  const hint = document.createElement("span");
  hint.className = "filter-hint";
  hint.id = `auto-filter-hint-${++filterNumber}`;
  hint.textContent = "Фильтры применяются автоматически";
  form.append(hint);
  for (const control of form.querySelectorAll("select, input[type=checkbox], input[type=date]")) {
    const descriptions = (control.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
    descriptions.push(hint.id);
    control.setAttribute("aria-describedby", descriptions.join(" "));
  }
}

// Browsers can restore a changed select from the page we left even when Back
// returns to an earlier filter URL. Server-rendered defaults match that URL.
window.addEventListener("pageshow", () => {
  for (const form of document.querySelectorAll("form[data-auto-filter]")) {
    if (form.method.toLowerCase() === "get") form.reset();
  }
});
