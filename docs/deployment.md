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

## Option B — Render (managed, free tier)

1. Push the repository to GitHub.
2. In Render choose **New → Blueprint** and select the repository.
   Render reads [`render.yaml`](../render.yaml), creates a PostgreSQL instance
   and a Docker web service.
3. After the first deploy, open the service's **Environment** tab and reveal
   `ADMIN_PASSWORD`. Log in with `ADMIN_EMAIL` and that password.
4. Change the admin password from the Employees page.

The container runs `scripts/bootstrap_db` when `ADMIN_DATABASE_URL` is present,
then `scripts/bootstrap_admin`, then Uvicorn. Both are idempotent, so restarts
and redeploys are safe.

Free instances sleep after inactivity, so the first request may take ~30 s.
`RENDER_EXTERNAL_HOSTNAME` is picked up automatically for CORS and trusted
hosts.

## Option C — any Docker host or VPS

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
