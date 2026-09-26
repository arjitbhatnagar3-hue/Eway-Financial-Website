"""
Application settings, read from environment variables (or a local `.env` file).

The only setting you *must* think about is DATABASE_URL:

    # local development (default — nothing to install, creates ./eway.db)
    DATABASE_URL=sqlite:///./eway.db

    # production (PostgreSQL — Render, Neon, Supabase, AWS RDS, …)
    DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME

See `.env.example` for every option.
"""
import os
from datetime import timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

try:  # python-dotenv is optional: load .env if the package is installed
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:  # pragma: no cover
    pass


def _normalize_db_url(url: str) -> str:
    """Hosts hand out `postgres://…` URLs; SQLAlchemy + psycopg3 wants `postgresql+psycopg://…`."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


DATABASE_URL: str = _normalize_db_url(
    os.getenv("DATABASE_URL", "").strip() or f"sqlite:///{BASE_DIR / 'eway.db'}"
)
IS_SQLITE = DATABASE_URL.startswith("sqlite")
DB_ECHO = _bool("DB_ECHO")  # log every SQL statement (debugging only)

# First administrator — created automatically on startup if it doesn't exist yet.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrator").strip()

# Sessions / cookies
COOKIE_NAME = "eway_session"
SESSION_TTL = timedelta(days=int(os.getenv("SESSION_TTL_DAYS", "7")))
# "auto" = secure cookie when the request arrived over HTTPS; "true"/"false" to force.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "auto").strip().lower()
PBKDF2_ITERATIONS = 300_000

# India Standard Time (no DST) — used for "today", attendance and payroll periods.
IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# HR policy (edit to match the company's actual policy)
# ---------------------------------------------------------------------------
# Annual leave quotas per calendar year. "unpaid" has no quota (loss of pay).
LEAVE_QUOTAS: dict[str, int] = {"casual": 12, "sick": 12, "earned": 15}
LEAVE_TYPES = [*LEAVE_QUOTAS.keys(), "unpaid"]
# Weekly off-days (Python weekday numbers: Monday=0 … Sunday=6). Office is Mon–Sat.
WEEKLY_OFF_DAYS = {6}

# Salary structure used by the payroll run (percent of monthly gross).
BASIC_PCT = 0.50
HRA_PCT = 0.20
PF_RATE = 0.12          # employee PF contribution, % of earned basic
PF_WAGE_CEILING = 15_000  # statutory PF wage ceiling → max ₹1,800 / month