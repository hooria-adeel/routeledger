# Deployment

RouteLedger ships as one Docker image: FastAPI serves the API and the static
frontend, and connects to any PostgreSQL 16+ database.

## Option A — Docker Compose (local, one command)

```bash
SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" \
APP_DB_PASSWORD="choose-a-strong-password" \
docker compose up --build
```

Open <http://localhost:8000>. The `app` container waits for PostgreSQL, loads
`schema.sql`, `seed.sql` and `seed_demo_orders.sql` on first boot, creates the
limited `routeledger_app` role, and creates the admin account from
`ADMIN_EMAIL` / `ADMIN_PASSWORD`.

Compose defaults are development-only. Override `SECRET_KEY`, `APP_DB_PASSWORD`,
`POSTGRES_PASSWORD`, `ADMIN_PASSWORD` and set `COOKIE_SECURE=true` when serving
over HTTPS.

## Option B — Vercel + Neon (serverless, free, no card)

This repository is deployed this way: **<https://routeledger-omega.vercel.app>**.

Vercel runs FastAPI as one serverless function (`index.py`) and Neon provides a
free PostgreSQL database through the Vercel Marketplace. Nothing here needs a
credit card.

### 1. Link the project and add the database

```bash
npm i -g vercel
vercel link --project routeledger
vercel integration accept-terms neon --yes      # accepts the marketplace terms
vercel integration add neon --name routeledger-db -e production
```

The Neon integration injects `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `PGHOST`,
`PGPASSWORD` and friends into the project. Pull them locally to load the schema:

```bash
vercel env pull .env.neon -e production
```

### 2. Create the schema and the limited role

```bash
cd backend
export ADMIN_DATABASE_URL="<DATABASE_URL_UNPOOLED from .env.neon>"
export DB_USER=routeledger_app DB_PASSWORD="<a strong password>"
python -m scripts.bootstrap_db

export DATABASE_URL="$ADMIN_DATABASE_URL"
export ADMIN_EMAIL=admin@routeledger.example
export ADMIN_PASSWORD="<a strong password>"
python -m scripts.bootstrap_admin
```

`bootstrap_db` loads `schema.sql`, the synthetic seed and the 400 demo orders,
then grants the application role only `SELECT`, `INSERT`, `UPDATE` and the
delete rights it needs. It never gets `CREATE`, `DROP` or access to rewrite the
audit log — verified against Neon:

```
create table: blocked (InsufficientPrivilege)
drop table:   blocked (InsufficientPrivilege)
edit audit log: blocked (InsufficientPrivilege)
```

### 3. Environment variables

Set these in **Project → Settings → Environment Variables** (production):

| Variable | Value | Why |
|---|---|---|
| `APP_DATABASE_URL` | pooled URL for `routeledger_app` | connect as the limited role instead of Neon's owner |
| `SECRET_KEY` | 48+ random characters | JWT signing |
| `COOKIE_SECURE` | `true` | `Secure` cookie + HSTS |
| `DB_DISABLE_PREPARED` | `true` | Neon's pooler cannot keep prepared statements |
| `DB_POOL_MIN` / `DB_POOL_MAX` | `0` / `2` | serverless instances must not hold idle connections |
| `ALLOWED_HOSTS` | `*.vercel.app` | `TrustedHostMiddleware`; the deployed URL is added automatically |
| `CORS_ORIGINS` | `https://<project>.vercel.app` | same-origin API calls |

`APP_DATABASE_URL` exists because the integration owns `DATABASE_URL` (the
owner role). The app prefers `APP_DATABASE_URL` when both are present.

### 4. Deploy

```bash
vercel --prod
```

`index.py` re-exports the FastAPI app from `backend/` because Vercel looks for a
`FastAPI` instance named `app` at the project root. `vercel.json` keeps the
bundle small, and `.vercelignore` keeps `.env` files and tests out of the upload.

### Serverless notes

- Function instances are recycled; `min_size=0` and a connection check avoid
  leaking connections into Neon's limit.
- Use the **pooled** host for the app (`...-pooler...`) and the **unpooled** one
  for migrations and `bootstrap_db`.
- Cold starts add roughly 1–2 seconds to the first request.
- Deployment Protection must be off for a public demo; otherwise every visitor
  needs a Vercel account.

## Option C — Render (managed, free tier)

### 1. Push the repository to GitHub

Create an **empty public repository** (no README, no `.gitignore`) at
<https://github.com/new>, then from this folder:

```bash
git remote add origin https://github.com/<your-username>/routeledger.git
git push -u origin main
```

### 2. Create the Render Blueprint

Open **[Deploy to Render](https://render.com/deploy?repo=https://github.com/hooria-adeel/routeledger)**
or, from the dashboard, choose **New → Blueprint**, select the `routeledger`
repository, and apply. Render reads [`render.yaml`](../render.yaml), creates a
PostgreSQL instance and a Docker web service, and builds the image. Wait for
the first deploy to become **Live**.

### 3. Get the login

1. Open the `routeledger` service → **Environment**.
2. Reveal `ADMIN_PASSWORD` (and note `ADMIN_EMAIL`).
3. Open the service URL and log in.
4. Change the admin password from the **Employees** page immediately.

The container runs `scripts/bootstrap_db` when `ADMIN_DATABASE_URL` is present,
then `scripts/bootstrap_admin`, then Uvicorn. Both are idempotent, so restarts
and redeploys are safe.

Free instances sleep after inactivity, so the first request may take ~30 s.
`RENDER_EXTERNAL_HOSTNAME` is picked up automatically for CORS and trusted
hosts.

### 4. Verify the deployment

```bash
curl https://<your-service>.onrender.com/health
# {"status":"ok","products_in_database":93}
```

Also confirm: login works, the dashboard shows 460 orders, and
`curl -I https://<your-service>.onrender.com/` returns
`strict-transport-security` and `content-security-policy`.

## Option D — any Docker host or VPS

```bash
docker build -t routeledger .
docker run -d --name routeledger -p 8000:8000 \
  -e DB_HOST=... -e DB_PORT=5432 -e DB_NAME=routeledger \
  -e DB_USER=routeledger_app -e DB_PASSWORD=... \
  -e ADMIN_DATABASE_URL='postgresql://postgres:...@host/routeledger' \
  -e SECRET_KEY=... -e ADMIN_EMAIL=... -e ADMIN_PASSWORD=... \
  -e COOKIE_SECURE=true -e ALLOWED_HOSTS=ledger.example.com \
  -e CORS_ORIGINS=https://ledger.example.com \
  routeledger
```

Put a TLS-terminating reverse proxy (Caddy, nginx, the platform's load balancer)
in front. Uvicorn trusts `X-Forwarded-*` from the proxy in the image.

## Environment variables

| Variable | Required | Meaning |
|---|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME` | yes | PostgreSQL address |
| `DB_USER`, `DB_PASSWORD` | yes | limited application role |
| `SECRET_KEY` | yes | JWT signing key, 48+ random characters |
| `TOKEN_MINUTES` | no (60) | session lifetime |
| `CORS_ORIGINS` | no | comma-separated public origins; platform URL is added automatically |
| `ALLOWED_HOSTS` | no | comma-separated host names for `TrustedHostMiddleware` |
| `COOKIE_SECURE` | no (false) | set `true` behind HTTPS |
| `ADMIN_DATABASE_URL` or `ADMIN_DB_PASSWORD` | first boot | lets `bootstrap_db` create the schema and role |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME` | first boot | first Administrator account |
| `LOAD_DEMO_DATA` | no (true) | load the 400 extra demo orders; set `false` for a real installation |
| `PORT` | no (8000) | port Uvicorn listens on |

## Manual installation without Docker

```bash
createdb routeledger && createdb routeledger_test
psql -d routeledger -f database/schema.sql -f database/seed.sql -f database/seed_demo_orders.sql
psql -d routeledger_test -f database/schema.sql -f database/seed.sql
# create the app role with a strong password (edit the file first)
psql -d routeledger -f database/create_app_user.sql
psql -d routeledger_test -f database/create_app_user.sql

cd backend
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                              # set DB_PASSWORD and SECRET_KEY
python -m scripts.create_admin
uvicorn app.main:app --reload
pytest
```

## Backups and restore

```bash
# backup
pg_dump --format=custom --file=routeledger-$(date +%F).dump "$DATABASE_URL"
# restore into an empty database
pg_restore --clean --if-exists --dbname="$DATABASE_URL" routeledger-2026-10-31.dump
```

Run a restore drill before trusting a backup. The audit log is append-only in
the application, so a restore is the only sanctioned way to rewrite history.

## Production checklist

- [ ] `COOKIE_SECURE=true`, HTTPS, HSTS enabled
- [ ] random `SECRET_KEY` and database passwords stored in the platform's secret store
- [ ] `ALLOWED_HOSTS` and `CORS_ORIGINS` limited to the real domain
- [ ] admin password changed after first login
- [ ] scheduled backups with a tested restore
- [ ] dependency updates (Dependabot) reviewed
- [ ] database not publicly reachable; only the app can connect
- [ ] monitoring on `/health` and the platform logs
