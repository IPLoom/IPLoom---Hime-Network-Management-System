from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "LAN Scanner"
    app_env: str = "development"
    app_debug: bool = False

    db_path: str = "../data/final_scanner.duckdb"
    db_schema_path: str = "app/schema.sql"
    db_init_mode: str = "create"  # create | recreate

    max_concurrent_scans: int = 4
    default_subnet: str = "192.168.1.0/24"

    # Auth settings
    secret_key: str = "supersecretkey" # Should be changed in production
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7 # 7 days

    # Assets settings
    assets_dir: str = "../data/assets"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
