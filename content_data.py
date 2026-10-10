"""
Extended content for the website: team profiles, awards & recognition,
media mentions, articles written by the team, workshops & training
programmes, and the downloadable resource (PDF) library.

Kept separate from `company_data.py` (which holds the core registered
company facts) so the two can be edited independently. Edit this file to
update team members, articles, workshops, awards, media mentions or PDFs.
"""
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
    TeamMember(
        id="aakriti-saxena",
        name="Aakriti Saxena",
        role="Head of Taxation & GST",
        department="Taxation",
        bio=(
            "Leads the taxation practice — income tax, GST and TDS advisory, "
            "return filings and representation before authorities for over "
            "a decade."
        ),
        photo="images/team/aakriti-saxena.jpg",
        email="caykagarwal@yahoo.com",
    ),
    TeamMember(
        id="rohit-malhotra",
        name="Rohit Malhotra",
        role="Senior Manager — Audit & Compliance",
        department="Audit",
        bio=(
            "Heads statutory audit coordination and compliance calendars, "
            "keeping client companies ahead of MCA and regulatory deadlines."
        ),
        photo="images/team/rohit-malhotra.jpg",
    ),
    TeamMember(
        id="neha-kapoor",
        name="Neha Kapoor",
        role="Client Relationship Manager",
        department="Client Services",
        bio=(
            "The first point of contact for clients — coordinates onboarding, "
            "documentation and day-to-day queries across all advisory lines."
        ),
        photo="images/team/neha-kapoor.jpg",
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
        image="images/awards/best-tax-advisory-firm.jpg",
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
        image="images/awards/excellence-in-client-service.jpg",
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
        image="images/awards/15-years-of-trusted-service.jpg",
    ),
]


# --------------------------------------------------------------------------
# Media mentions (About Us → Media)
# --------------------------------------------------------------------------
class MediaMention(BaseModel):
    id: str
    title: str
    outlet: str
    date: str  # ISO date
    excerpt: str
    url: str | None = None


MEDIA: list[MediaMention] = [
    MediaMention(
        id="gst-filing-deadlines-explainer",
        title="EWAY Financial explains new GST filing deadlines for SMEs",
        outlet="Bareilly Business Journal",
        date="2024-11-08",
        excerpt=(
            "Director Sanjay Bhatnagar breaks down upcoming GST return "
            "changes and what small businesses should do to stay compliant."
        ),
    ),
    MediaMention(
        id="local-firm-15-years",
        title="Local advisory firm marks 15 years of serving UP businesses",
        outlet="UP Udyog Times",
        date="2024-04-02",
        excerpt=(
            "A profile on EWAY Financial Consultancy's journey from a small "
            "practice in Bareilly to a trusted regional advisory firm."
        ),
    ),
    MediaMention(
        id="msme-credit-advisory-panel",
        title="Panel discussion: Credit access for MSMEs",
        outlet="CA Connect Webinar Series",
        date="2023-09-19",
        excerpt=(
            "Divya Bhatnagar joined a panel of advisors discussing working "
            "capital and credit challenges facing small manufacturers."
        ),
    ),
]


# --------------------------------------------------------------------------
# Articles written by the team (Articles)
# --------------------------------------------------------------------------
class Article(BaseModel):
    slug: str
    title: str
    author: str
    date: str  # ISO date
    category: str
    read_minutes: int
    excerpt: str
    image: str | None = None
    body: list[str]  # paragraphs


ARTICLES: list[Article] = [
    Article(
        slug="gst-checklist-small-business",
        title="A Practical GST Compliance Checklist for Small Businesses",
        author="Aakriti Saxena",
        date="2025-06-12",
        category="Taxation & GST",
        read_minutes=6,
        excerpt=(
            "The filing dates, reconciliations and records every small "
            "business owner should track each month to stay GST-compliant "
            "without last-minute stress."
        ),
        image="images/service-tax.jpg",
        body=[
            "Goods and Services Tax compliance is a recurring task, not a "
            "once-a-year event — and small businesses that treat it that way "
            "often end up paying avoidable interest and late fees.",
            "Start with a monthly calendar: GSTR-1 (outward supplies) is due "
            "on the 11th, GSTR-3B (summary return and tax payment) by the "
            "20th for most taxpayers, and composition dealers file CMP-08 "
            "quarterly. Mark these dates and build in a two-day buffer.",
            "Reconcile your sales register against GSTR-1 every month, not "
            "just at year-end. Mismatches compound quickly and are far "
            "easier to fix within the same filing period than six months "
            "later during an audit.",
            "Track input tax credit carefully. Only claim ITC that shows up "
            "in your GSTR-2B — claiming credit that your supplier hasn't "
            "reported invites notices and reversal with interest.",
            "Finally, keep a compliance folder (digital or physical) with "
            "invoices, e-way bills and reconciliation statements for each "
            "period. When our team runs your annual review, organised "
            "records cut the time — and the stress — in half.",
        ],
    ),
    Article(
        slug="choosing-right-business-structure",
        title="Proprietorship, Partnership, LLP or Private Limited — Which One Fits?",
        author="Divya Bhatnagar",
        date="2025-04-28",
        category="Corporate Advisory",
        read_minutes=7,
        excerpt=(
            "A founder's guide to picking a business structure based on "
            "liability, compliance burden, fundraising plans and tax "
            "treatment."
        ),
        image="images/service-advisory.jpg",
        body=[
            "One of the first — and most consequential — decisions a founder "
            "makes is the legal structure of the business. It shapes "
            "liability exposure, compliance obligations, and how easily you "
            "can raise capital later.",
            "A sole proprietorship is the simplest to start and has minimal "
            "compliance, but offers no separation between personal and "
            "business liability — a real risk once you take on debt or "
            "larger contracts.",
            "A partnership spreads capital and responsibility across "
            "partners but, like a proprietorship, leaves partners personally "
            "liable for business debts unless structured as an LLP.",
            "A Limited Liability Partnership (LLP) combines the operational "
            "flexibility of a partnership with limited liability protection, "
            "and suits professional services firms well. Compliance is "
            "lighter than a private limited company but heavier than a "
            "proprietorship.",
            "A Private Limited Company offers the strongest liability "
            "protection and is usually the preferred structure if you plan "
            "to raise external investment, but it comes with the highest "
            "compliance load — ROC filings, statutory audit and board "
            "governance from day one.",
            "There's no universally 'right' answer — it depends on your "
            "growth plans, risk tolerance and the compliance bandwidth you "
            "can commit to. We walk new founders through this decision as "
            "part of our incorporation advisory.",
        ],
    ),
    Article(
        slug="reading-your-cash-flow-statement",
        title="Reading Your Cash-Flow Statement Like an Advisor Does",
        author="Rohit Malhotra",
        date="2025-02-15",
        category="Financial Planning",
        read_minutes=5,
        excerpt=(
            "Profit on paper and cash in the bank are two different things. "
            "Here's how to spot cash-flow trouble before it becomes a crisis."
        ),
        image="images/service-planning.jpg",
        body=[
            "A profitable business can still run out of cash — it happens "
            "more often than most founders expect, usually because of the "
            "gap between recognising revenue and actually collecting it.",
            "Start with operating cash flow. If it's consistently lower than "
            "net profit, look at receivables — are customers taking longer "
            "to pay than your payment terms allow?",
            "Watch the cash conversion cycle: the time between paying "
            "suppliers and collecting from customers. A lengthening cycle is "
            "an early warning sign, even while the income statement still "
            "looks healthy.",
            "Separate one-off financing inflows (loans, capital infusions) "
            "from operating cash flow when judging the health of the core "
            "business — a loan can mask an operating shortfall for a while, "
            "but not indefinitely.",
            "Review a rolling 13-week cash-flow forecast monthly, not just "
            "the annual budget. Short-term visibility is what actually "
            "prevents a liquidity crunch.",
        ],
    ),
    Article(
        slug="loan-documentation-mistakes",
        title="Five Documentation Mistakes That Delay Business Loan Approvals",
        author="Sanjay Bhatnagar",
        date="2024-12-03",
        category="Loans & Credit",
        read_minutes=5,
        excerpt=(
            "Banks reject or delay more loan applications over paperwork "
            "gaps than over the underlying business case. Avoid these common "
            "mistakes."
        ),
        image="images/service-credit.jpg",
        body=[
            "Incomplete financial statements are the most common cause of "
            "delay — banks want audited (or at minimum, CA-certified) "
            "financials for the last two to three years, not provisional "
            "figures.",
            "Mismatched GST returns and bank statement credits raise "
            "immediate red flags during underwriting. Reconcile these before "
            "you apply, not after the bank asks.",
            "Missing KYC for all partners, directors or guarantors — not "
            "just the primary applicant — is a frequent, entirely avoidable "
            "delay.",
            "An unclear end-use of funds, without a simple projected "
            "utilisation note, makes underwriters nervous and slows "
            "approval, especially for working capital limits.",
            "Finally, outdated collateral valuations or incomplete property "
            "documents can stall disbursement even after approval. Get "
            "valuations refreshed before submission, not during.",
        ],
    ),
]


# --------------------------------------------------------------------------
# Workshops & training
# --------------------------------------------------------------------------
class Workshop(BaseModel):
    id: str
    title: str
    mode: str  # "In-person" | "Online" | "Hybrid"
    duration: str
    audience: str
    description: str
    topics: list[str]
    image: str | None = None
    next_batch: str | None = None  # human-readable date / cadence


WORKSHOPS: list[Workshop] = [
    Workshop(
        id="gst-compliance-for-startups",
        title="GST Compliance for Startups & Small Businesses",
        mode="In-person",
        duration="Half-day (4 hours)",
        audience="Founders, accountants and office managers",
        description=(
            "A hands-on workshop covering GST registration, monthly return "
            "filing, input tax credit rules and common mistakes that trigger "
            "notices — with worked examples from real filings."
        ),
        topics=[
            "Registration thresholds and voluntary registration",
            "GSTR-1, GSTR-3B and annual return walkthrough",
            "Input tax credit reconciliation (GSTR-2B)",
            "E-way bills and e-invoicing basics",
        ],
        image="images/workshops/gst-compliance-for-startups.jpg",
        next_batch="Last Saturday of every month, Bareilly office",
    ),
    Workshop(
        id="financial-planning-for-founders",
        title="Financial Planning & Cash-Flow Management for Founders",
        mode="Hybrid",
        duration="Full day (6 hours)",
        audience="First-time founders and small business owners",
        description=(
            "Build a working budget, a 13-week cash-flow forecast and a set "
            "of monthly MIS reports you can actually maintain — no finance "
            "background required."
        ),
        topics=[
            "Building a 12-month operating budget",
            "13-week rolling cash-flow forecasting",
            "Reading your own financial statements",
            "Simple monthly MIS templates",
        ],
        image="images/workshops/financial-planning-for-founders.jpg",
        next_batch="Quarterly — next session on request",
    ),
    Workshop(
        id="corporate-compliance-bootcamp",
        title="Corporate Compliance Bootcamp for New Companies",
        mode="Online",
        duration="Two evenings (3 hours total)",
        audience="Newly incorporated companies and LLPs",
        description=(
            "Everything a newly incorporated company needs to know in its "
            "first year — ROC filings, board meeting requirements, statutory "
            "registers and the annual compliance calendar."
        ),
        topics=[
            "Annual ROC filings (AOC-4, MGT-7)",
            "Board & statutory meeting requirements",
            "Statutory registers founders forget to maintain",
            "Building your own compliance calendar",
        ],
        image="images/workshops/corporate-compliance-bootcamp.jpg",
        next_batch="On request for incorporated clients",
    ),
]


# --------------------------------------------------------------------------
# Resource library (downloadable PDFs)
# --------------------------------------------------------------------------
class Resource(BaseModel):
    id: str
    title: str
    category: str
    description: str
    file: str  # path relative to static/
    pages: int


RESOURCES: list[Resource] = [
    Resource(
        id="company-profile-brochure",
        title="EWAY Financial — Company Profile Brochure",
        category="Company Profile",
        description=(
            "An overview of EWAY Financial Consultancy Pvt. Ltd. — our "
            "services, leadership and registered company details."
        ),
        file="resources/company-profile-brochure.pdf",
        pages=3,
    ),
    Resource(
        id="gst-compliance-checklist",
        title="Monthly GST Compliance Checklist",
        category="Taxation & GST",
        description=(
            "A printable monthly checklist covering GSTR-1, GSTR-3B, ITC "
            "reconciliation and e-way bill requirements."
        ),
        file="resources/gst-compliance-checklist.pdf",
        pages=2,
    ),
    Resource(
        id="annual-compliance-calendar",
        title="Annual Corporate Compliance Calendar",
        category="Corporate Advisory",
        description=(
            "Key ROC, tax and statutory deadlines for private limited "
            "companies and LLPs across the financial year."
        ),
        file="resources/annual-compliance-calendar.pdf",
        pages=2,
    ),
    Resource(
        id="loan-documentation-guide",
        title="Business Loan Documentation Guide",
        category="Loans & Credit",
        description=(
            "The documents banks and NBFCs typically require for working "
            "capital and term loan applications, organised by category."
        ),
        file="resources/loan-documentation-guide.pdf",
        pages=2,
    ),
]
