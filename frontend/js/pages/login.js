import { api } from '../api.js';
import { el, icon } from '../ui.js';

export function renderLogin(root, onSuccess, notice) {
  const errorLine = el('div', { class: 'form-error', role: 'alert', hidden: !notice }, notice || '');
  const email = el('input', { id: 'email', type: 'email', required: true, autocomplete: 'username', maxlength: 150, placeholder: 'you@company.com' });
  const password = el('input', { id: 'password', type: 'password', required: true, autocomplete: 'current-password', maxlength: 128 });
  const button = el('button', { class: 'btn btn-primary', type: 'submit' }, 'Log in');

  // Shown only when the server is configured for a public demo (DEMO_EMAIL and
  // DEMO_PASSWORD). A real installation leaves it hidden.
  const demoBox = el('div', { class: 'demo-box', hidden: true });
  api.get('/auth/demo').then((demo) => {
    if (!demo || !demo.enabled) return;
    const fill = el('button', { class: 'btn btn-ghost btn-sm', type: 'button' }, 'Use demo account');
    fill.addEventListener('click', () => {
      email.value = demo.email;
      password.value = demo.password;
      errorLine.hidden = true;
      password.focus();
    });
    demoBox.replaceChildren(
      el('div', {}, el('b', {}, 'Demo access'), ' — read-only account for this public demo.'),
      el('div', { class: 'demo-row' },
        el('code', {}, demo.email + ' / ' + demo.password),
        fill));
    demoBox.hidden = false;
  }).catch(() => { /* the hint is optional; login still works */ });

  const form = el('form', { class: 'form', onsubmit: async (event) => {
    event.preventDefault();
    errorLine.hidden = true;
    button.disabled = true;
    try {
      await api.post('/auth/login', { email: email.value.trim(), password: password.value });
      password.value = '';
      onSuccess();
    } catch (problem) {
      errorLine.textContent = problem.message;
      errorLine.hidden = false;
      password.value = '';
      password.focus();
    } finally { button.disabled = false; }
  } },
    el('div', { class: 'field' }, el('label', { for: 'email' }, 'Email'), email),
    el('div', { class: 'field' }, el('label', { for: 'password' }, 'Password'), password),
    errorLine, button);

  const point = (title, text) => el('li', {}, el('div', { class: 'dot' }, icon('activity')), el('div', {}, el('b', {}, title), el('span', {}, text)));
  root.replaceChildren(el('div', { class: 'login-page' },
    el('section', { class: 'login-hero' },
      el('div', { class: 'hero-brand' }, el('img', { src: '/img/logo-mark.svg', alt: '' }), el('b', {}, 'ROUTELEDGER')),
      el('h2', {}, 'One place for every product, retailer and ', el('em', {}, 'order.')),
      el('p', { class: 'hero-lead' }, 'Great distribution starts with data everyone can trust.'),
      el('ul', { class: 'hero-points' },
        point('Always the latest data', 'No more Excel copies sent around by email.'),
        point('The right access for each person', 'Everyone can look. Only approved staff can change.'),
        point('Every change is recorded', 'See who changed what, and when.'))),
    el('div', { class: 'login-card' },
      el('div', { class: 'login-brand' }, el('img', { src: '/img/logo-mark.svg', alt: '' }), el('h1', {}, 'ROUTELEDGER')),
      el('p', { class: 'tagline' }, 'Every route, on the record.'),
      el('h2', {}, 'Welcome back'),
      el('p', { class: 'sub' }, 'Log in to the Distribution Management System.'),
      form,
      demoBox,
      el('p', { class: 'login-foot' }, 'Authorised employees only. Activity is recorded.'))));
  email.focus();
}
