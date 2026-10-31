#!/bin/sh
# Starts RouteLedger inside the container.
# 1. Build/update the database when admin credentials are present (first boot).
# 2. Create the first admin account if there are no employees yet.
# 3. Start the web server.
set -eu

if [ -n "${ADMIN_DATABASE_URL:-}" ] || [ -n "${ADMIN_DB_PASSWORD:-}" ]; then
    echo "==> Preparing the database"
    python -m scripts.bootstrap_db
else
    echo "==> No admin credentials supplied; assuming the database is already prepared"
fi

echo "==> Preparing the first admin account"
python -m scripts.bootstrap_admin

echo "==> Starting the web server on port ${PORT:-8000}"
exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --no-server-header \
    --proxy-headers \
    --forwarded-allow-ips="*"
