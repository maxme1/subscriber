from pathlib import Path

from pydantic_settings import BaseSettings


ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings, extra='ignore'):
    telegram_token: str
    storage_path: Path
    logs_path: Path | None = None
    db_path: Path = ROOT / 'db.sqlite3'


config = Settings(_env_file=ROOT / '.env')
