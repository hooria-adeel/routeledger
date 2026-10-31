import { api } from '../api.js';
import { badge, dataTable, el, errorBox, fdatetime, openModal, pager, spinner } from '../ui.js';

const TABLES = ['products', 'retailers', 'branches', 'areas', 'orders', 'order_items', 'categories'];
const HIDDEN_FIELDS = new Set(['updated_at', 'created_at']);

const show = (v) => (v === null || v === undefined ? '—' : typeof v === 'object' ? JSON.stringify(v) : String(v));

function openDetails(row) {
  const old = row.old_value || {}, now = row.new_value || {};
  const keys = [...new Set([...Object.keys(old), ...Object.keys(now)])].filter((k) => !HIDDEN_FIELDS.has(k));
  const lines = keys.filter((k) => row.action !== 'UPDATE' || show(old[k]) !== show(now[k]));
  const columns = [
    { key: 'field', label: 'Field' },
    { key: 'before', label: 'Before', cls: 'wrap', render: (l) => (row.action === 'INSERT' ? '—' : el('span', { class: row.action === 'UPDATE' ? 'diff-old' : '' }, show(old[l.field]))) },
    { key: 'after', label: 'After', cls: 'wrap', render: (l) => (row.action === 'DELETE' ? '—' : el('span', { class: 'diff-new' }, show(now[l.field]))) },
  ];
  openModal(`${row.action} · ${row.table_name} #${row.record_id}`, el('div', {},
    el('p', { class: 'muted' }, `${row.employee || 'System'} · ${fdatetime(row.logged_at)}`),
    dataTable({ columns, rows: lines.map((field) => ({ field })) })), { wide: true });
}

export async function render(root) {
  const state = { page: 1, pageSize: 25, table_name: '', action: '', record_id: '' };
  const tableBox = el('div', {}), pagerBox = el('div', {});
  const tableSel = el('select', { 'aria-label': 'Table', onchange: () => { state.table_name = tableSel.value; state.page = 1; load(); } },
    el('option', { value: '' }, 'All tables'), TABLES.map((t) => el('option', { value: t }, t)));
  const actionSel = el('select', { 'aria-label': 'Action', onchange: () => { state.action = actionSel.value; state.page = 1; load(); } },
    el('option', { value: '' }, 'All actions'), ['INSERT', 'UPDATE', 'DELETE'].map((a) => el('option', { value: a }, a)));
  const idInput = el('input', { type: 'number', min: 1, placeholder: 'Record #', 'aria-label': 'Record number',
    onchange: () => { state.record_id = idInput.value; state.page = 1; load(); } });

  root.replaceChildren(
    el('div', { class: 'page-head' }, el('h2', {}, 'Activity log')),
    el('p', { class: 'muted' }, 'Every change to the data is recorded here. Nobody can edit or delete this log.'),
    el('div', { class: 'toolbar' },
      el('div', { class: 'field' }, el('label', {}, 'Table'), tableSel),
      el('div', { class: 'field' }, el('label', {}, 'Action'), actionSel),
      el('div', { class: 'field' }, el('label', {}, 'Record'), idInput)),
    tableBox, pagerBox);

  async function load() {
    tableBox.replaceChildren(spinner()); pagerBox.replaceChildren();
    try {
      const data = await api.get('/activity-log', { table_name: state.table_name, action: state.action, record_id: state.record_id, page: state.page, page_size: state.pageSize });
      tableBox.replaceChildren(dataTable({
        rows: data.items, emptyText: 'No activity matches these filters.', onRowClick: openDetails,
        columns: [
          { key: 'logged_at', label: 'When', render: (r) => fdatetime(r.logged_at) },
          { key: 'employee', label: 'Who', render: (r) => r.employee || 'System' },
          { key: 'action', label: 'Action', render: (r) => badge(r.action, r.action === 'DELETE' ? 'bad' : r.action === 'INSERT' ? 'good' : 'warn') },
          { key: 'table_name', label: 'Table' },
          { key: 'record_id', label: 'Record', render: (r) => `#${r.record_id}` },
          { key: '_d', label: '', cls: 'actions', render: () => el('span', { class: 'muted' }, 'Details ›') },
        ] }));
      pagerBox.replaceChildren(pager({ page: state.page, pageSize: state.pageSize, total: data.total, onPage: (p) => { state.page = p; load(); } }));
    } catch (p) { tableBox.replaceChildren(errorBox(p.message, load)); }
  }
  load();
}
