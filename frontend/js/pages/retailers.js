import { api } from '../api.js';
import { crudPage } from '../crud.js';
import { confirmBox, dataTable, el, errorBox, formModal, money, openModal, spinner, toast } from '../ui.js';

async function areaOptions() {
  return (await api.get('/areas')).map((a) => ({ value: a.area_id, label: a.name }));
}

// The list of shops (branches) of one retailer, with add / edit / delete.
function openBranches(retailer, ctx, reloadList) {
  const modal = openModal(`Branches of ${retailer.name}`, spinner(), { wide: true });

  async function show() {
    let data;
    try { data = await api.get(`/retailers/${retailer.retailer_id}`); } catch (p) { modal.setBody(errorBox(p.message, show)); return; }
    const canEdit = ctx.can('can_edit'), canDelete = ctx.can('can_delete');
    const columns = [
      { key: 'branch_name', label: 'Branch' },
      { key: 'area', label: 'Area' },
      { key: '_a', label: '', cls: 'actions', render: (b) => [
        canEdit ? el('button', { class: 'btn btn-sm', type: 'button', onclick: () => edit(b) }, 'Edit') : null,
        canDelete ? el('button', { class: 'btn btn-sm btn-danger', type: 'button', onclick: () => remove(b) }, 'Delete') : null] },
    ];
    modal.setBody(el('div', {},
      canEdit ? el('div', { class: 'form-actions' }, el('button', { class: 'btn btn-primary', type: 'button', onclick: add }, '+ Add branch')) : null,
      el('div', { class: 'sep' }),
      dataTable({ columns, rows: data.branches, emptyText: 'This retailer has no branches yet.' })));
  }

  async function fields() {
    return [
      { name: 'area_id', label: 'Area', type: 'select', coerce: 'int', required: true, options: await areaOptions() },
      { name: 'branch_name', label: 'Branch name', required: true, maxlength: 80 },
    ];
  }
  async function add() {
    formModal({ title: 'Add branch', fields: await fields(), submitLabel: 'Add', onSubmit: async (v, m) => {
      await api.post('/branches', { retailer_id: retailer.retailer_id, ...v });
      m.close(); toast('Branch added.'); show(); reloadList();
    } });
  }
  async function edit(b) {
    const initial = { area_id: b.area_id, branch_name: b.branch_name };
    formModal({ title: 'Edit branch', fields: await fields(), initial, onSubmit: async (v, m) => {
      const changes = {};
      for (const k of Object.keys(v)) if (String(v[k]) !== String(initial[k])) changes[k] = v[k];
      if (Object.keys(changes).length) {
        try { await api.patch(`/branches/${b.branch_id}`, { ...changes, version: b.version }); }
        catch (p) { if (p.status === 409) { m.close(); toast(p.message, 'error'); show(); return; } throw p; }
      }
      m.close(); toast('Branch saved.'); show();
    } });
  }
  async function remove(b) {
    if (!(await confirmBox(`Delete the branch “${b.branch_name}”?`))) return;
    try { await api.del(`/branches/${b.branch_id}`); toast('Branch deleted.'); show(); reloadList(); } catch (p) { toast(p.message, 'error'); }
  }
  show();
}

export function render(root, ctx) {
  return crudPage(root, ctx, {
    title: 'Retailers', singular: 'retailer', endpoint: '/retailers', idKey: 'retailer_id',
    defaultSort: { sort: 'name', order: 'asc' },
    sortOptions: [
      { sort: 'name', order: 'asc', label: 'Name (A → Z)' },
      { sort: 'name', order: 'desc', label: 'Name (Z → A)' },
      { sort: 'sales', order: 'desc', label: 'Sales (highest first)' },
      { sort: 'sales', order: 'asc', label: 'Sales (lowest first)' },
      { sort: 'branches', order: 'desc', label: 'Most branches' },
      { sort: 'branches', order: 'asc', label: 'Fewest branches' },
    ],
    filters: [{ kind: 'search', placeholder: 'Search retailers…' }],
    columns: [
      { key: 'name', label: 'Retailer', sort: 'name', cls: 'wrap' },
      { key: 'branch_count', label: 'Branches', sort: 'branches', align: 'right' },
      { key: 'total_sales', label: 'Total sales', sort: 'sales', align: 'right', render: (r) => money(r.total_sales, 0) },
    ],
    rowActions: (row, reload) => [el('button', { class: 'btn btn-sm', type: 'button', onclick: (e) => { e.stopPropagation(); openBranches(row, ctx, reload); } }, 'Branches')],
    fields: async () => [{ name: 'name', label: 'Retailer name', required: true, maxlength: 120 }],
    initialFromRow: (r) => ({ name: r.name }),
    label: (r) => r.name,
  });
}
