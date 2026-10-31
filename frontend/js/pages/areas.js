import { api } from '../api.js';
import { crudPage } from '../crud.js';
import { dataTable, el, errorBox, openModal, spinner } from '../ui.js';

async function openShops(area) {
  const modal = openModal(`Shops in ${area.name}`, spinner(), { wide: true });
  try {
    const data = await api.get(`/areas/${area.area_id}`);
    modal.setBody(dataTable({
      columns: [{ key: 'retailer', label: 'Retailer' }, { key: 'branch_name', label: 'Branch' }],
      rows: data.branches, emptyText: 'No shops in this area yet.' }));
  } catch (p) { modal.setBody(errorBox(p.message)); }
}

export function render(root, ctx) {
  return crudPage(root, ctx, {
    title: 'Areas', singular: 'area', endpoint: '/areas', idKey: 'area_id', paged: false,
    clientSearch: ['name', 'district'],
    filters: [{ kind: 'search', placeholder: 'Search areas…' }],
    columns: [
      { key: 'name', label: 'Area' },
      { key: 'district', label: 'District' },
      { key: 'branch_count', label: 'Shops', align: 'right' },
    ],
    rowActions: (row) => [el('button', { class: 'btn btn-sm', type: 'button', onclick: (e) => { e.stopPropagation(); openShops(row); } }, 'Shops')],
    fields: async () => [
      { name: 'name', label: 'Area name', required: true, maxlength: 80 },
      { name: 'district', label: 'District (optional)', maxlength: 80, clearable: true },
    ],
    initialFromRow: (r) => ({ name: r.name, district: r.district }),
    label: (r) => r.name,
  });
}
