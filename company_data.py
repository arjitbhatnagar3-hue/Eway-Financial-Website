"""
Single source of truth for all public company data.

The FastAPI backend serves this data as JSON, and the website renders
everything from these models. Edit this file to update the site.
"""
from pydantic import BaseModel


def _inr_full(amount: float) -> str:
    """Format a number in Indian digit grouping, e.g. 8700000 -> ₹87,00,000."""
    digits = f"{int(amount)}"
    if len(digits) <= 3:
        return f"₹{digits}"
    last3 = digits[-3:]
    rest = digits[:-3]
    grouped = ""
    while len(rest) > 2:
        grouped = "," + rest[-2:] + grouped
        rest = rest[:-2]
    return f"₹{rest}{grouped},{last3}"


def _inr_short(amount: float) -> str:
    """Short Indian currency notation, e.g. 10000000 -> ₹1.00 Cr."""
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:.2f} Cr"
    if amount >= 1_00_000:
        return f"₹{amount / 1_00_000:.2f} L"
    return _inr_full(amount)


class Company(BaseModel):
    name: str
    short_name: str
    cin: str
    registration_number: str
    roc: str
    incorporated_on: str  # ISO date
    status: str
    category: str
    sub_category: str
    class_of_company: str
    listed: str
    nic_code: str
    nic_description: str
    authorized_share_capital: float
    paid_up_share_capital: float
    authorized_capital_formatted: str
    paid_up_capital_formatted: str
    authorized_capital_short: str
    paid_up_capital_short: str
    email: str
    address_lines: list[str]
    address_line: str


COMPANY = Company(
    name="EWAY FINANCIAL CONSULTANCY PRIVATE LIMITED",
    short_name="EWAY Financial",
    cin="U74900UP2009PTC037001",
    registration_number="37001",
    roc="RoC-Kanpur",
    incorporated_on="2009-03-20",
    status="Active",
    category="Company limited by shares",
    sub_category="Non-government company",
    class_of_company="Private",
    listed="Unlisted",
    nic_code="749",
    nic_description="Business activities n.e.c.",
    authorized_share_capital=10_000_000.0,
    paid_up_share_capital=8_700_000.0,
    authorized_capital_formatted=_inr_full(10_000_000.0),
    paid_up_capital_formatted=_inr_full(8_700_000.0),
    authorized_capital_short=_inr_short(10_000_000.0),
    paid_up_capital_short=_inr_short(8_700_000.0),
    email="caykagarwal@yahoo.com",
    address_lines=[
        "Bhatnagar Complex, 2nd Floor",
        "Mini Bye Pass Road, Opp. Officers Enclave",
        "Near Karamchari Nagar",
        "Bareilly, Uttar Pradesh 243122, India",
    ],
    address_line=(
        "Bhatnagar Complex, 2nd Floor, Mini Bye Pass Road, "
        "Opp. Officers Enclave, Near Karamchari Nagar, "
        "Bareilly, Uttar Pradesh 243122, India"
    ),
)


class Service(BaseModel):
    id: str
    title: str
    tagline: str
    description: str
    image: str | None = None  # path relative to static/, e.g. "images/service-audit.jpg"


SERVICES: list[Service] = [
    Service(
        id="corporate-advisory",
        title="Corporate & Business Advisory",
        tagline="Incorporation to annual filings",
        description=(
            "Company incorporation, ROC (MCA) compliance, annual filings, "
            "licenses and registrations, and ongoing secretarial support "
            "for companies, LLPs and proprietorships."
        ),
        image="images/service-advisory.jpg",
    ),
    Service(
        id="financial-planning",
        title="Financial Planning & Analysis",
        tagline="Budgeting · Cash flow · MIS",
        description=(
            "Budgeting, cash-flow management, MIS reporting and financial "
            "modelling that help you make confident, data-driven decisions "
            "for growth."
        ),
        image="images/service-planning.jpg",
    ),
    Service(
        id="taxation",
        title="Taxation & GST Advisory",
        tagline="Income tax · GST · TDS",
        description=(
            "Income tax, GST and TDS compliance, return filing, tax planning "
            "and representation before authorities — for individuals and "
            "businesses alike."
        ),
        image="images/service-tax.jpg",
    ),
    Service(
        id="credit",
        title="Loans & Credit Advisory",
        tagline="Bank loans · Working capital",
        description=(
            "Bank loans, working capital and credit advisory — structuring, "
            "documentation and negotiation with banks and NBFCs to secure "
            "funding that fits."
        ),
        image="images/service-credit.jpg",
    ),
    Service(
        id="accounting",
        title="Accounting & Bookkeeping",
        tagline="Books you can rely on",
        description=(
            "Day-to-day bookkeeping, payroll support, TDS and statutory "
            "ledgers, monthly closings and clean management accounts."
        ),
        image="images/service-accounting.jpg",
    ),
    Service(
        id="audit",
        title="Audit & Compliance Support",
        tagline="Stay ahead of deadlines",
        description=(
            "Statutory audit coordination, internal control reviews and "
            "compliance calendars that keep you ahead of MCA and tax "
            "deadlines."
        ),
        image="images/service-audit.jpg",
    ),
]


class Director(BaseModel):
    name: str
    role: str
    bio: str
    photo: str | None = None  # path relative to static/, e.g. "images/divya-bhatnagar.jpg"


DIRECTORS: list[Director] = [
    Director(
        name="Divya Bhatnagar",
        role="Director",
        bio=(
            "Co-founder and director of EWAY Financial Consultancy. Leads "
            "client advisory, practice management and long-standing "
            "relationships with clients across Uttar Pradesh."
        ),
    ),
    Director(
        name="Sanjay Bhatnagar",
        role="Director",
        bio=(
            "Co-founder and director. Oversees advisory engagements across "
            "compliance, taxation and banking relationships for companies "
            "and individuals."
        ),
    ),
]


class Testimonial(BaseModel):
    quote: str
    attribution: str
    image: str | None = None  # path relative to static/


TESTIMONIALS: list[Testimonial] = [
    Testimonial(
        quote=(
            "Their comprehensive forecast modeled multiple scenarios and gave "
            "us the confidence to expand into new markets ahead of schedule."
        ),
        attribution="Company Director, Manufacturing",
    ),
    Testimonial(
        quote=(
            "They streamlined our cash-flow management and uncovered tax "
            "efficiencies we didn't know were possible."
        ),
        attribution="Proprietor, Trading Business",
    ),
    Testimonial(
        quote=(
            "From incorporation to our first ROC filing, the team kept "
            "everything on track — patient, precise, and always responsive."
        ),
        attribution="Founder, Services Firm",
        image="images/testimonial.jpg",
    ),
]


class FaqItem(BaseModel):
    question: str
    answer: str


FAQS: list[FaqItem] = [
    FaqItem(
        question="How does the consultation process work?",
        answer=(
            "Start by scheduling a complimentary call. We'll discuss your "
            "objectives, gather preliminary information, and outline a "
            "proposed scope. A detailed engagement plan — complete with "
            "timeline and milestones — is provided before any commitment "
            "is required."
        ),
    ),
    FaqItem(
        question="Can your team adapt to different accounting systems?",
        answer=(
            "Yes. Our advisors are fluent in all major accounting and ERP "
            "platforms. During onboarding, we integrate seamlessly with your "
            "existing infrastructure, minimizing disruption and ensuring "
            "data integrity from day one."
        ),
    ),
    FaqItem(
        question="Do you offer flexible payment terms?",
        answer=(
            "Absolutely. Most projects are billed through itemized invoices "
            "tied to agreed milestones, giving you clear visibility into "
            "deliverables and costs throughout the engagement."
        ),
    ),
    FaqItem(
        question="Do you work with clients outside Bareilly?",
        answer=(
            "Yes. While our office is in Bareilly, we serve clients across "
            "Uttar Pradesh and nationwide — most engagements are handled "
            "remotely, with in-person visits scheduled as needed."
        ),
    ),
]


class Compliance(BaseModel):
    last_agm: str  # ISO date
    last_balance_sheet: str  # ISO date
    number_of_members: int
    company_status: str
    source: str


COMPLIANCE = Compliance(
    last_agm="2022-09-30",
    last_balance_sheet="2022-03-31",
    number_of_members=0,
    company_status="Active",
    source="Ministry of Corporate Affairs (MCA)",
)
