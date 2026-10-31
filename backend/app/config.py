from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# the .env file sits in the "backend" folder, next to the "app" folder
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "routeledger"
    db_user: str = "postgres"
    db_password: str
    secret_key: str
    token_minutes: int = 60
    cookie_secure: bool = False   # set to true when the site runs on https
    # websites allowed to talk to this backend (the frontend), separated by commas
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # names the browser may use to reach this server (blocks DNS-rebinding attacks)
    allowed_hosts: str = "localhost,127.0.0.1,testserver"

    model_config = SettingsConfigDict(env_file=ENV_FILE)


settings = Settings()