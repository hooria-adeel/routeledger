from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# the .env file sits in the "backend" folder, next to the "app" folder
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # Either one full URL (Neon, Supabase, Render, ...) or the separate parts.
    # DATABASE_URL wins when both are present.
    database_url: str = ""
    # Optional override used to connect with the least-privilege role when the
    # platform hands out an owner-level DATABASE_URL (Vercel + Neon do).
    app_database_url: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "routeledger"
    db_user: str = "postgres"
    db_password: str = ""
    secret_key: str
    token_minutes: int = 60
    cookie_secure: bool = False   # set to true when the site runs on https
    # websites allowed to talk to this backend (the frontend), separated by commas
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # names the browser may use to reach this server (blocks DNS-rebinding attacks)
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    # Public demo login shown on the sign-in page. Leave both empty in a real
    # installation; set them only for a synthetic demo with a read-only account.
    demo_email: str = ""
    demo_password: str = ""
    # Connection pool size. Serverless platforms should use DB_POOL_MIN=0 so an
    # idle function does not hold database connections open.
    db_pool_min: int = 1
    db_pool_max: int = 5
    # Managed poolers (Neon, pgbouncer) cannot use prepared statements.
    db_disable_prepared: bool = False

    model_config = SettingsConfigDict(env_file=ENV_FILE)

    @model_validator(mode="after")
    def require_a_database(self):
        if not self.database_url and not self.db_password:
            raise ValueError(
                "Set DATABASE_URL, or DB_PASSWORD together with DB_HOST/DB_NAME/DB_USER."
            )
        return self


settings = Settings()
