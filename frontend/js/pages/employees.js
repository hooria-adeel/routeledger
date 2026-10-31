import { api } from '../api.js';
import { crudPage } from '../crud.js';
import { badge, fdatetime } from '../ui.js';

export function render(root, ctx) {
  return crudPage(root, ctx, {
    title: 'Employees', singular: 'employee', endpoint: '/employees', idKey: 'employee_id', paged: false, noVersion: true,
    allowDelete: false, clientSearch: ['full_name', 'email', 'role'],
    addDefaults: { role: 'Viewer' },
    filters: [{ kind: 'search', placeholder: 'Search employees…' }],
    columns: [
      { key: 'full_name', label: 'Name' },
      { key: 'email', label: 'Email' },
      { key: 'role', label: 'Role', render: (r) => badge(r.role, 'role') },
      { key: 'is_active', label: 'Status', render: (r) => (!r.is_active ? badge('Inactive', 'bad') : r.is_locked ? badge('Locked', 'warn') : badge('Active', 'good')) },
      { key: 'last_login_at', label: 'Last login', render: (r) => (r.last_login_at ? fdatetime(r.last_login_at) : 'Never') },
    ],
    fields: async () => {
      const roles = (await api.get('/employees/roles')).map((r) => ({ value: r.name, label: `${r.name} — ${r.description}` }));
      return [
        { name: 'full_name', label: 'Full name', required: true, maxlength: 100, addOnly: true },
        { name: 'email', label: 'Email', type: 'email', required: true, maxlength: 150, addOnly: true, autocomplete: 'off' },
        { name: 'password', label: 'Password', type: 'password', required: true, addOnly: true, autocomplete: 'new-password',
          help: 'At least 10 characters, with a capital letter, a small letter and a number.' },
        { name: 'role', label: 'Role', type: 'select', required: true, options: roles },
        { name: 'is_active', label: 'Status', type: 'select', coerce: 'bool', editOnly: true,
          options: [{ value: 'true', label: 'Active' }, { value: 'false', label: 'Inactive (cannot log in)' }] },
        { name: 'new_password', label: 'New password (leave empty to keep the old one)', type: 'password', editOnly: true, autocomplete: 'new-password' },
      ];
    },
    initialFromRow: (r) => ({ role: r.role, is_active: r.is_active, new_password: '' }),
    label: (r) => r.full_name,
  });
}
