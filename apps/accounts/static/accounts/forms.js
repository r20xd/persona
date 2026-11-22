"use strict";
// After navigation (including fragment focus), announce server validation errors.
window.addEventListener("pageshow", () => {
  const errorSummary = document.querySelector("[data-error-summary]");
  if (errorSummary) errorSummary.focus();
});
