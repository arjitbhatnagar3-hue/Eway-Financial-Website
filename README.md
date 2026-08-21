# EWAY Financial Consultancy Pvt. Ltd. — Company Website

A professional company website for **EWAY FINANCIAL CONSULTANCY PRIVATE LIMITED**
(CIN: U74900UP2009PTC037001), built with **Python + FastAPI** as the backend and a
clean static frontend that renders all data from the API.

## Tech Stack

| Layer     | Technology                                        |
| --------- | ------------------------------------------------- |
| Backend   | Python 3.12+, FastAPI, Pydantic                   |
| Server    | Uvicorn                                           |
| Frontend  | Semantic HTML5, modern CSS (no framework), vanilla JS |
| Data      | `company_data.py` (single source of truth)         |
| Storage   | Contact-form enquiries saved to `messages.json`    |

## Quick Start

```bash
cd eway-financial
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then open:

- **Website:** http://localhost:8000
- **Interactive API docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Project Structure

```
eway-financial/
├── main.py              # FastAPI app: API routes + static serving + SPA fallback
├── company_data.py      # All company data (edit this to update the site)
├── messages.json        # Contact-form submissions (auto-created/appended)
├── requirements.txt
├── Dockerfile           # Docker deployment
├── .gitignore
└── static/
    ├── index.html       # Single-page website
    ├── login.html       # Login page
    ├── signup.html      # Signup page
    ├── images/          # Hero, service and testimonial photos
    ├── css/style.css    # Styles (warm cream editorial "Lumen" theme)
    └── js/
        ├── app.js       # Main page logic (fetches /api/*)
        └── auth.js      # Login/signup form logic
```

## API Endpoints

| Method | Endpoint         | Description                              |
| ------ | ---------------- | ---------------------------------------- |
| GET    | `/api/health`    | Service health check                     |
| GET    | `/api/company`   | Registered company details (MCA records) |
| GET    | `/api/services`  | Advisory services offered by the firm    |
| GET    | `/api/directors` | Directors of the company                 |
| GET    | `/api/compliance`| Annual compliance status (AGM, BS, etc.) |
| GET    | `/api/testimonials`| Client testimonials                 |
| GET    | `/api/faq`     | Frequently asked questions           |
| GET    | `/api/stats`     | Key headline numbers (capital, years…)   |
| POST   | `/api/contact`   | Save a website enquiry (validated)       |
| POST   | `/api/auth/signup` | Create an account (sets session cookie) |
| POST   | `/api/auth/login`  | Log in (sets session cookie)             |
| POST   | `/api/auth/logout` | End session, clear cookie                |
| GET    | `/api/auth/me`     | Current user, or 401 if not logged in    |

## Authentication

- Pages: `/login` and `/signup` (styled to match the site).
- Passwords are hashed with **PBKDF2-SHA256** (300,000 iterations, per-user
  salt) — plain text is never stored.
- Sessions are random 256-bit tokens stored server-side in `sessions.json`
  with a **7-day expiry**; the browser keeps the token in an
  **HttpOnly + SameSite=Lax cookie** (secure flag on when served over HTTPS).
- After login the nav bar shows the user's name with a **Log out** link.
- `users.json`, `sessions.json` and `messages.json` are created automatically
  at runtime — they are git-ignored. For production, move them to a database.

### Example: POST /api/contact

```bash
curl -X POST http://localhost:8000/api/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Ramesh Kumar","email":"ramesh@example.com","phone":"+91 98765 43210","service":"Taxation & GST Advisory","message":"Need help with my GST filing."}'
```

## Customising the Site

- **Company facts, services, directors, compliance:** edit `company_data.py` —
  the whole site updates automatically because it is data-driven.
- **Design / copy:** `static/css/style.css` and `static/index.html`.
- **Collected enquiries:** open `messages.json` (one JSON object per message,
  with an id and timestamp). For production, swap the storage helpers in
  `main.py` for a database (PostgreSQL, SQLite, …) or an email
  notification (SMTP).

### Adding founder photos

1. Put the images in `static/images/` (e.g. `static/images/divya-bhatnagar.jpg`).
2. In `company_data.py`, set the `photo` field on the director:
   ```python
   Director(
       name="Divya Bhatnagar",
       role="Director",
       bio="…",
       photo="images/divya-bhatnagar.jpg",
   )
   ```
3. Restart the server — the Leadership section shows the photo (initials are
   shown automatically when no photo is set).

### Which files matter (cheat sheet)

| File | Purpose |
| ---- | ------- |
| `main.py` | The brain — API routes, auth logic, static serving |
| `company_data.py` | All company content (edit this to update the site) |
| `requirements.txt` | Python packages to install |
| `static/index.html` | Main page structure |
| `static/login.html` / `static/signup.html` | Auth pages |
| `static/css/style.css` | All design |
| `static/js/app.js` | Main page logic (fetches the API) |
| `static/js/auth.js` | Login/signup form logic |

Runtime files (`messages.json`, `users.json`, `sessions.json`, `__pycache__/`)
are created automatically — you don't need to create or manage them.

## Docker

```bash
docker build -t eway-financial .
docker run --rm -p 8000:8000 eway-financial
```

## Production Notes

- Run behind a reverse proxy (Nginx/Caddy) with TLS, e.g. `company.ewayfinancial.in`.
- Use a real ASGI server manager (e.g. `uvicorn main:app --workers 2`).
- Store enquiries in a database and add rate limiting on `POST /api/contact`.
