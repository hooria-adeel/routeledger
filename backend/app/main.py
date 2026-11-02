import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import ensure_pool, get_db, pool
from app.middleware import (
    add_security_headers,
    allowed_hosts,
    check_request_origin,
    cors_origins,
)
from app.routers import (
    activity_log,
    areas,
    auth,
    dashboard,
    employees,
    orders,
    products,
    retailers,
)

# Some Windows computers describe these files wrongly, and then the browser
# refuses to run them. We say it clearly ourselves.
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_pool()    # app starts: open the database connections (once)
    yield
    pool.close()     # app stops: close them


app = FastAPI(title="RouteLedger Distribution System", lifespan=lifespan)

# Extra safety headers on every answer
app.middleware("http")(add_security_headers)

# A state-changing request from another website is refused (CSRF defence).
app.middleware("http")(check_request_origin)

# Only names that really belong to this server are accepted.
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts())

# Only our own frontend website may call this backend from a browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,                      # needed for the login cookie
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

for router in (
    auth, products, retailers, areas, orders, dashboard, employees, activity_log
):
    app.include_router(router.router)


@app.get("/health")
def health(db=Depends(get_db)):
    """Quick check that Python can really talk to the database."""
    row = db.execute("SELECT count(*) AS products FROM products").fetchone()
    return {"status": "ok", "products_in_database": row["products"]}


# The web pages (the "frontend" folder next to "backend"). This must stay LAST,
# so that the data routes above are found first.
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
