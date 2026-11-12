"""Small application audit helper. Never pass personal field values or secrets."""
from sqlalchemy.orm import Session

from .models import ActivityEvent, User


def record_activity(
    db: Session,
    action: str,
    actor: User | None = None,
    entity_type: str = "",
    entity_id: str | int = "",
) -> None:
    db.add(ActivityEvent(
        actor_user_id=actor.id if actor else None,
        actor_name=actor.name[:120] if actor else "System",
        actor_role=actor.role if actor else "system",
        action=action[:80], entity_type=entity_type[:50], entity_id=str(entity_id)[:80],
    ))
