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

```bash
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open:

- **Website:** http://localhost:8000
- **Interactive API docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Site Map

The homepage nav exposes 8 top-level sections, each a real page:

- **Home** (`/`) — centered brand + city, services, testimonials, article &
  workshop previews, FAQ teaser and a contact form.
- **About Us** (`/about`) — overview with 4 sub-pages:
  - `/about/company-profile` — registered MCA details & compliance status
  - `/about/team` — team profiles (photos + bios)
  - `/about/awards` — awards & recognition
  - `/about/media` — press & media mentions
- **Services** (`/services`) — list of advisory services, each with its own
  page at `/services/{service-id}`.
- **Resources** (`/resources`) — a library of downloadable PDFs; each can be
  previewed in-page (modal viewer) or downloaded.
- **Workshops & Training** (`/workshops`) — upcoming workshops and training
  programmes.
- **Articles** (`/articles`) — articles written by the team, each with its
  own page at `/articles/{slug}`.
- **FAQ** (`/faq`) — frequently asked questions.
- **Contact Us** (`/contact`) — contact form and office details.

Plus: a site-wide search (`/search`, header search bar), a floating circular
social-media rail on the right edge, a small brand mark that appears
top-left once you scroll, and `/login`, `/signup`, `/hr` (staff HR portal).

## Project Structure

```
.
├── main.py                 # FastAPI app: API routes, page routes, static serving
├── company_data.py         # Core company facts, services, directors, FAQ (source of truth)
├── content_data.py         # Team, awards, media, articles, workshops, resources (source of truth)
├── scripts/
│   └── generate_pdfs.py    # Regenerates the sample PDFs in static/resources/
├── eway/
│   ├── routers/
│   │   ├── auth.py         # Signup/login/session endpoints
│   │   ├── contact.py      # Contact form + enquiries inbox + user/role admin
│   │   ├── content.py      # Team / awards / media / articles / workshops / resources / search
│   │   └── hr.py           # HR portal (employees, leave, attendance, payroll)
│   ├── database.py, models.py, schemas.py, security.py, services.py, serializers.py
│   └── config.py           # Settings (DATABASE_URL, HR policy, etc.)
├── requirements.txt
├── Dockerfile
└── static/
    ├── index.html, about.html, about-company-profile.html, about-team.html,
    │   about-awards.html, about-media.html, services.html, service-detail.html,
    │   resources.html, workshops.html, articles.html, article-detail.html,
    │   faq.html, contact.html, search.html, login.html, signup.html, hr.html
    ├── images/              # Hero, service, team, awards, workshop photos
    ├── resources/           # Downloadable PDF resources
    ├── css/style.css        # All styles
    └── js/
        ├── layout.js        # Shared header/nav/search/social-rail/footer (every page)
        ├── common.js        # Shared helpers (fetchJSON, toast, contact form, PDF modal)
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
| GET    | `/api/media`          | Press & media mentions                    |
| GET    | `/api/articles`       | Articles written by the team              |
| GET    | `/api/articles/{slug}`| A single article's full content           |
| GET    | `/api/workshops`      | Workshops & training programmes           |
| GET    | `/api/workshops/{id}` | A single workshop's detail                |
| GET    | `/api/resources`      | Downloadable PDF resource library         |
| GET    | `/api/compliance`     | Annual compliance status (AGM, BS, etc.)  |
| GET    | `/api/testimonials`   | Client testimonials                       |
| GET    | `/api/faq`            | Frequently asked questions                |
| GET    | `/api/stats`          | Key headline numbers (capital, years…)    |
| GET    | `/api/search?q=`      | Site-wide search across all content types |
| POST   | `/api/contact`        | Save a website enquiry (validated)        |
| POST   | `/api/auth/signup`    | Create an account (sets session cookie)   |
| POST   | `/api/auth/login`     | Log in (sets session cookie)              |
| POST   | `/api/auth/logout`    | End session, clear cookie                 |
| GET    | `/api/auth/me`        | Current user, or 401 if not logged in     |

The HR portal exposes a further set of endpoints under `/api/hr/*` and
`/api/admin/*` — see `/docs` for the full, interactive list.

## Customising the Site

- **Core company facts, services, directors, FAQ:** edit `company_data.py`.
- **Team, awards, media, articles, workshops, PDF resources:** edit
  `content_data.py` — the relevant pages update automatically.
- **PDF resources:** generated by `scripts/generate_pdfs.py` into
  `static/resources/`. Edit the script and re-run it (`python
  scripts/generate_pdfs.py`) to regenerate them, or drop your own PDFs in
  `static/resources/` and reference them from `content_data.py`.
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
- Set `DATABASE_URL` to a PostgreSQL instance and add rate limiting on
  `POST /api/contact`.
