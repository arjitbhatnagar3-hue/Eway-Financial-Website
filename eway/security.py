"""
Authentication & authorization helpers.

- Passwords: PBKDF2-SHA256 (300k iterations, per-user salt) — stdlib only.
- Sessions: random 256-bit token in an HttpOnly cookie; only its SHA-256 hash
  is stored in the `sessions` table, so a leaked DB can't be used to log in.
- Roles: FastAPI dependencies `require_user`, `require_roles(...)`,
  `require_employee` protect every private endpoint.
"""
import hashlib
import hmac
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import COOKIE_NAME, COOKIE_SECURE, PBKDF2_ITERATIONS, SESSION_TTL
from .database import get_db
from .models import Employee, Role, User, UserSession


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, digest = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(dk.hex(), digest)
    except (ValueError, AttributeError):
        return False


def generate_temp_password() -> str:
    """Readable one-time password handed to new employees by HR."""
    return "Ew-" + secrets.token_urlsafe(9)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _cookie_secure(request: Request) -> bool:
    if COOKIE_SECURE in {"true", "1", "yes"}:
        return True
    if COOKIE_SECURE in {"false", "0", "no"}:
        return False
    return request.url.scheme == "https"


def start_session(db: Session, user: User, request: Request, response: Response) -> None:
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    # housekeeping: drop expired sessions
    db.execute(delete(UserSession).where(UserSession.expires_at < now))
    db.add(
        UserSession(
            token_hash=_token_hash(token),
            user_id=user.id,
            expires_at=now + SESSION_TTL,
            user_agent=(request.headers.get("user-agent") or "")[:255],
            ip_address=request.client.host if request.client else None,
        )
    )
    user.last_login_at = now
    db.commit()
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(SESSION_TTL.total_seconds()),
        httponly=True,       # JavaScript cannot read the cookie
        samesite="lax",      # not sent on cross-site POSTs → CSRF protection
        secure=_cookie_secure(request),
        path="/",
    )


def end_session(db: Session, request: Request, response: Response) -> None:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.execute(delete(UserSession).where(UserSession.token_hash == _token_hash(token)))
        db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")


def end_all_sessions(db: Session, user: User, keep_request: Request | None = None) -> None:
    """Log a user out everywhere (e.g. after a password change or deactivation)."""
    stmt = delete(UserSession).where(UserSession.user_id == user.id)
    if keep_request is not None and (token := keep_request.cookies.get(COOKIE_NAME)):
        stmt = stmt.where(UserSession.token_hash != _token_hash(token))
    db.execute(stmt)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    session = db.get(UserSession, _token_hash(token))
    if not session:
        return None
    if session.expires_at < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        return None
    user = session.user
    return user if user and user.is_active else None


# ---------------------------------------------------------------------------
# Authorization dependencies
# ---------------------------------------------------------------------------
def require_user(user: User | None = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    return user


def require_roles(*roles: str):
    """Dependency factory: `Depends(require_roles(Role.ADMIN, Role.HR))`."""

    def checker(user: User = Depends(require_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You don't have permission to do that.")
        return user

    return checker


require_staff = require_roles(*Role.STAFF)
require_manager = require_roles(*Role.MANAGERS)
require_admin = require_roles(Role.ADMIN)


def require_employee(user: User = Depends(require_staff), db: Session = Depends(get_db)) -> Employee:
    """Self-service endpoints: the logged-in user must be linked to an employee record."""
    emp = db.scalar(select(Employee).where(Employee.user_id == user.id))
    if not emp:
        raise HTTPException(
            status_code=403,
            detail="Your account isn't linked to an employee profile yet. Please contact HR.",
        )
    return emp


# ---------------------------------------------------------------------------
# Tiny in-memory login throttle (per IP + email). Use Redis for multi-instance.
# ---------------------------------------------------------------------------
_FAILED: dict[str, deque] = defaultdict(deque)
MAX_FAILURES = 8
WINDOW_SECONDS = 15 * 60


def check_login_throttle(key: str) -> None:
    q = _FAILED[key]
    cutoff = time.monotonic() - WINDOW_SECONDS
    while q and q[0] < cutoff:
        q.popleft()
    if len(q) >= MAX_FAILURES:
        raise HTTPException(
            status_code=429, detail="Too many failed attempts. Please try again in 15 minutes."
        )


def record_login_failure(key: str) -> None:
    _FAILED[key].append(time.monotonic())


def clear_login_failures(key: str) -> None:
    _FAILED.pop(key, None)
