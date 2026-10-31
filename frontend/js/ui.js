// Small building blocks for the pages.
// SECURITY NOTE: pages are built with createElement and text nodes (never from
// HTML strings), so text that comes from the database can never run as code (XSS).

import { ApiError } from './api.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  let value;
  let hasValue = false;
  for (const [key, val] of Object.entries(attrs || {})) {
    if (val === false || val === null || val === undefined) continue;
    if (key === 'class') node.className = val;
    else if (key === 'value') { value = val; hasValue = true; }
    else if (key.startsWith('on') && typeof val === 'function') node.addEventListener(key.slice(2), val);
    else node.setAttribute(key, val === true ? '' : val);
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  if (hasValue) node.value = value;       // after the options exist (for <select>)
  return node;
}

export function svg(tag, attrs = {}, ...children) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [key, val] of Object.entries(attrs)) node.setAttribute(key, val);
  for (const child of children.flat()) {
    if (child !== null && child !== undefined) node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

export const clear = (node) => node.replaceChildren();

// ---------- icons ----------
const ICONS = {
  dashboard: [['rect', { x: 3, y: 3, width: 7, height: 9 }], ['rect', { x: 14, y: 3, width: 7, height: 5 }], ['rect', { x: 14, y: 12, width: 7, height: 9 }], ['rect', { x: 3, y: 16, width: 7, height: 5 }]],
  products: [['path', { d: 'M21 8l-9-5-9 5v8l9 5 9-5z' }], ['path', { d: 'M3 8l9 5 9-5M12 13v8' }]],
  retailers: [['path', { d: 'M4 9l1.5-5h13L20 9' }], ['path', { d: 'M4 9v11h16V9M9 20v-6h6v6' }], ['path', { d: 'M4 9a2.7 2.7 0 005.3 0 2.7 2.7 0 005.4 0A2.7 2.7 0 0020 9' }]],
  areas: [['path', { d: 'M12 21s-7-6.2-7-11a7 7 0 0114 0c0 4.8-7 11-7 11z' }], ['circle', { cx: 12, cy: 10, r: 2.5 }]],
  orders: [['rect', { x: 6, y: 4, width: 12, height: 17, rx: 2 }], ['path', { d: 'M9 4h6v3H9zM9 12h6M9 16h6' }]],
  employees: [['circle', { cx: 9, cy: 8, r: 3 }], ['path', { d: 'M3 20c0-3.5 2.7-6 6-6s6 2.5 6 6' }], ['circle', { cx: 17, cy: 9, r: 2.5 }], ['path', { d: 'M17 14c2.5 0 4 1.8 4 5' }]],
  activity: [['path', { d: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z' }], ['path', { d: 'M9 12l2 2 4-4' }]],
  logout: [['path', { d: 'M9 4H5v16h4M16 8l4 4-4 4M20 12H9' }]],
  sun: [['circle', { cx: 12, cy: 12, r: 4 }], ['path', { d: 'M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5' }]],
  moon: [['path', { d: 'M20 14a8 8 0 11-10-10 6.5 6.5 0 0010 10z' }]],
  menu: [['path', { d: 'M4 6h16M4 12h16M4 18h16' }]],
};

export function icon(name) {
  const root = svg('svg', { viewBox: '0 0 24 24', class: 'icon', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true' });
  for (const [tag, attrs] of ICONS[name] || []) root.append(svg(tag, attrs));
  return root;
}

// ---------- formatting ----------
export const money = (v, decimals = 2) =>
  v === null || v === undefined ? '' : 'Rs ' + Number(v).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
export const compact = (v) =>
  'Rs ' + new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(Number(v));
export const num = (v) => Number(v).toLocaleString('en-US');
export const fdate = (v) =>
  v ? new Date(`${String(v).slice(0, 10)}T00:00:00`).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
export const fdatetime = (v) =>
  v ? new Date(v).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—';

export function debounce(fn, ms = 300) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

// ---------- messages ----------
let toastBox;
export function toast(message, type = 'ok') {
  if (!toastBox) { toastBox = el('div', { class: 'toasts', role: 'status', 'aria-live': 'polite' }); document.body.append(toastBox); }
  const t = el('div', { class: `toast ${type === 'error' ? 'error' : ''}` }, message);
  toastBox.append(t);
  setTimeout(() => t.remove(), type === 'error' ? 6000 : 3200);
}

export const spinner = () => el('div', { class: 'spinner', role: 'status', 'aria-label': 'Loading' });

export function errorBox(message, onRetry) {
  return el('div', { class: 'error-box', role: 'alert' }, el('span', {}, message),
    onRetry ? el('button', { class: 'btn btn-sm', type: 'button', onclick: onRetry }, 'Try again') : null);
}

// ---------- modal ----------
const openModals = [];
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && openModals.length) openModals[openModals.length - 1].close();
});

export function closeAllModals() {
  while (openModals.length) openModals[openModals.length - 1].close();
}

export function openModal(title, body, { wide = false } = {}) {
  const heading = el('h2', {}, title);
  const closeBtn = el('button', { class: 'x-btn', type: 'button', 'aria-label': 'Close' }, '×');
  const bodyBox = el('div', { class: 'modal-body' }, body);
  const dialog = el('div', { class: `modal ${wide ? 'wide' : ''}`, role: 'dialog', 'aria-modal': 'true', 'aria-label': title },
    el('div', { class: 'modal-head' }, heading, closeBtn), bodyBox);
  const overlay = el('div', { class: 'overlay' }, dialog);
  const handle = {
    body: bodyBox,
    setBody(node) { bodyBox.replaceChildren(node); },
    close() { const i = openModals.indexOf(handle); if (i >= 0) openModals.splice(i, 1); overlay.remove(); },
  };
  closeBtn.addEventListener('click', handle.close);
  overlay.addEventListener('mousedown', (event) => { if (event.target === overlay) handle.close(); });
  document.body.append(overlay);
  openModals.push(handle);
  const first = bodyBox.querySelector('input, select, button');
  if (first) first.focus();
  return handle;
}

export function confirmBox(message, { okLabel = 'Delete', danger = true } = {}) {
  return new Promise((resolve) => {
    let answered = false;
    const finish = (answer) => { if (!answered) { answered = true; modal.close(); resolve(answer); } };
    const body = el('div', {}, el('p', {}, message),
      el('div', { class: 'form-actions' },
        el('button', { class: 'btn', type: 'button', onclick: () => finish(false) }, 'Cancel'),
        el('button', { class: `btn ${danger ? 'btn-solid-danger' : 'btn-primary'}`, type: 'button', onclick: () => finish(true) }, okLabel)));
    const modal = openModal('Please confirm', body);
    const baseClose = modal.close;
    modal.close = () => { baseClose(); if (!answered) { answered = true; resolve(false); } };
  });
}

// ---------- forms ----------
// fields: [{name,label,type,required,options,coerce,min,max,step,maxlength,placeholder,help,autocomplete}]
//   type: text | number | date | password | select | combo (type-to-search list)
export function formModal({ title, fields, initial = {}, submitLabel = 'Save', onSubmit, wide = false }) {
  const inputs = {};
  const errorLine = el('div', { class: 'form-error', role: 'alert', hidden: true });
  const form = el('form', { class: 'form' });
  const uid = Math.random().toString(36).slice(2, 7);

  for (const f of fields) {
    const id = `f-${uid}-${f.name}`;
    const common = { id, name: f.name, required: !!f.required, placeholder: f.placeholder, maxlength: f.maxlength,
      min: f.min, max: f.max, step: f.step, autocomplete: f.autocomplete || 'off' };
    let input;
    if (f.type === 'select') {
      input = el('select', { id, name: f.name, required: !!f.required },
        (f.options || []).map((o) => el('option', { value: o.value }, o.label)));
      input.value = initial[f.name] ?? (f.options && f.options[0] ? f.options[0].value : '');
    } else if (f.type === 'combo') {
      const listId = `${id}-list`;
      const shown = (f.options || []).find((o) => String(o.value) === String(initial[f.name]));
      input = el('input', { ...common, type: 'text', list: listId, value: shown ? shown.label : '' });
      form.append(el('datalist', { id: listId }, (f.options || []).map((o) => el('option', { value: o.label }))));
    } else {
      input = el('input', { ...common, type: f.type || 'text', value: initial[f.name] ?? '' });
    }
    inputs[f.name] = input;
    form.append(el('div', { class: 'field' }, el('label', { for: id }, f.label + (f.required ? ' *' : '')), input,
      f.help ? el('div', { class: 'help' }, f.help) : null));
  }

  const submitBtn = el('button', { class: 'btn btn-primary', type: 'submit' }, submitLabel);
  form.append(errorLine, el('div', { class: 'form-actions' },
    el('button', { class: 'btn', type: 'button', onclick: () => modal.close() }, 'Cancel'), submitBtn));

  function collect() {
    const out = {};
    for (const f of fields) {
      let raw = inputs[f.name].value;
      if (f.type !== 'password') raw = raw.trim();
      if (f.type === 'combo') {
        const match = (f.options || []).find((o) => o.label.toLowerCase() === raw.toLowerCase());
        if (raw && !match) throw new Error(`${f.label}: please choose one from the list.`);
        out[f.name] = match ? match.value : null;
      } else if (f.type === 'number' || f.coerce === 'int' || f.coerce === 'number') {
        out[f.name] = raw === '' ? null : Number(raw);
      } else if (f.coerce === 'bool') {
        out[f.name] = raw === 'true';
      } else {
        out[f.name] = raw === '' ? null : raw;
      }
    }
    return out;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorLine.hidden = true;
    submitBtn.disabled = true;
    try {
      await onSubmit(collect(), modal);
    } catch (problem) {
      errorLine.textContent = problem instanceof Error ? problem.message : 'Something went wrong.';
      errorLine.hidden = false;
    } finally {
      submitBtn.disabled = false;
    }
  });

  const modal = openModal(title, form, { wide });
  return modal;
}

// ---------- tables ----------
export function dataTable({ columns, rows, sort, order, onSort, onRowClick, emptyText = 'No records found.' }) {
  const head = el('tr', {}, columns.map((c) => {
    const sortable = c.sort && onSort;
    const arrow = sortable && sort === c.sort ? (order === 'asc' ? ' ▲' : ' ▼') : '';
    return el('th', {
      class: `${c.align === 'right' ? 'num' : ''} ${sortable ? 'sortable' : ''}`,
      scope: 'col',
      'aria-sort': sortable && sort === c.sort ? (order === 'asc' ? 'ascending' : 'descending') : false,
      tabindex: sortable ? '0' : false,
      onclick: sortable ? () => onSort(c.sort) : null,
      onkeydown: sortable ? (e) => { if (e.key === 'Enter') onSort(c.sort); } : null,
    }, c.label + arrow);
  }));
  const body = rows.map((row) => el('tr', {
    class: onRowClick ? 'clickable' : '',
    onclick: onRowClick ? () => onRowClick(row) : null,
  }, columns.map((c) => {
    const content = c.render ? c.render(row) : row[c.key];
    return el('td', { class: `${c.align === 'right' ? 'num' : ''} ${c.cls || ''}` }, content === null || content === undefined || content === '' ? '—' : content);
  })));
  if (!rows.length) return el('div', { class: 'table-wrap' }, el('div', { class: 'empty' }, emptyText));
  return el('div', { class: 'table-wrap' }, el('table', {}, el('thead', {}, head), el('tbody', {}, body)));
}

export function pager({ page, pageSize, total, onPage }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const from = total ? (page - 1) * pageSize + 1 : 0;
  const to = Math.min(total, page * pageSize);
  return el('div', { class: 'pager' },
    el('span', {}, `Showing ${from}–${to} of ${num(total)}`),
    el('div', { class: 'buttons' },
      el('button', { class: 'btn btn-sm', type: 'button', disabled: page <= 1, onclick: () => onPage(page - 1) }, '‹ Previous'),
      el('span', {}, `Page ${page} of ${pages}`),
      el('button', { class: 'btn btn-sm', type: 'button', disabled: page >= pages, onclick: () => onPage(page + 1) }, 'Next ›')));
}

export function badge(text, kind = '') { return el('span', { class: `badge ${kind}` }, text); }

export { ApiError };

// ---------- tooltips (hover or keyboard focus) ----------
let tipBox;
function placeTip(x, y) {
  if (!tipBox) return;
  const pad = 14;
  const box = tipBox.getBoundingClientRect();
  let left = x + pad;
  let top = y + pad;
  if (left + box.width > window.innerWidth - 8) left = x - box.width - pad;
  if (top + box.height > window.innerHeight - 8) top = y - box.height - pad;
  tipBox.style.left = `${Math.max(8, left)}px`;
  tipBox.style.top = `${Math.max(8, top)}px`;
}
export function tooltip(node, makeContent) {
  const show = (x, y) => {
    if (!tipBox) { tipBox = el('div', { class: 'tip', role: 'tooltip' }); document.body.append(tipBox); }
    tipBox.replaceChildren(...makeContent());
    tipBox.classList.add('on');
    placeTip(x, y);
  };
  const hide = () => { if (tipBox) tipBox.classList.remove('on'); };
  node.addEventListener('mouseenter', (e) => show(e.clientX, e.clientY));
  node.addEventListener('mousemove', (e) => placeTip(e.clientX, e.clientY));
  node.addEventListener('mouseleave', hide);
  node.addEventListener('focus', () => { const r = node.getBoundingClientRect(); show(r.left + r.width / 2, r.top); });
  node.addEventListener('blur', hide);
}
