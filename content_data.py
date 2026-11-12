"""Team profiles and awards displayed on the public website."""
from pydantic import BaseModel


# --------------------------------------------------------------------------
# Team profiles (About Us → Team Profile)
# --------------------------------------------------------------------------
class TeamMember(BaseModel):
    id: str
    name: str
    role: str
    department: str
    bio: str
    photo: str | None = None  # path relative to static/
    email: str | None = None
    is_director: bool = False


TEAM: list[TeamMember] = [
    TeamMember(
        id="divya-bhatnagar",
        name="Divya Bhatnagar",
        role="Director",
        department="Leadership",
        bio=(
            "Co-founder and director of EWAY Financial Consultancy. Leads "
            "client advisory, practice management and long-standing "
            "relationships with clients across Uttar Pradesh."
        ),
        photo="images/team/divya-bhatnagar.jpg",
        is_director=True,
    ),
    TeamMember(
        id="sanjay-bhatnagar",
        name="Sanjay Bhatnagar",
        role="Director",
        department="Leadership",
        bio=(
            "Co-founder and director. Oversees advisory engagements across "
            "compliance, taxation and banking relationships for companies "
            "and individuals."
        ),
        photo="images/team/sanjay-bhatnagar.jpg",
        is_director=True,
    ),
]


# --------------------------------------------------------------------------
# Awards & recognition (About Us → Awards)
# --------------------------------------------------------------------------
class Award(BaseModel):
    id: str
    title: str
    issuer: str
    year: int
    description: str
    image: str | None = None


AWARDS: list[Award] = [
    Award(
        id="best-tax-advisory-firm",
        title="Best Regional Tax Advisory Firm",
        issuer="Uttar Pradesh Chamber of Commerce & Industry",
        year=2023,
        description=(
            "Recognised for consistent excellence in taxation and GST advisory "
            "services to SMEs across Uttar Pradesh."
        ),
    ),
    Award(
        id="excellence-in-client-service",
        title="Excellence in Client Service",
        issuer="Bareilly Trade & Industries Association",
        year=2021,
        description=(
            "Awarded for sustained client satisfaction and responsiveness "
            "across corporate advisory engagements."
        ),
    ),
    Award(
        id="15-years-of-trusted-service",
        title="15 Years of Trusted Service",
        issuer="EWAY Financial Consultancy — Milestone Recognition",
        year=2024,
        description=(
            "Commemorating fifteen years of advising companies, proprietors "
            "and individuals across Uttar Pradesh since incorporation in 2009."
        ),
    ),
]
