"""One-off script: generates the sample PDF resources under static/resources/.

Run with:  python scripts/generate_pdfs.py
"""
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

OUT = Path(__file__).resolve().parent.parent / "static" / "resources"
OUT.mkdir(parents=True, exist_ok=True)

INK = (26, 26, 26)
MUTED = (110, 110, 115)
ACCENT = (51, 51, 53)


def new_pdf(title: str, subtitle: str) -> FPDF:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 0, 210, 32, style="F")
    pdf.set_xy(15, 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 8, "EWAY FINANCIAL CONSULTANCY PVT. LTD.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "CIN: U74900UP2009PTC037001  |  Bareilly, Uttar Pradesh", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(14)
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*MUTED)
    pdf.set_font("Helvetica", "I", 11)
    pdf.multi_cell(0, 6, subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_text_color(*INK)
    return pdf


def heading(pdf: FPDF, text: str) -> None:
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 11)


def para(pdf: FPDF, text: str) -> None:
    pdf.multi_cell(0, 6.2, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def bullets(pdf: FPDF, items: list[str]) -> None:
    pdf.set_font("Helvetica", "", 11)
    for item in items:
        pdf.set_x(pdf.l_margin + 4)
        pdf.cell(4, 6.2, chr(149))
        pdf.multi_cell(0, 6.2, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)


def footer_note(pdf: FPDF) -> None:
    pdf.set_y(-18)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(
        0, 8,
        "EWAY Financial Consultancy Pvt. Ltd.  |  caykagarwal@yahoo.com  |  "
        "This document is for general guidance only and is not a substitute "
        "for professional advice.",
        align="C",
    )


# ---------------------------------------------------------------------
# 1. Company Profile Brochure
# ---------------------------------------------------------------------
pdf = new_pdf(
    "Company Profile Brochure",
    "An overview of EWAY Financial Consultancy Pvt. Ltd.",
)
heading(pdf, "About Us")
para(
    pdf,
    "EWAY Financial Consultancy Private Limited (CIN: U74900UP2009PTC037001) "
    "was incorporated on 20 March 2009 and is registered with the Registrar "
    "of Companies, Kanpur. Headquartered in Bareilly, Uttar Pradesh, the "
    "firm has spent over fifteen years advising companies, proprietorships "
    "and individuals on taxation, corporate compliance, financial planning "
    "and credit advisory.",
)
heading(pdf, "What We Do")
bullets(
    pdf,
    [
        "Corporate & Business Advisory - incorporation, ROC/MCA compliance, annual filings",
        "Financial Planning & Analysis - budgeting, cash flow, MIS reporting",
        "Taxation & GST Advisory - income tax, GST, TDS, return filing and representation",
        "Loans & Credit Advisory - working capital, term loans, bank & NBFC negotiation",
        "Accounting & Bookkeeping - day-to-day books, payroll support, statutory ledgers",
        "Audit & Compliance Support - statutory audit coordination, compliance calendars",
    ],
)
pdf.add_page()
heading(pdf, "Registered Company Details")
rows = [
    ("Registration Number", "37001"),
    ("Registrar of Companies", "RoC-Kanpur"),
    ("Date of Incorporation", "20 March 2009"),
    ("Category", "Company limited by shares"),
    ("Class of Company", "Private (Non-government company)"),
    ("Authorised Share Capital", "Rs. 1,00,00,000"),
    ("Paid-up Share Capital", "Rs. 87,00,000"),
    ("Status", "Active"),
]
pdf.set_font("Helvetica", "", 11)
for label, value in rows:
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(65, 7.5, label)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7.5, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
heading(pdf, "Leadership")
para(pdf, "Divya Bhatnagar - Director")
para(pdf, "Sanjay Bhatnagar - Director")
heading(pdf, "Registered Office")
para(
    pdf,
    "Bhatnagar Complex, 2nd Floor, Mini Bye Pass Road, Opp. Officers "
    "Enclave, Near Karamchari Nagar, Bareilly, Uttar Pradesh 243122, India.",
)
footer_note(pdf)
pdf.output(str(OUT / "company-profile-brochure.pdf"))


# ---------------------------------------------------------------------
# 2. Monthly GST Compliance Checklist
# ---------------------------------------------------------------------
pdf = new_pdf(
    "Monthly GST Compliance Checklist",
    "A practical checklist to keep your GST filings on schedule.",
)
heading(pdf, "Before the 11th of Every Month")
bullets(
    pdf,
    [
        "Finalise outward supply invoices for the previous month",
        "Reconcile sales register against accounting books",
        "File GSTR-1 (outward supplies)",
    ],
)
heading(pdf, "Before the 20th of Every Month")
bullets(
    pdf,
    [
        "Download and review GSTR-2B for eligible input tax credit",
        "Reconcile purchase register against GSTR-2B",
        "Compute net GST liability and arrange payment",
        "File GSTR-3B (summary return + tax payment)",
    ],
)
heading(pdf, "Ongoing / As Applicable")
bullets(
    pdf,
    [
        "Generate e-way bills for eligible consignments",
        "Raise e-invoices if applicable to your turnover slab",
        "Respond to any notices or mismatches within the given timeline",
        "File CMP-08 quarterly if registered under the composition scheme",
    ],
)
heading(pdf, "Annually")
bullets(
    pdf,
    [
        "File GSTR-9 annual return (where applicable)",
        "Reconcile annual turnover with audited financial statements",
    ],
)
footer_note(pdf)
pdf.output(str(OUT / "gst-compliance-checklist.pdf"))


# ---------------------------------------------------------------------
# 3. Annual Corporate Compliance Calendar
# ---------------------------------------------------------------------
pdf = new_pdf(
    "Annual Corporate Compliance Calendar",
    "Key ROC, tax and statutory deadlines for private limited companies and LLPs.",
)
heading(pdf, "Quarterly / Periodic")
bullets(
    pdf,
    [
        "Board meetings - at least once every calendar quarter",
        "TDS payment - by the 7th of the following month",
        "TDS return (Form 24Q / 26Q) - quarterly, within the prescribed due date",
        "Advance tax instalments - 15 Jun, 15 Sep, 15 Dec, 15 Mar",
    ],
)
heading(pdf, "Annual - Company Law (MCA/ROC)")
bullets(
    pdf,
    [
        "Annual General Meeting - within 6 months of financial year end",
        "Form AOC-4 (financial statements) - within 30 days of AGM",
        "Form MGT-7 / MGT-7A (annual return) - within 60 days of AGM",
        "Form DPT-3 (return of deposits) - by 30 June",
        "DIR-3 KYC for all directors - by 30 September",
    ],
)
heading(pdf, "Annual - Tax")
bullets(
    pdf,
    [
        "Statutory audit completion - before income tax filing due date",
        "Income tax return filing - per applicable due date (with/without audit)",
        "GSTR-9 annual return - as notified for the financial year",
    ],
)
footer_note(pdf)
pdf.output(str(OUT / "annual-compliance-calendar.pdf"))


# ---------------------------------------------------------------------
# 4. Business Loan Documentation Guide
# ---------------------------------------------------------------------
pdf = new_pdf(
    "Business Loan Documentation Guide",
    "Documents typically required for working capital and term loan applications.",
)
heading(pdf, "KYC Documents")
bullets(
    pdf,
    [
        "PAN and Aadhaar of all partners / directors / proprietor",
        "Passport-size photographs",
        "Address proof of business premises",
        "Certificate of Incorporation, MOA & AOA (for companies)",
    ],
)
heading(pdf, "Financial Documents")
bullets(
    pdf,
    [
        "Audited financial statements for the last 2-3 years",
        "Provisional financials for the current year, if available",
        "Income tax returns for the last 2-3 years",
        "GST returns for the last 12 months",
        "Bank statements for the last 6-12 months (all operative accounts)",
    ],
)
heading(pdf, "Business & Collateral Documents")
bullets(
    pdf,
    [
        "Business plan / projected utilisation of funds note",
        "Existing loan sanction letters and repayment track record",
        "Property documents and valuation report, if offering collateral",
        "List of major customers / suppliers with trade references",
    ],
)
heading(pdf, "Tip")
para(
    pdf,
    "Reconcile GST returns with bank statement credits before applying - "
    "mismatches here are the single most common cause of delay during "
    "underwriting.",
)
footer_note(pdf)
pdf.output(str(OUT / "loan-documentation-guide.pdf"))

print("Generated 4 PDFs in", OUT)
