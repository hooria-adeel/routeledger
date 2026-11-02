from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings


def conninfo() -> str:
    """One place that decides how to reach PostgreSQL.

    A full DATABASE_URL (the usual form on managed hosts such as Neon,
    Supabase or Render) is used as-is. Otherwise the individual DB_* settings
    are combined, which is how local development and Docker work.
    """
    if settings.app_database_url:
        return settings.app_database_url
    if settings.database_url:
        return settings.database_url
    return make_conninfo(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


# Server-side prepared statements do not survive a transaction-pooling
# pgbouncer (Neon's -pooler endpoint, Supabase's pooler), so they can be
# switched off with DB_DISABLE_PREPARED=true.
_connect_kwargs = {"row_factory": dict_row}
if settings.db_disable_prepared:
    _connect_kwargs["prepare_threshold"] = None

# A small "pool" of ready connections, so every request does not have to
# log in to the database again.
pool = ConnectionPool(
    conninfo=conninfo(),
    min_size=settings.db_pool_min,
    max_size=settings.db_pool_max,
    kwargs=_connect_kwargs,
    # Recycle connections that the database or a pooler closed while idle.
    check=ConnectionPool.check_connection,
    open=False,                          # opened on startup or first request
)


def ensure_pool() -> None:
    """Opens the pool once. Safe to call from a lifespan event *and* at import
    time, which is what serverless platforms need on a cold start."""
    if pool.closed:
        pool.open()


def get_db():
    """Gives each request one connection. Saves (commits) if the request
    succeeds and undoes (rolls back) everything if it fails."""
    ensure_pool()
    with pool.connection() as conn:
        yield conn
