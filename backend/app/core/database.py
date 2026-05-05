from sqlalchemy import create_engine

from app.core.config import settings


settings.require_database_settings()
database_url = settings.DATABASE_URL

engine = create_engine(database_url, pool_pre_ping=True)
