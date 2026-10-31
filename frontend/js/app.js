import { api } from './api.js';
import { renderLogin } from './pages/login.js';
import { clear, closeAllModals, el, errorBox, icon, spinner, toast } from './ui.js';

const PAGES = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', module: './pages/dashboard.js' },
  { id: 'products', label: 'Products', icon: 'products', module: './pages/products.js' },
  { id: 'retailers', label: 'Retailers', icon: 'retailers', module: './pages/retailers.js' },
  { id: 'areas', label: 'Areas', icon: 'areas', module: './pages/areas.js' },
  { id: 'orders', label: 'Orders', icon: 'orders', module: './pages/orders.js' },
  { id: 'employees', label: 'Employees', icon: 'employees', module: './pages/employees.js', needs: 'can_manage' },
  { id: 'activity', label: 'Activity log', icon: 'activity', module: './pages/activity.js', needs: 'can_delete' },
];

const root = document.getElementById('app');
let user = null;
let routeToken = 0;

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  try { localStorage.setItem('routeledger-theme', theme); } catch (e) { /* private mode */ }
}

function showLogin(notice) {
  user = null;
  renderLogin(root, start, notice);
}

async function start() {
  try {
    user = await api.get('/auth/me');
  } catch (problem) {
    showLogin();
    return;
  }
  buildShell();
  route();
}

function buildShell() {
  const pages = PAGES.filter((p) => !p.needs || user[p.needs]);
  const nav = el('nav', { class: 'nav', 'aria-label': 'Main' }, pages.map((p) =>
    el('a', { href: `#/${p.id}`, 'data-page': p.id }, icon(p.icon), p.label)));
  const title = el('h1', { id: 'page-title' }, '');
  const themeBtn = el('button', { class: 'btn btn-ghost', type: 'button', 'aria-label': 'Switch light or dark mode', onclick: () => {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    setTheme(dark ? 'light' : 'dark');
    refreshThemeIcon();
  } });
  const SIZES = ['small', 'normal', 'large'];
  const sizeBtn = el('button', { class: 'btn btn-ghost text-size-btn', type: 'button', title: 'Change text size',
    'aria-label': 'Change text size', onclick: () => {
      const now = document.documentElement.getAttribute('data-size') || 'normal';
      const next = SIZES[(SIZES.indexOf(now) + 1) % SIZES.length];
      document.documentElement.setAttribute('data-size', next);
      try { localStorage.setItem('routeledger-size', next); } catch (e) { /* private mode */ }
      toast(`Text size: ${next}`);
    } }, 'Aa');
  const refreshThemeIcon = () => themeBtn.replaceChildren(icon(document.documentElement.getAttribute('data-theme') === 'dark' ? 'sun' : 'moon'));
  refreshThemeIcon();

  const shell = el('div', { class: 'shell' },
    el('aside', { class: 'sidebar' },
      el('div', { class: 'brand' }, el('img', { src: '/img/logo-mark.svg', alt: '' }),
        el('div', {}, el('b', {}, 'ROUTELEDGER'), el('span', {}, 'Every route, on the record.'))),
      nav,
      el('div', { class: 'side-foot' }, 'Distribution Management System')),
    el('div', { class: 'main' },
      el('header', { class: 'topbar' },
        el('button', { class: 'btn btn-ghost menu-btn', type: 'button', 'aria-label': 'Open menu', onclick: () => shell.classList.toggle('open') }, icon('menu')),
        title, sizeBtn, themeBtn,
        el('div', { class: 'user-chip' },
          el('div', { class: 'avatar', 'aria-hidden': 'true' }, (user.full_name || '?').charAt(0).toUpperCase()),
          el('div', { class: 'who' }, el('b', {}, user.full_name), el('span', {}, user.role)),
          el('button', { class: 'btn btn-sm', type: 'button', onclick: logout }, icon('logout'), 'Log out'))),
      el('main', { class: 'content', id: 'view' })));
  nav.addEventListener('click', () => shell.classList.remove('open'));
  root.replaceChildren(shell);
}

async function logout() {
  try { await api.post('/auth/logout'); } catch (e) { /* the cookie is cleared by the server if it can */ }
  window.location.hash = '';
  showLogin();
}

async function route() {
  if (!user) return;
  const pages = PAGES.filter((p) => !p.needs || user[p.needs]);
  const wanted = (window.location.hash.replace(/^#\//, '') || 'dashboard').split('?')[0];
  const page = pages.find((p) => p.id === wanted) || pages[0];
  if (wanted !== page.id) { window.location.hash = `#/${page.id}`; return; }

  closeAllModals();                      // open windows belong to the page we are leaving
  const view = document.getElementById('view');
  document.getElementById('page-title').textContent = page.label;
  document.title = `${page.label} · RouteLedger`;
  document.querySelectorAll('.nav a').forEach((a) => a.classList.toggle('active', a.dataset.page === page.id));
  const token = ++routeToken;
  // Every visit gets its own container. If you click to another page quickly, a slow
  // page that finishes late can only draw into its old, removed container.
  const container = el('div', { class: 'page' }, spinner());
  view.replaceChildren(container);
  try {
    const module = await import(page.module);
    if (token !== routeToken) return;
    container.replaceChildren();
    await module.render(container, { user, can: (permission) => Boolean(user[permission]) });
  } catch (problem) {
    if (token === routeToken) container.replaceChildren(errorBox(problem.message || 'This page could not be loaded.', route));
  }
}

window.addEventListener('hashchange', route);
window.addEventListener('session-expired', () => { if (user) showLogin('Your session has ended. Please log in again.'); });
start();
