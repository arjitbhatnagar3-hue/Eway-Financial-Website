"""
Database connection (SQLAlchemy 2.0).

Works with SQLite out of the box and PostgreSQL in production — only the
DATABASE_URL changes, the code stays the same.
"""
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DATABASE_URL, DB_ECHO, IS_SQLITE

engine = create_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    pool_pre_ping=True,  # transparently reconnect if the DB dropped an idle connection
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)

if IS_SQLITE:
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):  # pragma: no cover - trivial
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")   # enforce FK constraints
        cur.execute("PRAGMA journal_mode=WAL")  # better concurrent reads
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create any missing tables. Safe to call on every startup."""
    from . import models  # noqa: F401  (registers the models on Base.metadata)

    Base.metadata.create_all(bind=engine)
