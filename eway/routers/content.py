"""Public content endpoints: team, awards, media, articles, workshops,
resources (PDF library), a single-service lookup and site-wide search.

All data is served from `content_data.py` / `company_data.py` — edit those
files to update the site.
"""
from fastapi import APIRouter, HTTPException, Query

from company_data import FAQS, SERVICES
from content_data import ARTICLES, AWARDS, MEDIA, RESOURCES, TEAM, WORKSHOPS

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
# Media mentions
# --------------------------------------------------------------------------
@router.get("/media")
def get_media() -> list[dict]:
    """Press & media mentions (About Us → Media)."""
    return [m.model_dump() for m in MEDIA]


# --------------------------------------------------------------------------
# Articles written by the team
# --------------------------------------------------------------------------
@router.get("/articles")
def get_articles(category: str | None = Query(default=None)) -> list[dict]:
    """Articles written by the team, newest first."""
    items = sorted(ARTICLES, key=lambda a: a.date, reverse=True)
    if category:
        items = [a for a in items if a.category.lower() == category.lower()]
    return [a.model_dump() for a in items]


@router.get("/articles/{slug}")
def get_article(slug: str) -> dict:
    for article in ARTICLES:
        if article.slug == slug:
            return article.model_dump()
    raise HTTPException(status_code=404, detail="Article not found.")


# --------------------------------------------------------------------------
# Workshops & training
# --------------------------------------------------------------------------
@router.get("/workshops")
def get_workshops() -> list[dict]:
    """Workshops & training programmes."""
    return [w.model_dump() for w in WORKSHOPS]


@router.get("/workshops/{workshop_id}")
def get_workshop(workshop_id: str) -> dict:
    for workshop in WORKSHOPS:
        if workshop.id == workshop_id:
            return workshop.model_dump()
    raise HTTPException(status_code=404, detail="Workshop not found.")


# --------------------------------------------------------------------------
# Resource library (downloadable PDFs)
# --------------------------------------------------------------------------
@router.get("/resources")
def get_resources() -> list[dict]:
    """Downloadable PDF resource library."""
    return [r.model_dump() for r in RESOURCES]


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
    """Simple substring search across services, articles, team, workshops,
    resources, awards, media and FAQs."""
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
    for a in ARTICLES:
        if hit([a.title, a.excerpt, a.category, a.author]):
            results.append(
                {"type": "Article", "title": a.title, "description": a.excerpt, "url": f"/articles/{a.slug}"}
            )
    for w in WORKSHOPS:
        if hit([w.title, w.description, w.audience]):
            results.append(
                {"type": "Workshop", "title": w.title, "description": w.description, "url": "/workshops"}
            )
    for m in TEAM:
        if hit([m.name, m.role, m.bio, m.department]):
            results.append({"type": "Team", "title": m.name, "description": m.role, "url": "/about/team"})
    for r in RESOURCES:
        if hit([r.title, r.description, r.category]):
            results.append({"type": "Resource", "title": r.title, "description": r.description, "url": "/resources"})
    for aw in AWARDS:
        if hit([aw.title, aw.description, aw.issuer]):
            results.append({"type": "Award", "title": aw.title, "description": aw.description, "url": "/about/awards"})
    for mm in MEDIA:
        if hit([mm.title, mm.excerpt, mm.outlet]):
            results.append({"type": "Media", "title": mm.title, "description": mm.excerpt, "url": "/about/media"})
    for f in FAQS:
        if hit([f.question, f.answer]):
            results.append({"type": "FAQ", "title": f.question, "description": f.answer, "url": "/faq"})

    return {"query": q, "results": results[:30]}