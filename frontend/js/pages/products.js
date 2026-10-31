import { api } from '../api.js';
import { crudPage } from '../crud.js';
import { money } from '../ui.js';

const categoryOptions = async () => (await api.get('/products/categories')).map((c) => ({ value: c.category_id, label: c.name }));

export function render(root, ctx) {
  return crudPage(root, ctx, {
    title: 'Products', singular: 'product', endpoint: '/products', idKey: 'product_id',
    defaultSort: { sort: 'name', order: 'asc' },
    sortOptions: [
      { sort: 'name', order: 'asc', label: 'Name (A → Z)' },
      { sort: 'name', order: 'desc', label: 'Name (Z → A)' },
      { sort: 'price', order: 'asc', label: 'Price (low → high)' },
      { sort: 'price', order: 'desc', label: 'Price (high → low)' },
      { sort: 'category', order: 'asc', label: 'Category (A → Z)' },
      { sort: 'pack_size', order: 'asc', label: 'Pack size (small → large)' },
      { sort: 'pack_size', order: 'desc', label: 'Pack size (large → small)' },
    ],
    filters: [
      { kind: 'search', placeholder: 'Search products…' },
      { kind: 'select', name: 'category_id', label: 'Category', all: 'All categories', options: categoryOptions },
    ],
    columns: [
      { key: 'name', label: 'Product', sort: 'name', cls: 'wrap' },
      { key: 'category', label: 'Category', sort: 'category' },
      { key: 'pack_size', label: 'Pack size', sort: 'pack_size', align: 'right' },
      { key: 'unit_price', label: 'Unit price', sort: 'price', align: 'right', render: (r) => money(r.unit_price) },
      { key: 'carton_price', label: 'Carton price', align: 'right', render: (r) => money(r.carton_price) },
    ],
    fields: async () => [
      { name: 'name', label: 'Product name', required: true, maxlength: 150 },
      { name: 'category_id', label: 'Category', type: 'select', coerce: 'int', required: true, options: await categoryOptions() },
      { name: 'pack_size', label: 'Pack size (units per carton)', type: 'number', min: 1, step: 1, required: true },
      { name: 'unit_price', label: 'Unit price (Rs)', type: 'number', min: 0, step: '0.01', required: true, help: 'Price of one unit. The carton price is worked out from it.' },
    ],
    initialFromRow: (r) => ({ name: r.name, category_id: r.category_id, pack_size: r.pack_size, unit_price: r.unit_price }),
    label: (r) => r.name,
  });
}
