/* Progressive enhancement: sending/clearing remain native, CSRF-protected POST forms. */
(() => {
  const form = document.querySelector('[data-assistant-form]');
  if (!form) return;
  const field = form.querySelector('textarea');
  document.querySelector('[data-starters]').hidden = false;
  document.querySelectorAll('[data-prompt]').forEach(button => {
    button.addEventListener('click', () => {
      field.value = button.dataset.prompt;
      field.focus();
    });
  });
  const send = form.querySelector('[data-send]');
  form.addEventListener('submit', () => {
    send.disabled = true;
    field.readOnly = true;
    document.querySelectorAll('[data-prompt], .assistant-chat-heading button').forEach(button => {
      button.disabled = true;
    });
    send.textContent = 'Отправляем вопрос…';
    form.setAttribute('aria-busy', 'true');
    form.querySelector('[data-pending]').hidden = false;
  });
  window.addEventListener('pageshow', () => {
    send.disabled = false;
    field.readOnly = false;
    document.querySelectorAll('[data-prompt], .assistant-chat-heading button').forEach(button => {
      button.disabled = false;
    });
    send.textContent = 'Отправить вопрос';
    form.removeAttribute('aria-busy');
    form.querySelector('[data-pending]').hidden = true;
  });
})();
