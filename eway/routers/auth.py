"""Signup / login / logout / current user / change password."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Role, User
from ..schemas import ChangePasswordRequest, LoginRequest, SignupRequest
from ..security import (
    check_login_throttle,
    clear_login_failures,
    end_all_sessions,
    end_session,
    hash_password,
    record_login_failure,
    require_user,
    start_session,
    verify_password,
)
from ..serializers import user_public

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _redirect_for(user: User) -> str:
    return "/hr" if user.role in Role.STAFF else "/"


@router.post("/signup", status_code=201)
def signup(payload: SignupRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    """Create a (client) account and log in. Staff roles are granted by an admin."""
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    start_session(db, user, request, response)
    return {"ok": True, "user": user_public(user), "redirect": _redirect_for(user)}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    email = payload.email.strip().lower()
    key = f"{request.client.host if request.client else '-'}|{email}"
    check_login_throttle(key)
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(payload.password, user.password_hash):
        record_login_failure(key)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated. Please contact the administrator.")
    clear_login_failures(key)
    start_session(db, user, request, response)
    return {"ok": True, "user": user_public(user), "redirect": _redirect_for(user)}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    end_session(db, request, response)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(require_user)) -> dict:
    """The logged-in user (401 if not authenticated)."""
    return {"user": user_public(user)}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Your current password is incorrect.")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="Choose a password different from the current one.")
    user.password_hash = hash_password(payload.new_password)
    end_all_sessions(db, user, keep_request=request)  # sign out other devices
    db.commit()
    return {"ok": True, "message": "Password updated. Other devices have been signed out."}