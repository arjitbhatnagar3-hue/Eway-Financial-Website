# EWAY Financial Consultancy Pvt. Ltd. — Website & HR Portal

Company website and internal **HR portal** for **EWAY FINANCIAL CONSULTANCY PRIVATE LIMITED**
(CIN: U74900UP2009PTC037001), built with **Python + FastAPI**, **SQLAlchemy** and a
**PostgreSQL** (or SQLite) database, with a clean vanilla-JS frontend.

| Part | URL | Who |
| ---- | --- | --- |
| Public website | `/` | Everyone |
| Login / signup | `/login`, `/signup` | Everyone |
| **HR Portal** | `/hr` | Staff (admin, HR, employees) |
| API docs (Swagger) | `/docs` | Developers |

---

## 1. Quick start (2 minutes, no database install needed)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py create-admin          # asks for email, name, password
python manage.py seed-demo             # optional: sample employees, leave, payroll…

uvicorn main:app --reload
```

Open http://localhost:8000/login, sign in with your admin account and you'll land on the HR portal.

Without any configuration the app creates a local **SQLite** file, `eway.db`. That's fine for
development. For the live site, connect **PostgreSQL** as described in section 3.

Demo logins (after `seed-demo`): **HR** `priya@ewayfinancial.in` / `Demo@12345`,
**Employee** `rohit@ewayfinancial.in` / `Demo@12345`.

---

## 2. HR Portal features

Each role sees different parts of the portal:

| Role | How they get it | What they can do |
| ---- | --------------- | ---------------- |
| **Admin** | `manage.py create-admin` or `ADMIN_EMAIL` env var | Everything, plus **Users & Roles** and deleting records |
| **HR** | Admin sets the role in *Users & Roles* | Employees, leave approvals, attendance register, payroll, departments, announcements, website enquiries |
| **Employee** | HR adds them on *Employees* (a login is created automatically) | Dashboard, check-in/out, apply for leave, payslips, directory, profile |
| **Client** | Public sign-up | Public website only |

**Modules**

- **Dashboard**: headcount, who's present or on leave today, pending approvals, payroll cost,
  headcount by department, upcoming birthdays, new joiners and announcements. Employees see their
  own attendance, leave balance and latest payslip.
- **Employees**: full records covering personal details, job, reporting manager, compensation,
  PAN, bank and statutory flags. Includes search and filters, **CSV export**, auto employee IDs
  (`EW-0001`…) and one-click portal login creation or password reset with a one-time temporary
  password. Setting status to *Exited* disables the login automatically.
- **Leave**: casual 12, sick 12 and earned 15 days a year, plus unpaid (LOP). Balances are checked,
  overlapping requests are blocked, Sundays are excluded and managers can't approve their own
  leave. Requests move through approve, reject (with a note) and cancel.
- **Attendance**: employees check in and out. HR has a daily register to mark or correct anyone,
  and approved leave shows up there automatically.
- **Payroll**: one click generates payslips for a month (Basic 50% / HRA 20% / Special 30%, PF at
  12% of basic capped at ₹1,800, monthly TDS, loss-of-pay and mid-month joiner pro-rating). HR
  reviews, re-runs, then **marks as paid**. Only then do employees see the payslip. Payslips can be
  printed or saved as PDF, with the amount in words (Indian numbering).
- **Departments**, **Announcements** (pinnable), **Staff directory**.
- **Website enquiries**: the public contact form now saves to the database, with a proper inbox
  (new → read → replied → archived).

The leave quotas, weekly off-days and salary split are in `eway/config.py` under *HR policy*.
Adjust them to match the company's actual policy.

---

## 3. Connecting a database

The whole app reads **one setting**: `DATABASE_URL`. The code is identical for SQLite and
PostgreSQL. Only the URL changes.

```bash
cp .env.example .env        # then edit .env
```

```ini
# .env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
ADMIN_EMAIL=you@ewayfinancial.in
ADMIN_PASSWORD=a-strong-password
```

On startup the app connects, **creates all tables automatically** and creates the admin account
if it doesn't exist. Check the connection at http://localhost:8000/api/health (it shows the
database status and engine) or with `python manage.py db-info`.

### Option A: Neon (recommended; free, doesn't expire)

1. Sign up at https://neon.tech → **Create project** (pick the region closest to India, e.g.
   *AWS Asia Pacific (Singapore)*).
2. On the dashboard click **Connect** and copy the connection string. It looks like
   `postgresql://neondb_owner:xxxx@ep-cool-name-123.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
3. Put it in `DATABASE_URL`, locally in `.env` or on Render (section 4).

### Option B: Supabase (free)

1. https://supabase.com → **New project** (region: *Mumbai*), and set a database password.
2. **Connect** → *Session pooler* → copy the URI and replace `[YOUR-PASSWORD]`.
3. Put it in `DATABASE_URL`.

### Option C: Render Postgres

In `render.yaml`, uncomment the `databases:` block and the `fromDatabase:` lines, and Render wires
`DATABASE_URL` for you. ⚠️ Render's **free** Postgres is **deleted 30 days after creation**, so
use at least the `basic-256mb` plan for real HR data.

### Option D: PostgreSQL on your own computer

```bash
docker compose up --build                            # Postgres + the site on :8000
docker compose exec web python manage.py seed-demo   # optional sample data
```

Or install PostgreSQL yourself and use `DATABASE_URL=postgresql://postgres:password@localhost:5432/eway`.

> `postgres://` URLs (Render/Heroku style) are accepted too. They're converted for the
> `psycopg` driver automatically.

### Moving existing data from the old JSON files

Earlier versions stored users and enquiries in `users.json` / `messages.json`. Move them into the
database once. Existing passwords keep working:

```bash
python manage.py import-json
```

---

## 4. Deploying (Render)

1. Create a Postgres database (Neon or Supabase, above) and copy its URL.
2. On render.com: **New + → Blueprint →** pick this repo. When asked, fill in
   `DATABASE_URL`, `ADMIN_EMAIL` and `ADMIN_PASSWORD`.
   For an existing service: **Environment →** add those three variables → **Save & deploy**.
3. Visit `https://<your-app>.onrender.com/api/health`. It should say `"engine": "postgresql"`.
4. Log in at `/login` with the admin email and password → HR Portal.

> If `DATABASE_URL` is missing on Render, the app logs a loud error. It falls back to SQLite on
> Render's temporary disk, and **all data is lost on each deploy**.

Docker anywhere else: `docker build -t eway . && docker run -p 8000:8000 -e DATABASE_URL=… eway`.

---

## 5. Project structure

```
├── main.py              # FastAPI app: company API, routers, static pages
├── company_data.py      # Public company content (services, directors, FAQ…)
├── manage.py            # CLI: create-admin, seed-demo, import-json, db-info
├── eway/
│   ├── config.py        # Settings (DATABASE_URL, admin, HR policy)
│   ├── database.py      # SQLAlchemy engine, session, table creation
│   ├── models.py        # Database tables
│   ├── schemas.py       # Request validation (Pydantic)
│   ├── security.py      # Password hashing, sessions, role checks
│   ├── services.py      # HR rules: leave balances, working days, payroll maths
│   ├── serializers.py   # DB rows → JSON
│   ├── bootstrap.py     # Startup: create tables + first admin
│   └── routers/
│       ├── auth.py      # /api/auth/*
│       ├── contact.py   # /api/contact, /api/admin/*
│       └── hr.py        # /api/hr/*
├── static/
│   ├── index.html · login.html · signup.html · hr.html
│   ├── css/style.css (website) · css/hr.css (portal)
│   └── js/app.js · js/auth.js · js/hr.js
├── tests/               # pytest suite (runs on SQLite or PostgreSQL)
├── .env.example · docker-compose.yml · Dockerfile · render.yaml
```

### Database tables

```
users ─┬─< sessions                    departments ─< employees
       └── employees ─┬─< leave_requests
                      ├─< attendance       announcements
                      └─< payslips         contact_messages
```

---

## 6. API overview

Full, interactive reference at **`/docs`**.

| Area | Endpoints |
| ---- | --------- |
| Public | `GET /api/health · company · services · directors · compliance · testimonials · faq · stats`, `POST /api/contact` |
| Auth | `POST /api/auth/signup · login · logout · change-password`, `GET /api/auth/me` |
| HR (staff) | `GET /api/hr/dashboard · directory · me · announcements · departments` |
| Self-service | `GET/POST /api/hr/leave/mine · /leave`, `POST /api/hr/leave/{id}/cancel`, `POST /api/hr/attendance/check-in · check-out`, `GET /api/hr/attendance/mine`, `GET /api/hr/payslips/mine · /payslips/{id}` |
| HR / admin | `GET/POST /api/hr/employees`, `GET/PATCH/DELETE /api/hr/employees/{id}`, `POST /api/hr/employees/{id}/login`, `GET /api/hr/employees/export.csv`, `GET /api/hr/leave`, `POST /api/hr/leave/{id}/approve · reject`, `GET/PUT /api/hr/attendance`, `POST /api/hr/payroll/run · pay-all · {id}/pay`, `GET /api/hr/payroll`, departments & announcements CRUD |
| Admin | `GET/PATCH /api/admin/users`, `GET/PATCH/DELETE /api/admin/enquiries` |

---

## 7. Security

- Passwords hashed with **PBKDF2-SHA256** (300k iterations, per-user salt).
- Sessions: random 256-bit token in an **HttpOnly, SameSite=Lax** cookie (Secure on HTTPS). Only
  a SHA-256 hash of the token is stored in the database. Changing the password signs out other
  devices, and deactivating a user signs them out everywhere.
- Every HR endpoint is protected server-side by role (`require_manager`, `require_employee`…).
  Hiding menu items in the UI is only cosmetic.
- PAN and bank numbers are masked on payslips. Login attempts are rate-limited (8 failures / 15 min).
- Security headers and `Cache-Control: no-store` on API responses.

## 8. Tests

```bash
pip install -r requirements-dev.txt
pytest                                                                  # SQLite
TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/eway_test pytest  # PostgreSQL
```

## 9. Customising the public site

- Company facts, services, directors, FAQ: `company_data.py`
- Design and copy: `static/css/style.css`, `static/index.html`
- Founder photos: put images in `static/images/` and set `photo="images/…jpg"` on the director
  in `company_data.py`.

## 10. Recommended next steps

- **Schema migrations with Alembic.** Tables are created automatically. Once the site is live,
  add Alembic before changing existing columns.
- **Email notifications** (SMTP / SendGrid): new enquiry alerts, leave approved/rejected, payslip released.
- **Backups**: Neon, Supabase and paid Render plans have point-in-time restore. Otherwise schedule `pg_dump`.
- Holiday calendar, document uploads (offer letters, ID proofs) to S3, and Form 16.
