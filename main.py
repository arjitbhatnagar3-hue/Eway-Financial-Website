"""
EWAY Financial Consultancy Pvt. Ltd. — company website.

FastAPI backend that exposes the company data + user authentication
(signup / login / logout) as a JSON API and serves the static frontend.

Run locally:
    uvicorn main:app --host 0.0.0.0 --port 8000

Interactive API docs: http://localhost:8000/docs

NOTE: Users/sessions are stored in JSON files (users.json, sessions.json).
Perfect for learning. For production, swap them for a real database.
"""
import hashlib
import hmac
import json
import re
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from company_data import COMPANY, COMPLIANCE, DIRECTORS, FAQS, SERVICES, TESTIMONIALS

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
MESSAGES_FILE = BASE_DIR / "messages.json"
USERS_FILE = BASE_DIR / "users.json"
SESSIONS_FILE = BASE_DIR / "sessions.json"

COOKIE_NAME = "eway_session"
SESSION_TTL = timedelta(days=7)
PBKDF2_ITERATIONS = 300_000

app = FastAPI(
    title="EWAY Financial Consultancy API",
    description=(
        "Backend API for the EWAY Financial Consultancy Pvt. Ltd. website — "
        "company data, user authentication and contact-form enquiries."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


# --------------------------------------------------------------------------
# Small utilities
# --------------------------------------------------------------------------
def _years_since(iso_date: str) -> int:
    d = date.fromisoformat(iso_date)
    today = date.today()
    return max(0, today.year - d.year - ((today.month, today.day) < (d.month, d.day)))


def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return default


def _save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------
# Password hashing (PBKDF2-SHA256, stdlib only — no extra packages)
# --------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, digest = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(dk.hex(), digest)
    except (ValueError, AttributeError):
        return False


# --------------------------------------------------------------------------
# Request models
# --------------------------------------------------------------------------
class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120, description="Full name")
    email: str = Field(min_length=5, max_length=200, description="Email address")
    password: str = Field(min_length=8, max_length=128, description="Min 8 characters")

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Please provide a valid email address.")
        return v

    @field_validator("name")
    @classmethod
    def _valid_name(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=128)


class ContactMessage(BaseModel):
    name: str = Field(min_length=2, max_length=120, description="Your full name")
    email: str = Field(min_length=5, max_length=200, description="Your email address")
    phone: str | None = Field(default=None, max_length=20, description="Phone number (optional)")
    service: str | None = Field(default=None, max_length=120, description="Service you are interested in")
    message: str = Field(min_length=10, max_length=4000, description="Your message")

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        v = v.strip()
        if not EMAIL_RE.match(v):
            raise ValueError("Please provide a valid email address.")
        return v

    @field_validator("name", "message")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


# --------------------------------------------------------------------------
# Auth helpers (cookie sessions, stored in sessions.json)
# --------------------------------------------------------------------------
def _public_user(user: dict) -> dict:
    return {k: user[k] for k in ("id", "name", "email", "created_at")}


def _set_session_cookie(response: Response, user_id: str, request_scheme: str) -> None:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    sessions = _load_json(SESSIONS_FILE, {})
    # prune expired sessions while we're here
    sessions = {
        t: s for t, s in sessions.items()
        if datetime.fromisoformat(s["expires_at"]) > now
    }
    sessions[token] = {
        "user_id": user_id,
        "expires_at": (now + SESSION_TTL).isoformat(),
    }
    _save_json(SESSIONS_FILE, sessions)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,          # JavaScript cannot read the cookie
        samesite="lax",         # basic CSRF protection
        secure=request_scheme == "https",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def _current_user(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    sessions = _load_json(SESSIONS_FILE, {})
    session = sessions.get(token)
    if not session:
        return None
    if datetime.fromisoformat(session["expires_at"]) < datetime.now(timezone.utc):
        del sessions[token]
        _save_json(SESSIONS_FILE, sessions)
        return None
    users = _load_json(USERS_FILE, [])
    return next((u for u in users if u["id"] == session["user_id"]), None)


# --------------------------------------------------------------------------
# System
# --------------------------------------------------------------------------
@app.get("/api/health", tags=["System"])
def health() -> dict:
    return {"status": "ok", "service": "eway-financial-api"}


# --------------------------------------------------------------------------
# Company data
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
# Authentication
# --------------------------------------------------------------------------
@app.post("/api/auth/signup", status_code=201, tags=["Auth"])
def signup(payload: SignupRequest, request: Request, response: Response) -> dict:
    """Create an account and log the user in (sets a session cookie)."""
    users = _load_json(USERS_FILE, [])
    if any(u["email"] == payload.email for u in users):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    users.append(user)
    _save_json(USERS_FILE, users)
    _set_session_cookie(response, user["id"], request.url.scheme)
    return {"ok": True, "user": _public_user(user)}


@app.post("/api/auth/login", tags=["Auth"])
def login(payload: LoginRequest, request: Request, response: Response) -> dict:
    """Log in with email + password (sets a session cookie)."""
    users = _load_json(USERS_FILE, [])
    user = next(
        (u for u in users if u["email"] == payload.email.strip().lower()), None
    )
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    _set_session_cookie(response, user["id"], request.url.scheme)
    return {"ok": True, "user": _public_user(user)}


@app.post("/api/auth/logout", tags=["Auth"])
def logout(request: Request, response: Response) -> dict:
    """End the current session and clear the cookie."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        sessions = _load_json(SESSIONS_FILE, {})
        if token in sessions:
            del sessions[token]
            _save_json(SESSIONS_FILE, sessions)
    _clear_session_cookie(response)
    return {"ok": True}


@app.get("/api/auth/me", tags=["Auth"])
def me(request: Request) -> dict:
    """Return the logged-in user, or 401 if not authenticated."""
    user = _current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return {"user": _public_user(user)}


# --------------------------------------------------------------------------
# Contact form
# --------------------------------------------------------------------------
@app.post("/api/contact", status_code=201, tags=["Contact"])
def submit_contact(payload: ContactMessage) -> dict:
    """Save an enquiry from the website contact form."""
    entry = {
        "id": str(uuid.uuid4()),
        "received_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **payload.model_dump(),
    }
    messages = _load_json(MESSAGES_FILE, [])
    messages.append(entry)
    _save_json(MESSAGES_FILE, messages)
    return {
        "ok": True,
        "id": entry["id"],
        "message": (
            "Thank you! Your message has been received. "
            "Our team will get back to you within one business day."
        ),
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


@app.get("/{path:path}", include_in_schema=False)
def spa_fallback(path: str) -> FileResponse:
    """Serve the main page for any other non-API path."""
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(STATIC_DIR / "index.html")
