"""Public contact form + enquiries inbox + user/role management."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import record_activity
from ..database import get_db
from ..models import ActivityEvent, ContactMessage, Role, User
from ..schemas import ContactMessageIn, EnquiryUpdate, UserUpdate
from ..security import check_throttle, end_all_sessions, record_throttle_attempt, require_admin, require_manager
from ..serializers import enquiry_out, user_public

router = APIRouter(tags=["Contact & Admin"])


@router.post("/api/contact", status_code=201)
def submit_contact(payload: ContactMessageIn, request: Request, db: Session = Depends(get_db)) -> dict:
    """Save an enquiry from the website contact form."""
    throttle_key = "contact|" + (request.client.host if request.client else "unknown")
    check_throttle(db, throttle_key)
    record_throttle_attempt(db, throttle_key)
    msg = ContactMessage(**payload.model_dump())
    db.add(msg)
    db.flush()
    record_activity(db, "contact.submitted", None, "contact", msg.id)
    db.commit()
    return {
        "ok": True,
        "id": msg.id,
        "message": "Thank you! Your message has been received. Our team will get back to you within one business day.",
    }


# ---------------------------------------------------------------------------
# Enquiries inbox (admin + HR)
# ---------------------------------------------------------------------------
@router.get("/api/admin/enquiries")
def list_enquiries(
    status: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    _: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict:
    stmt = select(ContactMessage).order_by(ContactMessage.received_at.desc())
    if status:
        stmt = stmt.where(ContactMessage.status == status)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            ContactMessage.name.ilike(like) | ContactMessage.email.ilike(like) | ContactMessage.message.ilike(like)
        )
    counts = dict(db.execute(select(ContactMessage.status, func.count()).group_by(ContactMessage.status)).all())
    return {"items": [enquiry_out(m) for m in db.scalars(stmt.limit(500))], "counts": counts}


@router.patch("/api/admin/enquiries/{enquiry_id}")
def update_enquiry(
    enquiry_id: str, payload: EnquiryUpdate, actor: User = Depends(require_manager), db: Session = Depends(get_db)
) -> dict:
    msg = db.get(ContactMessage, enquiry_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Enquiry not found.")
    msg.status = payload.status
    record_activity(db, "contact.status_changed", actor, "contact", enquiry_id)
    db.commit()
    return enquiry_out(msg)


@router.delete("/api/admin/enquiries/{enquiry_id}", status_code=204)
def delete_enquiry(enquiry_id: str, actor: User = Depends(require_admin), db: Session = Depends(get_db)) -> None:
    msg = db.get(ContactMessage, enquiry_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Enquiry not found.")
    record_activity(db, "contact.deleted", actor, "contact", enquiry_id)
    db.delete(msg)
    db.commit()


# ---------------------------------------------------------------------------
# Users & roles (admin only)
# ---------------------------------------------------------------------------
@router.get("/api/admin/users")
def list_users(
    q: str | None = Query(default=None, max_length=100),
    role: str | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = select(User).order_by(User.created_at.desc())
    if role:
        stmt = stmt.where(User.role == role)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(User.name.ilike(like) | User.email.ilike(like))
    return [user_public(u) for u in db.scalars(stmt.limit(1000))]


@router.patch("/api/admin/users/{user_id}")
def update_user(
    user_id: str, payload: UserUpdate, admin: User = Depends(require_admin), db: Session = Depends(get_db)
) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id and (
        (payload.role and payload.role != Role.ADMIN) or payload.is_active is False
    ):
        raise HTTPException(status_code=400, detail="You can't remove your own admin access.")
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
        if not payload.is_active:
            end_all_sessions(db, user)
    record_activity(db, "user.access_changed", admin, "user", user.id)
    db.commit()
    return user_public(user)


@router.get("/api/admin/activity")
def list_activity(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Admin-only audit trail; event records omit sensitive payload values."""
    rows = db.scalars(
        select(ActivityEvent).order_by(ActivityEvent.created_at.desc(), ActivityEvent.id.desc())
        .offset(offset).limit(limit)
    ).all()
    return {"items": [
        {"id": e.id, "actor": e.actor_name, "role": e.actor_role, "action": e.action,
         "entity_type": e.entity_type, "entity_id": e.entity_id, "created_at": e.created_at.isoformat()}
        for e in rows
    ], "limit": limit, "offset": offset}
