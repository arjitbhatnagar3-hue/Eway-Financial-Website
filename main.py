"""
EWAY Financial Consultancy Pvt. Ltd. — company website + HR portal.

FastAPI backend that serves:
  • public company data (from company_data.py)
  • user accounts & sessions, contact enquiries          → database
  • the HR portal: employees, leave, attendance, payroll → database

Run locally:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Database: set DATABASE_URL (see .env.example). Without it a local SQLite
file `eway.db` is used, so the site works with zero setup.

Interactive API docs: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from company_data import COMPANY, COMPLIANCE, DIRECTORS, FAQS, SERVICES, TESTIMONIALS
from eway.bootstrap import startup
from eway.config import IS_SQLITE, STATIC_DIR
from eway.database import get_db
from eway.routers import auth, contact, hr


@asynccontextmanager
async def lifespan(_app: FastAPI):
    startup()  # create tables + first admin
    yield


app = FastAPI(
    title="EWAY Financial Consultancy API",
    description=(
        "Backend API for the EWAY Financial Consultancy Pvt. Ltd. website — company data, "
        "user authentication, contact enquiries and the HR portal (employees, leave, "
        "attendance, payroll, announcements)."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(contact.router)
app.include_router(hr.router)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


def _years_since(iso_date: str) -> int:
    d = date.fromisoformat(iso_date)
    today = date.today()
    return max(0, today.year - d.year - ((today.month, today.day) < (d.month, d.day)))


# --------------------------------------------------------------------------
# System
# --------------------------------------------------------------------------
@app.get("/api/health", tags=["System"])
def health(db: Session = Depends(get_db)) -> dict:
    """Service + database health check."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:  # pragma: no cover
        db_status = "unavailable"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "eway-financial-api",
        "database": {"status": db_status, "engine": "sqlite" if IS_SQLITE else "postgresql"},
    }


# --------------------------------------------------------------------------
# Company data (static content from company_data.py)
# --------------------------------------------------------------------------
@app.get("/api/company", tags=["Company"])
def get_company() -> dict:
    """Registered company details (MCA records)."""
    return COMPANY.model_dump()


@app.get("/api/services", tags=["Company"])
def get_services() -> list[dict]:
    """Advisory services offered by the firm."""
    return [s.model_dump() for s in SERVICES]


@app.get("/api/directors", tags=["Company"])
def get_directors() -> list[dict]:
    """Directors of the company (includes optional photo paths)."""
    return [d.model_dump() for d in DIRECTORS]


@app.get("/api/compliance", tags=["Company"])
def get_compliance() -> dict:
    """Annual compliance status as reported to MCA."""
    return COMPLIANCE.model_dump()


@app.get("/api/testimonials", tags=["Company"])
def get_testimonials() -> list[dict]:
    """Client testimonials shown on the homepage."""
    return [t.model_dump() for t in TESTIMONIALS]


@app.get("/api/faq", tags=["Company"])
def get_faq() -> list[dict]:
    """Frequently asked questions."""
    return [f.model_dump() for f in FAQS]


@app.get("/api/stats", tags=["Company"])
def get_stats() -> dict:
    """Key headline numbers for the website."""
    return {
        "years_in_business": _years_since(COMPANY.incorporated_on),
        "directors": len(DIRECTORS),
        "status": COMPANY.status,
        "authorized_capital": COMPANY.authorized_share_capital,
        "authorized_capital_formatted": COMPANY.authorized_capital_formatted,
        "authorized_capital_short": COMPANY.authorized_capital_short,
        "paid_up_capital": COMPANY.paid_up_share_capital,
        "paid_up_capital_formatted": COMPANY.paid_up_capital_formatted,
        "paid_up_capital_short": COMPANY.paid_up_capital_short,
    }


# --------------------------------------------------------------------------
# Static frontend (routes + mount, then SPA fallback last)
# --------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login", include_in_schema=False)
def login_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/signup", include_in_schema=False)
def signup_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "signup.html")


@app.get("/hr", include_in_schema=False)
@app.get("/hr/{path:path}", include_in_schema=False)
def hr_portal(path: str = "") -> FileResponse:
    """HR portal single-page app (auth is enforced by the API)."""
    return FileResponse(STATIC_DIR / "hr.html")


@app.get("/{path:path}", include_in_schema=False)
def spa_fallback(path: str) -> FileResponse:
    """Serve the main page for any other non-API path."""
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(STATIC_DIR / "index.html")
