import { api } from '../api.js';
import { badge, clear, confirmBox, dataTable, debounce, el, errorBox, fdate, formModal, money, num, openModal, pager, spinner, toast } from '../ui.js';

let productCache = null;
async function products() {
  if (!productCache) {
    const first = await api.get('/products', { page_size: 100, sort: 'name' });
    let rows = first.items;
    for (let p = 2; p <= Math.ceil(first.total / 100); p += 1) rows = rows.concat((await api.get('/products', { page_size: 100, sort: 'name', page: p })).items);
    productCache = rows.map((r) => ({ value: r.product_id, label: r.name, price: r.carton_price }));
  }
  return productCache;
}

export async function render(root, ctx) {
  const canEdit = ctx.can('can_edit');
  const state = { page: 1, pageSize: 25, sort: 'date', order: 'desc', retailer_id: '', area_id: '', date_from: '', date_to: '' };
  const tableBox = el('div', {});
  const pagerBox = el('div', {});

  let retailers = [], areas = [];
  try {
    [retailers, areas] = await Promise.all([api.get('/retailers', { page_size: 100 }).then((d) => d.items), api.get('/areas')]);
  } catch (p) { root.replaceChildren(errorBox(p.message, () => render(root, ctx))); return; }

  const select = (name, all, options) => {
    const s = el('select', { 'aria-label': all, onchange: () => { state[name] = s.value; state.page = 1; load(); } },
      el('option', { value: '' }, all), options.map((o) => el('option', { value: o.value }, o.label)));
    return s;
  };
  const dateInput = (name, label) => {
    const i = el('input', { type: 'date', 'aria-label': label, onchange: () => { state[name] = i.value; state.page = 1; load(); } });
    return el('div', { class: 'field' }, el('label', {}, label), i);
  };

  const SORTS = [
    ['date:desc', 'Newest first'], ['date:asc', 'Oldest first'], ['total:desc', 'Biggest order first'],
    ['total:asc', 'Smallest order first'], ['cartons:desc', 'Most cartons'], ['retailer:asc', 'Retailer (A → Z)'],
  ];
  const sortSelect = el('select', { 'aria-label': 'Sort by', onchange: () => {
    if (!sortSelect.value) return;
    [state.sort, state.order] = sortSelect.value.split(':'); state.page = 1; load();
  } }, el('option', { value: '' }, 'Sorted by column'), SORTS.map(([v, label]) => el('option', { value: v }, label)));
  const syncSort = () => { const now = `${state.sort}:${state.order}`; sortSelect.value = SORTS.some(([v]) => v === now) ? now : ''; };

  root.replaceChildren(
    el('div', { class: 'page-head' }, el('h2', {}, 'Orders'),
      canEdit ? el('button', { class: 'btn btn-primary', type: 'button', onclick: () => newOrder(ctx, load) }, '+ New order') : null),
    el('div', { class: 'toolbar' },
      el('div', { class: 'field' }, el('label', {}, 'Retailer'), select('retailer_id', 'All retailers', retailers.map((r) => ({ value: r.retailer_id, label: r.name })))),
      el('div', { class: 'field' }, el('label', {}, 'Area'), select('area_id', 'All areas', areas.map((a) => ({ value: a.area_id, label: a.name })))),
      dateInput('date_from', 'From'), dateInput('date_to', 'To'),
      el('div', { class: 'field' }, el('label', {}, 'Sort by'), sortSelect)),
    tableBox, pagerBox);

  async function load() {
    tableBox.replaceChildren(spinner()); pagerBox.replaceChildren();
    try {
      const data = await api.get('/orders', { retailer_id: state.retailer_id, area_id: state.area_id, date_from: state.date_from, date_to: state.date_to, sort: state.sort, order: state.order, page: state.page, page_size: state.pageSize });
      syncSort();
      tableBox.replaceChildren(dataTable({
        rows: data.items, sort: state.sort, order: state.order, emptyText: 'No orders match these filters.',
        onRowClick: (row) => openOrder(row.order_id, ctx, load),
        onSort: (key) => { state.order = state.sort === key && state.order === 'asc' ? 'desc' : 'asc'; state.sort = key; state.page = 1; load(); },
        columns: [
          { key: 'order_id', label: 'Order', render: (r) => `#${r.order_id}` },
          { key: 'order_date', label: 'Date', sort: 'date', render: (r) => fdate(r.order_date) },
          { key: 'retailer', label: 'Retailer', sort: 'retailer', cls: 'wrap' },
          { key: 'area', label: 'Area' },
          { key: 'item_count', label: 'Products', align: 'right' },
          { key: 'cartons', label: 'Cartons', sort: 'cartons', align: 'right', render: (r) => num(r.cartons) },
          { key: 'total_value', label: 'Total', sort: 'total', align: 'right', render: (r) => money(r.total_value, 0) },
        ] }));
      pagerBox.replaceChildren(pager({ page: state.page, pageSize: state.pageSize, total: data.total, onPage: (p) => { state.page = p; load(); } }));
    } catch (p) { tableBox.replaceChildren(errorBox(p.message, load)); }
  }
  load();
}

// ---------------------------------------------------------------- one order
function openOrder(orderId, ctx, reloadList) {
  const modal = openModal(`Order #${orderId}`, spinner(), { wide: true });
  const canEdit = ctx.can('can_edit'), canDelete = ctx.can('can_delete');

  async function show() {
    let o;
    try { o = await api.get(`/orders/${orderId}`); } catch (p) { modal.setBody(errorBox(p.message, show)); return; }

    const stale = (p) => { if (p.status === 409) { toast(p.message, 'error'); show(); return true; } return false; };

    const editItem = (item) => {
      const initial = { cartons: item.cartons, carton_price: item.carton_price };
      formModal({ title: `Edit ${item.product}`, initial, fields: [
        { name: 'cartons', label: 'Cartons', type: 'number', min: 1, step: 1, required: true },
        { name: 'carton_price', label: 'Price per carton (Rs)', type: 'number', min: 0, step: '0.01', required: true },
      ], onSubmit: async (v, m) => {
        const changes = {};
        for (const k of Object.keys(v)) if (Number(v[k]) !== Number(initial[k])) changes[k] = v[k];
        if (Object.keys(changes).length) {
          try { await api.patch(`/orders/${orderId}/items/${item.item_id}`, { ...changes, version: item.version }); } catch (p) { if (stale(p)) { m.close(); return; } throw p; }
        }
        m.close(); toast('Item saved.'); show(); reloadList();
      } });
    };
    const removeItem = async (item) => {
      if (!(await confirmBox(`Remove “${item.product}” from this order?`))) return;
      try { await api.del(`/orders/${orderId}/items/${item.item_id}`); toast('Item removed.'); show(); reloadList(); } catch (p) { toast(p.message, 'error'); }
    };
    const addItem = async () => {
      const opts = await products();
      formModal({ title: 'Add product to order', fields: [
        { name: 'product_id', label: 'Product (type to search)', type: 'combo', required: true, options: opts },
        { name: 'cartons', label: 'Cartons', type: 'number', min: 1, step: 1, required: true },
        { name: 'carton_price', label: 'Price per carton (optional)', type: 'number', min: 0, step: '0.01', help: 'Leave empty to use the normal carton price.' },
      ], submitLabel: 'Add', onSubmit: async (v, m) => {
        if (v.product_id === null) throw new Error('Please choose a product.');
        const body = { product_id: v.product_id, cartons: v.cartons };
        if (v.carton_price !== null) body.carton_price = v.carton_price;
        await api.post(`/orders/${orderId}/items`, body);
        m.close(); toast('Product added.'); show(); reloadList();
      } });
    };
    const editHeader = async () => {
      const retailers = (await api.get('/retailers', { page_size: 100 })).items;
      const initial = { order_date: o.order_date, retailer_id: o.retailer_id };
      formModal({ title: 'Edit order', initial, fields: [
        { name: 'retailer_id', label: 'Retailer', type: 'select', coerce: 'int', required: true, options: retailers.map((r) => ({ value: r.retailer_id, label: r.name })) },
        { name: 'order_date', label: 'Order date', type: 'date', required: true, max: new Date().toISOString().slice(0, 10) },
      ], onSubmit: async (v, m) => {
        const changes = {};
        for (const k of Object.keys(v)) if (String(v[k]) !== String(initial[k])) changes[k] = v[k];
        if (Object.keys(changes).length) {
          try { await api.patch(`/orders/${orderId}`, { ...changes, version: o.version }); } catch (p) { if (stale(p)) { m.close(); return; } throw p; }
        }
        m.close(); toast('Order saved.'); show(); reloadList();
      } });
    };
    const removeOrder = async () => {
      if (!(await confirmBox(`Delete order #${orderId}? It is hidden, not destroyed, and a manager can restore it.`))) return;
      try { await api.del(`/orders/${orderId}`); modal.close(); toast('Order deleted.'); reloadList(); } catch (p) { toast(p.message, 'error'); }
    };

    const columns = [
      { key: 'product', label: 'Product', cls: 'wrap' },
      { key: 'cartons', label: 'Cartons', align: 'right', render: (i) => num(i.cartons) },
      { key: 'carton_price', label: 'Carton price', align: 'right', render: (i) => money(i.carton_price) },
      { key: 'line_value', label: 'Value', align: 'right', render: (i) => money(i.line_value) },
      { key: '_a', label: '', cls: 'actions', render: (i) => [
        canEdit ? el('button', { class: 'btn btn-sm', type: 'button', onclick: () => editItem(i) }, 'Edit') : null,
        canDelete ? el('button', { class: 'btn btn-sm btn-danger', type: 'button', onclick: () => removeItem(i) }, 'Remove') : null] },
    ];
    modal.setBody(el('div', {},
      el('div', { class: 'kv' },
        el('div', {}, el('span', {}, 'Retailer'), el('b', {}, o.retailer)),
        el('div', {}, el('span', {}, 'Date'), el('b', {}, fdate(o.order_date))),
        el('div', {}, el('span', {}, 'Branch / area'), el('b', {}, o.branch_name ? `${o.branch_name} · ${o.area}` : 'Not recorded'))),
      el('div', { class: 'form-actions' },
        canEdit ? el('button', { class: 'btn', type: 'button', onclick: editHeader }, 'Edit order') : null,
        canEdit ? el('button', { class: 'btn btn-primary', type: 'button', onclick: addItem }, '+ Add product') : null,
        canDelete ? el('button', { class: 'btn btn-danger', type: 'button', onclick: removeOrder }, 'Delete order') : null),
      el('div', { class: 'sep' }),
      dataTable({ columns, rows: o.items }),
      el('div', { class: 'total-line' }, `Total: ${money(o.total_value)}`)));
  }
  show();
}

// ---------------------------------------------------------------- new order
async function newOrder(ctx, reloadList) {
  const [retailers, productOptions] = await Promise.all([api.get('/retailers', { page_size: 100 }).then((d) => d.items), products()]);
  const today = new Date().toISOString().slice(0, 10);
  const errorLine = el('div', { class: 'form-error', role: 'alert', hidden: true });

  const retailer = el('select', { id: 'no-retailer', required: true, onchange: loadBranches }, el('option', { value: '' }, 'Choose a retailer…'),
    retailers.map((r) => el('option', { value: r.retailer_id }, r.name)));
  const branch = el('select', { id: 'no-branch' }, el('option', { value: '' }, 'Not specified'));
  const date = el('input', { id: 'no-date', type: 'date', required: true, max: today, value: today });
  const listId = 'no-products';
  const datalist = el('datalist', { id: listId }, productOptions.map((p) => el('option', { value: p.label })));
  const rowsBox = el('div', {});
  const rows = [];

  async function loadBranches() {
    branch.replaceChildren(el('option', { value: '' }, 'Not specified'));
    if (!retailer.value) return;
    try {
      const data = await api.get('/branches', { retailer_id: retailer.value, page_size: 100 });
      data.items.forEach((b) => branch.append(el('option', { value: b.branch_id }, `${b.branch_name} (${b.area})`)));
    } catch (p) { /* the list stays on "Not specified" */ }
  }

  function addRow() {
    const product = el('input', { type: 'text', list: listId, placeholder: 'Type a product name…', 'aria-label': 'Product', autocomplete: 'off' });
    const cartons = el('input', { type: 'number', min: 1, step: 1, value: 1, 'aria-label': 'Cartons' });
    const price = el('input', { type: 'number', min: 0, step: '0.01', placeholder: 'Normal', 'aria-label': 'Price per carton' });
    const rowEl = el('div', { class: 'items-grid' }, product, cartons, price,
      el('button', { class: 'btn btn-sm btn-danger', type: 'button', 'aria-label': 'Remove this line', onclick: () => {
        if (rows.length > 1) { rows.splice(rows.indexOf(entry), 1); rowEl.remove(); } } }, '×'));
    const entry = { product, cartons, price };
    rows.push(entry); rowsBox.append(rowEl);
  }

  const submit = el('button', { class: 'btn btn-primary', type: 'submit' }, 'Save order');
  const form = el('form', { class: 'form', onsubmit: async (event) => {
    event.preventDefault(); errorLine.hidden = true; submit.disabled = true;
    try {
      const items = rows.map((r, n) => {
        const match = productOptions.find((p) => p.label.toLowerCase() === r.product.value.trim().toLowerCase());
        if (!match) throw new Error(`Line ${n + 1}: please choose a product from the list.`);
        const item = { product_id: match.value, cartons: Number(r.cartons.value) };
        if (r.price.value !== '') item.carton_price = Number(r.price.value);
        return item;
      });
      const body = { retailer_id: Number(retailer.value), order_date: date.value, items };
      if (branch.value) body.branch_id = Number(branch.value);
      await api.post('/orders', body);
      modal.close(); toast('Order saved.'); reloadList();
    } catch (p) { errorLine.textContent = p.message; errorLine.hidden = false; } finally { submit.disabled = false; }
  } },
    el('div', { class: 'field' }, el('label', { for: 'no-retailer' }, 'Retailer *'), retailer),
    el('div', { class: 'field' }, el('label', { for: 'no-branch' }, 'Branch'), branch),
    el('div', { class: 'field' }, el('label', { for: 'no-date' }, 'Order date *'), date),
    el('div', {}, el('div', { class: 'items-grid head' }, el('span', {}, 'Product'), el('span', {}, 'Cartons'), el('span', {}, 'Price / carton'), el('span', {})),
      rowsBox, datalist,
      el('button', { class: 'btn btn-sm', type: 'button', onclick: addRow }, '+ Add another product'),
      el('div', { class: 'help muted' }, 'Leave the price empty to use the normal carton price.')),
    errorLine,
    el('div', { class: 'form-actions' }, el('button', { class: 'btn', type: 'button', onclick: () => modal.close() }, 'Cancel'), submit));
  addRow();
  const modal = openModal('New order', form, { wide: true });
}
