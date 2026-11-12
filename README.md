# EWAY Financial Consultancy Pvt. Ltd. — Company Website

A professional company website for **EWAY FINANCIAL CONSULTANCY PRIVATE LIMITED**
(CIN: U74900UP2009PTC037001), built with **Python + FastAPI** as the backend and a
clean, multi-page static frontend that renders all data from the API.

## Tech Stack

| Layer     | Technology                                        |
| --------- | ------------------------------------------------- |
| Backend   | Python 3.12+, FastAPI, Pydantic, SQLAlchemy        |
| Server    | Uvicorn                                           |
| Frontend  | Semantic HTML5, modern CSS (no framework), vanilla JS |
| Data      | `company_data.py` + `content_data.py` (single source of truth) |
| Storage   | SQLite by default (`eway.db`); PostgreSQL via `DATABASE_URL` |

## Quick Start

### Windows PowerShell

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### macOS / Linux

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open:

- **Website:** http://localhost:8000
- **Interactive API docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Database setup

The app uses a local SQLite file for development. For a deployed site, connect a managed PostgreSQL database so records survive app redeploys. PostgreSQL storage is limited by the database plan; choose a plan with enough capacity and enable backups.

### Local setup

1. Copy `.env.example` to `.env` in the project root.
2. Keep `DATABASE_URL=sqlite:///./eway.db` for a local database, or replace it with a PostgreSQL URL for a shared development database.
3. If this is a new installation and you need the first HR administrator, set `ADMIN_EMAIL` and a strong `ADMIN_PASSWORD` in `.env`.
4. Start the app. It reads `.env`, connects through SQLAlchemy, and creates missing tables at startup.

PowerShell copy command:

```powershell
Copy-Item .env.example .env
```

### Paid production deployment (Render Blueprint)

1. Push this project to your GitHub repository.
2. In Render, choose **New → Blueprint**, connect the repository, and review the paid web service and paid PostgreSQL database in `render.yaml` before confirming. The current template provisions both in Singapore and keeps the database private to the service.
3. Enter a private `ADMIN_EMAIL` and a unique, long `ADMIN_PASSWORD` when Render requests the secret values. Do not share them or commit them in Git.
4. Let Render provision the database and deploy the site. The Blueprint connects the app to its managed PostgreSQL database automatically.
5. Open the deployment URL and check `/api/health`; it should report the database as `ok` and engine as `postgresql`. Then sign in and change the initial admin password. If you use another host, provide a strong private `APP_SECRET` as well; Render generates it from the Blueprint.

The Render plan and database disk in `render.yaml` are paid resources. Review current pricing, included storage, backup/PITR options, and upgrade path in Render before confirming; database storage is plan-limited, not endless. Keep the website and database in the same region. Never put a real database URL in frontend code, a committed `.env` file, screenshots, or public issue reports. Do not use the local SQLite database for a hosted deployment: many app hosts use temporary disks. Changing `DATABASE_URL` alone does not copy local records.

The app creates missing tables at startup. This does not alter existing table structures when the schema changes; back up the database before upgrades and apply schema migrations before deploying future model changes. The new audit trail records successful sign-ins and selected HR/admin actions without storing passwords or sensitive field values. Review the Activity Log in the admin portal and establish an approved retention/archive policy before live HR use.

## Site Map

The homepage nav exposes 8 top-level sections, each a real page:

- **Home** (`/`) — services, testimonials, FAQ teaser and a contact form.
- **About Us** (`/about`) — overview with 3 sub-pages:
  - `/about/company-profile` — registered MCA details & compliance status
  - `/about/team` — team profiles (photos + bios)
  - `/about/awards` — awards & recognition
- **Services** (`/services`) — list of advisory services, each with its own
  page at `/services/{service-id}`.
- **FAQ** (`/faq`) — frequently asked questions.
- **Contact Us** (`/contact`) — contact form and office details.

Plus: a site-wide search (`/search`, header search bar), a small brand mark
that appears top-left once you scroll, and `/login`, `/signup`, `/hr` (staff
HR portal). Social links appear after verified company profile URLs are added.

## Project Structure

```
.
├── main.py                 # FastAPI app: API routes, page routes, static serving
├── company_data.py         # Core company facts, services, directors, FAQ (source of truth)
├── content_data.py         # Team and awards (source of truth)
├── eway/
│   ├── routers/
│   │   ├── auth.py         # Signup/login/session endpoints
│   │   ├── contact.py      # Contact form + enquiries inbox + user/role admin
│   │   ├── content.py      # Team / awards / services / search
│   │   └── hr.py           # HR portal (employees, leave, attendance, payroll)
│   ├── database.py, models.py, schemas.py, security.py, services.py, serializers.py
│   └── config.py           # Settings (DATABASE_URL, HR policy, etc.)
├── requirements.txt
├── Dockerfile
└── static/
    ├── index.html, about.html, about_company_profile.html, about_team.html,
    │   about_awards.html, services.html, services_detail.html,
    │   faq.html, contact.html, search.html, login.html, signup.html, hr.html
    ├── images/              # Hero, service and testimonial photography
    ├── css/style.css        # All styles
    └── js/
        ├── layout.js        # Shared header/nav/search/social-rail/footer (every page)
        ├── common.js        # Shared helpers (fetchJSON, toast, contact form)
        ├── pages.js         # Per-page data fetching & rendering (keyed by <body data-page="">)
        └── auth.js          # Login/signup form logic
```

## API Endpoints

| Method | Endpoint             | Description                              |
| ------ | -------------------- | ----------------------------------------- |
| GET    | `/api/health`         | Service + database health check           |
| GET    | `/api/company`        | Registered company details (MCA records)  |
| GET    | `/api/services`       | Advisory services offered by the firm     |
| GET    | `/api/services/{id}`  | A single service's detail                 |
| GET    | `/api/directors`      | Directors of the company                  |
| GET    | `/api/team`           | All team profiles (directors + staff)     |
| GET    | `/api/team/{id}`      | A single team member's profile            |
| GET    | `/api/awards`         | Awards & recognition                      |
| GET    | `/api/compliance`     | Annual compliance status (AGM, BS, etc.)  |
| GET    | `/api/testimonials`   | Client testimonials                       |
| GET    | `/api/faq`            | Frequently asked questions                |
| GET    | `/api/stats`          | Key headline numbers (capital, years…)    |
| GET    | `/api/search?q=`      | Site-wide search across current content   |
| POST   | `/api/contact`        | Save a website enquiry (validated)        |
| POST   | `/api/auth/signup`    | Create an account (sets session cookie)   |
| POST   | `/api/auth/login`     | Log in (sets session cookie)              |
| POST   | `/api/auth/logout`    | End session, clear cookie                 |
| GET    | `/api/auth/me`        | Current user, or 401 if not logged in     |

The HR portal exposes a further set of endpoints under `/api/hr/*` and
`/api/admin/*` — see `/docs` for the full, interactive list.

## Customising the Site

- **Core company facts, services, directors, FAQ:** edit `company_data.py`.
- **Team and awards:** edit `content_data.py` — the relevant pages update
  automatically.
- **Navigation / header / footer / social links:** `static/js/layout.js`
  (shared across every page).
- **Design / copy:** `static/css/style.css` and the individual page HTML
  files in `static/`.

### Adding team photos

1. Put the image in `static/images/team/` (e.g. `static/images/team/your-name.jpg`).
2. In `content_data.py`, set the `photo` field on the `TeamMember`:
   ```python
   TeamMember(
       id="your-id",
       name="Your Name",
       role="Your Role",
       department="...",
       bio="…",
       photo="images/team/your-name.jpg",
   )
   ```
3. Restart the server — the Team Profile page shows the photo (initials are
   shown automatically when no photo is set).

### Which files matter (cheat sheet)

| File | Purpose |
| ---- | ------- |
| `main.py` | API routes, page routes, auth logic, static serving |
| `company_data.py` | Core company content (edit to update company facts) |
| `content_data.py` | Team, awards, media, articles, workshops, resources |
| `eway/routers/content.py` | API endpoints for the content above + search |
| `static/js/layout.js` | Shared header/nav/search/social-rail/footer |
| `static/js/pages.js` | Per-page rendering logic |
| `static/css/style.css` | All design |

Runtime files (`eway.db`, `__pycache__/`) are created automatically — you
don't need to create or manage them.

## Docker

```bash
docker build -t eway-financial .
docker run --rm -p 8000:8000 eway-financial
```

## Production Notes

- Run behind a reverse proxy (Nginx/Caddy) with TLS, e.g. `company.ewayfinancial.in`.
- Use a real ASGI server manager (e.g. `uvicorn main:app --workers 2`).
- The Render production template disables public API docs, enables secure cookies and HTTPS security headers, limits sessions to one day, and uses a database-backed request throttle shared across app instances.
- Employee CSV exports are restricted to admins and omit bank/PAN details. Employee records with leave, attendance, or payslip history cannot be hard-deleted; mark them exited to preserve records and revoke access.
- Payroll percentages are starter policy settings, not payroll/accounting advice. Have a qualified payroll professional validate the calculations, tax treatment, PF settings, leave rules, and payslip before paying staff.
- Before launch, review all registry figures and compliance dates against current
  official records, and confirm team biographies, testimonials, awards and media
  mentions with the people or sources involved. These details are editable in
  `company_data.py` and `content_data.py`.
