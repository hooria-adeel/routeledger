// One reusable page for "list + search + add + edit + delete".
// Products, retailers, areas and employees all use it.

import { api, ApiError } from './api.js';
import { badge, clear, confirmBox, dataTable, debounce, el, errorBox, formModal, pager, spinner, toast } from './ui.js';

export async function crudPage(root, ctx, cfg) {
  const canEdit = ctx.can('can_edit') && cfg.allowEdit !== false;
  const canDelete = ctx.can('can_delete') && cfg.allowDelete !== false;
  const paged = cfg.paged !== false;
  const state = { page: 1, pageSize: cfg.pageSize || 25, ...(cfg.defaultSort || {}), filters: {} };
  let fieldCache = null;
  const getFields = async () => (fieldCache ||= await cfg.fields());

  const tableBox = el('div', {});
  const pagerBox = el('div', {});
  const addBtn = canEdit && cfg.canAdd !== false
    ? el('button', { class: 'btn btn-primary', type: 'button', onclick: addRecord }, `+ Add ${cfg.singular}`) : null;

  // ----- filters -----
  const toolbar = el('div', { class: 'toolbar' });
  let sortSelect = null;
  const syncSort = () => {
    if (!sortSelect) return;
    const now = `${state.sort}:${state.order}`;
    sortSelect.value = [...sortSelect.options].some((o) => o.value === now) ? now : '';
  };
  for (const f of cfg.filters || []) {
    if (f.kind === 'search') {
      const input = el('input', { type: 'search', placeholder: f.placeholder || 'Search…', 'aria-label': 'Search',
        oninput: debounce(() => { state.filters.search = input.value.trim(); state.page = 1; load(); }, 300) });
      toolbar.append(el('div', { class: 'field grow' }, el('label', {}, 'Search'), input));
    } else if (f.kind === 'select') {
      const select = el('select', { 'aria-label': f.all, onchange: () => { state.filters[f.name] = select.value; state.page = 1; load(); } },
        el('option', { value: '' }, f.all));
      toolbar.append(el('div', { class: 'field' }, el('label', {}, f.label || ''), select));
      f.options().then((opts) => opts.forEach((o) => select.append(el('option', { value: o.value }, o.label)))).catch(() => {});
    }
  }

  if (cfg.sortOptions && paged) {
    sortSelect = el('select', { 'aria-label': 'Sort by', onchange: () => {
      if (!sortSelect.value) return;
      [state.sort, state.order] = sortSelect.value.split(':');
      state.page = 1; load();
    } }, el('option', { value: '' }, 'Sorted by column'),
    cfg.sortOptions.map((o) => el('option', { value: `${o.sort}:${o.order}` }, o.label)));
    toolbar.append(el('div', { class: 'field' }, el('label', {}, 'Sort by'), sortSelect));
    syncSort();
  }

  root.replaceChildren(
    el('div', { class: 'page-head' }, el('h2', {}, cfg.title), addBtn),
    cfg.filters && cfg.filters.length ? toolbar : null,
    tableBox, pagerBox);

  // ----- loading -----
  async function load() {
    tableBox.replaceChildren(spinner());
    pagerBox.replaceChildren();
    try {
      let rows; let total;
      if (paged) {
        const data = await api.get(cfg.endpoint, { ...state.filters, sort: state.sort, order: state.order, page: state.page, page_size: state.pageSize });
        rows = data.items; total = data.total;
      } else {
        rows = await api.get(cfg.endpoint);
        const q = (state.filters.search || '').toLowerCase();
        if (q) rows = rows.filter((r) => (cfg.clientSearch || []).some((k) => String(r[k] ?? '').toLowerCase().includes(q)));
        total = rows.length;
      }
      draw(rows, total);
    } catch (problem) {
      tableBox.replaceChildren(errorBox(problem.message, load));
    }
  }

  function draw(rows, total) {
    syncSort();
    const columns = [...cfg.columns];
    columns.push({ key: '_actions', label: '', cls: 'actions', render: (row) => {
      const buttons = [];
      for (const extra of (cfg.rowActions ? cfg.rowActions(row, load, ctx) : [])) buttons.push(extra);
      if (canEdit) buttons.push(el('button', { class: 'btn btn-sm', type: 'button', onclick: (e) => { e.stopPropagation(); editRecord(row); } }, 'Edit'));
      if (canDelete) buttons.push(el('button', { class: 'btn btn-sm btn-danger', type: 'button', onclick: (e) => { e.stopPropagation(); deleteRecord(row); } }, 'Delete'));
      return buttons;
    } });
    tableBox.replaceChildren(dataTable({
      columns, rows, sort: state.sort, order: state.order, emptyText: cfg.emptyText || `No ${cfg.title.toLowerCase()} found.`,
      onSort: paged ? (key) => { state.order = state.sort === key && state.order === 'asc' ? 'desc' : 'asc'; state.sort = key; state.page = 1; load(); } : null,
    }));
    pagerBox.replaceChildren(paged ? pager({ page: state.page, pageSize: state.pageSize, total, onPage: (p) => { state.page = p; load(); } }) : '');
  }

  // ----- add / edit / delete -----
  async function addRecord() {
    const fields = await getFields();
    formModal({ title: `Add ${cfg.singular}`, fields: fields.filter((f) => !f.editOnly), submitLabel: 'Add',
      initial: cfg.addDefaults || {},
      onSubmit: async (values, modal) => {
        await api.post(cfg.endpoint, cfg.toCreateBody ? cfg.toCreateBody(values) : values);
        modal.close(); toast(`${cap(cfg.singular)} added.`); load();
      } });
  }

  async function editRecord(row) {
    const fields = (await getFields()).filter((f) => !f.addOnly);
    const initial = cfg.initialFromRow(row);
    formModal({ title: `Edit ${cfg.singular}`, fields, initial,
      onSubmit: async (values, modal) => {
        const changes = {};
        for (const [key, value] of Object.entries(values)) {
          if (value === null && !fields.find((f) => f.name === key).clearable) continue;
          if (String(value ?? '') !== String(initial[key] ?? '')) changes[key] = value;
        }
        if (!Object.keys(changes).length) { modal.close(); return; }
        try {
          await api.patch(`${cfg.endpoint}/${row[cfg.idKey]}`, { ...(cfg.toUpdateBody ? cfg.toUpdateBody(changes) : changes), ...(cfg.noVersion ? {} : { version: row.version }) });
        } catch (problem) {
          if (problem instanceof ApiError && problem.status === 409 && /changed this record/i.test(problem.message)) {
            modal.close(); toast(problem.message, 'error'); load(); return;
          }
          throw problem;
        }
        modal.close(); toast(`${cap(cfg.singular)} saved.`); load();
      } });
  }

  async function deleteRecord(row) {
    const ok = await confirmBox(`Delete ${cfg.singular} “${cfg.label(row)}”? It is hidden, not destroyed, and a manager can restore it.`);
    if (!ok) return;
    try {
      await api.del(`${cfg.endpoint}/${row[cfg.idKey]}`);
      toast(`${cap(cfg.singular)} deleted.`); load();
    } catch (problem) { toast(problem.message, 'error'); }
  }

  load();
}

const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
export { badge, clear };
