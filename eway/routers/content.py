"""Public content endpoints: team, awards, service lookup and site-wide search.

All data is served from `content_data.py` / `company_data.py` — edit those
files to update the site.
"""
from fastapi import APIRouter, HTTPException, Query

from company_data import FAQS, SERVICES
from content_data import AWARDS, TEAM

router = APIRouter(prefix="/api", tags=["Content"])


# --------------------------------------------------------------------------
# Team
# --------------------------------------------------------------------------
@router.get("/team")
def get_team() -> list[dict]:
    """All team member profiles (About Us → Team Profile)."""
    return [t.model_dump() for t in TEAM]


@router.get("/team/{member_id}")
def get_team_member(member_id: str) -> dict:
    for member in TEAM:
        if member.id == member_id:
            return member.model_dump()
    raise HTTPException(status_code=404, detail="Team member not found.")


# --------------------------------------------------------------------------
# Awards & recognition
# --------------------------------------------------------------------------
@router.get("/awards")
def get_awards() -> list[dict]:
    """Awards & recognition (About Us → Awards)."""
    return [a.model_dump() for a in AWARDS]


# --------------------------------------------------------------------------
# Single service lookup (service detail pages)
# --------------------------------------------------------------------------
@router.get("/services/{service_id}")
def get_service(service_id: str) -> dict:
    for service in SERVICES:
        if service.id == service_id:
            return service.model_dump()
    raise HTTPException(status_code=404, detail="Service not found.")


# --------------------------------------------------------------------------
# Site-wide search
# --------------------------------------------------------------------------
@router.get("/search")
def search(q: str = Query(default="", max_length=120)) -> dict:
    """Simple substring search across services, team, awards and FAQs."""
    term = q.strip().lower()
    if len(term) < 2:
        return {"query": q, "results": []}

    results: list[dict] = []

    def hit(haystacks: list[str]) -> bool:
        return any(term in (h or "").lower() for h in haystacks)

    for s in SERVICES:
        if hit([s.title, s.tagline, s.description]):
            results.append(
                {"type": "Service", "title": s.title, "description": s.tagline, "url": f"/services/{s.id}"}
            )
    for m in TEAM:
        if hit([m.name, m.role, m.bio, m.department]):
            results.append({"type": "Team", "title": m.name, "description": m.role, "url": "/about/team"})
    for aw in AWARDS:
        if hit([aw.title, aw.description, aw.issuer]):
            results.append({"type": "Award", "title": aw.title, "description": aw.description, "url": "/about/awards"})
    for f in FAQS:
        if hit([f.question, f.answer]):
            results.append({"type": "FAQ", "title": f.question, "description": f.answer, "url": "/faq"})

    return {"query": q, "results": results[:30]}
