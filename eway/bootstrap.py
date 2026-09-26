"""Startup tasks: create tables and the first administrator."""
import logging
import os

from sqlalchemy import select

from .config import ADMIN_EMAIL, ADMIN_NAME, ADMIN_PASSWORD, IS_SQLITE
from .database import SessionLocal, init_db
from .models import Role, User
from .security import hash_password

log = logging.getLogger("eway")


def ensure_admin() -> None:
    """Create the admin from ADMIN_EMAIL / ADMIN_PASSWORD if that account doesn't exist yet."""
    if not (ADMIN_EMAIL and ADMIN_PASSWORD):
        return
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        if user:
            return
        db.add(User(name=ADMIN_NAME, email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD), role=Role.ADMIN))
        db.commit()
        log.warning("Created administrator account %s", ADMIN_EMAIL)


def startup() -> None:
    if IS_SQLITE and (os.getenv("RENDER") or os.getenv("DYNO") or os.getenv("RAILWAY_ENVIRONMENT")):
        log.error(
            "DATABASE_URL is not set — using SQLite on a temporary disk. "
            "All data will be LOST on the next deploy/restart. Set DATABASE_URL to a PostgreSQL database."
        )
    init_db()
    ensure_admin()
