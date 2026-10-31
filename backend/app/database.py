from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings

# A small "pool" of ready connections, so every request does not have to
# log in to the database again.
pool = ConnectionPool(
    conninfo=make_conninfo(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    ),
    min_size=1,
    max_size=5,
    kwargs={"row_factory": dict_row},   # rows come back as {"column": value}
    open=False,                          # opened when the app starts
)


def get_db():
    """Gives each request one connection. Saves (commits) if the request
    succeeds and undoes (rolls back) everything if it fails."""
    with pool.connection() as conn:
        yield conn