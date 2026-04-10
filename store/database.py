"""
ATO Shield v2 - Database Connection & Session Management
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

load_dotenv()

# Use PostgreSQL if DATABASE_URL is set, otherwise SQLite for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ato_shield_dev.db")

# SQLite compatibility
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        pool_pre_ping=True
    )
    # Enable WAL mode for better concurrent access
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
