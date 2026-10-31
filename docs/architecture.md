# Architecture

RouteLedger is a three-tier application with no frontend build step: the
FastAPI process serves both the JSON API and the static pages, so one container
is enough.

```
Browser (vanilla JS + CSS)
        │  fetch JSON, HttpOnly session cookie
        ▼
FastAPI application  ──  psycopg 3 connection pool
        │
        ▼
PostgreSQL 16+  (schema, constraints, triggers, views, roles)
```

## Request flow

1. The browser loads `/`, `app.js` and the page module.
2. Page modules call the API with `fetch(..., { credentials: "same-origin" })`.
3. `TrustedHostMiddleware` rejects unknown host names.
4. The origin check rejects cross-site writes.
5. The auth dependency validates the JWT cookie and reloads the employee and
   role from the database, so a deactivated user is rejected immediately.
6. `require("can_edit" | "can_delete" | "can_manage")` checks the permission and
   tells PostgreSQL who is acting via `set_config('app.current_employee_id', …)`.
7. The SQL query runs with bound parameters. Writes send the record's `version`;
   the database trigger raises `40001` if the record changed meanwhile, which the
   API turns into `409 Conflict`.
8. Audit and price-history triggers write their rows in the same transaction.
9. The API returns JSON with `Cache-Control: no-store` and security headers.

## Backend modules

| Path | Responsibility |
|---|---|
| `app/main.py` | app assembly, middleware, static frontend, `/health` |
| `app/config.py` | environment settings (pydantic-settings) |
| `app/database.py` | psycopg connection pool and per-request transaction |
| `app/dependencies.py` | current-user lookup and role checks |
| `app/middleware.py` | security headers, CSRF origin check, login rate limiter |
| `app/security.py` | Argon2 hashing, JWT creation/validation, password policy |
| `app/utils.py` | paging shape, friendly database errors, versioned updates |
| `app/schemas.py` | Pydantic request/response models |
| `app/routers/` | one module per resource: auth, products, retailers/branches, areas, orders, dashboard, employees, activity log |
| `scripts/` | admin creation, password reset, database and admin bootstrap |

## Frontend modules

| Path | Responsibility |
|---|---|
| `frontend/index.html` | single entry page |
| `js/app.js` | shell, navigation, session, theme and text-size controls |
| `js/api.js` | fetch wrapper, error handling, login redirect |
| `js/crud.js` | shared table, form and confirmation helpers |
| `js/ui.js` | DOM helpers, toasts, spinners, charts primitives |
| `js/pages/*.js` | one module per screen |

## Database

See [`database.md`](database.md) for the ER diagram, data dictionary,
normalisation and trigger catalogue.

## Repository layout

```
routeledger/
├─ backend/
│  ├─ app/                 FastAPI application
│  ├─ scripts/             admin + database bootstrap
│  ├─ tests/               pytest suite
│  ├─ requirements*.txt
│  └─ .env.example
├─ database/               schema, synthetic seed, role grants
├─ docs/                   architecture, database, security, deployment
├─ frontend/               static HTML/CSS/JS
├─ docker/                 container entrypoint
├─ Dockerfile
├─ docker-compose.yml
├─ render.yaml
└─ .github/workflows/ci.yml
```

## Design decisions

- **One process, no build step.** A static frontend served by FastAPI keeps the
  demo deployable on a single free container and easy to read.
- **The database is the last line of defence.** Constraints, triggers and roles
  enforce the rules even if a future endpoint forgets them.
- **Audit in the database, not in Python.** A forgotten `INSERT` into a log
  table cannot happen because the trigger always runs.
- **Optimistic locking over table locks.** Readers never block; conflicting
  writers get a clear `409`.
- **Soft delete.** Historical orders and reporting stay consistent; Managers
  can restore mistakes.
