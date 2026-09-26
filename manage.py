"""
Management commands.

    python manage.py init-db                     # create tables
    python manage.py create-admin                # interactive: create / promote an admin
    python manage.py create-admin --email a@b.com --name "Divya Bhatnagar" --password '…'
    python manage.py seed-demo                   # sample departments, employees, leave, payroll
    python manage.py import-json                 # move legacy users.json / messages.json into the DB
    python manage.py db-info                     # show which database is in use + row counts
"""
import argparse
import getpass
import json
import random
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select

from eway.config import BASE_DIR, DATABASE_URL
from eway.database import SessionLocal, init_db
from eway.models import (
    Announcement,
    Attendance,
    ContactMessage,
    Department,
    Employee,
    LeaveRequest,
    Payslip,
    Role,
    User,
)
from eway.schemas import EMAIL_RE
from eway.security import hash_password
from eway.services import run_payroll, today_ist, working_days_between


def _safe_url(url: str) -> str:
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        return f"{scheme}://***@{rest.split('@', 1)[1]}"
    return url


def cmd_init_db(_args) -> None:
    init_db()
    print(f"✓ Tables ready on {_safe_url(DATABASE_URL)}")


def cmd_db_info(_args) -> None:
    init_db()
    print(f"Database: {_safe_url(DATABASE_URL)}")
    with SessionLocal() as db:
        for model in (User, Employee, Department, LeaveRequest, Attendance, Payslip, Announcement, ContactMessage):
            print(f"  {model.__tablename__:<18} {db.scalar(select(func.count()).select_from(model)):>6}")


def cmd_create_admin(args) -> None:
    init_db()
    email = (args.email or input("Admin email: ")).strip().lower()
    if not EMAIL_RE.match(email):
        sys.exit("✗ Invalid email address.")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            user.role = Role.ADMIN
            user.is_active = True
            if args.password:
                user.password_hash = hash_password(args.password)
            db.commit()
            print(f"✓ {email} is now an admin.")
            return
        name = args.name or input("Full name: ").strip() or "Administrator"
        password = args.password or getpass.getpass("Password (min 8 chars): ")
        if len(password) < 8:
            sys.exit("✗ Password must be at least 8 characters.")
        db.add(User(name=name, email=email, password_hash=hash_password(password), role=Role.ADMIN))
        db.commit()
        print(f"✓ Admin {email} created. Log in at /login → you'll land on /hr.")


def cmd_import_json(_args) -> None:
    """One-time migration from the old JSON-file storage."""
    init_db()
    users_file, messages_file = BASE_DIR / "users.json", BASE_DIR / "messages.json"
    with SessionLocal() as db:
        n_users = n_msgs = 0
        if users_file.exists():
            for u in json.loads(users_file.read_text(encoding="utf-8")):
                if db.scalar(select(User).where(User.email == u["email"].lower())):
                    continue
                db.add(
                    User(
                        id=u["id"], name=u["name"], email=u["email"].lower(), password_hash=u["password_hash"],
                        created_at=datetime.fromisoformat(u["created_at"]),
                    )
                )
                n_users += 1
        if messages_file.exists():
            for m in json.loads(messages_file.read_text(encoding="utf-8")):
                if db.get(ContactMessage, m["id"]):
                    continue
                db.add(
                    ContactMessage(
                        id=m["id"], name=m["name"], email=m["email"], phone=m.get("phone"),
                        service=m.get("service"), message=m["message"],
                        received_at=datetime.fromisoformat(m["received_at"]),
                    )
                )
                n_msgs += 1
        db.commit()
    print(f"✓ Imported {n_users} user(s) and {n_msgs} enquiry(ies). Existing passwords keep working.")
    print("  You can now delete users.json, sessions.json and messages.json.")


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------
DEMO_PASSWORD = "Demo@12345"
DEMO_DEPARTMENTS = [
    ("Advisory", "Corporate & business advisory, ROC compliance"),
    ("Taxation", "Income tax, GST and TDS"),
    ("Accounts", "Bookkeeping, payroll and MIS"),
    ("Credit & Banking", "Loans, working capital and bank liaison"),
    ("Operations", "Admin, front office and HR"),
]
DEMO_EMPLOYEES = [
    # name, designation, dept index, gross, dob, joined, gender
    ("Priya Sharma", "HR & Admin Manager", 4, 48000, "1990-10-08", "2016-04-01", "female"),
    ("Rohit Verma", "Senior Tax Consultant", 1, 62000, "1987-10-14", "2012-07-16", "male"),
    ("Anjali Gupta", "Tax Associate", 1, 32000, "1996-02-21", "2021-06-01", "female"),
    ("Vikas Saxena", "Accounts Executive", 2, 28000, "1994-11-30", "2019-01-07", "male"),
    ("Neha Agarwal", "Chartered Accountant", 0, 85000, "1989-05-17", "2014-09-15", "female"),
    ("Amit Khanna", "Credit Analyst", 3, 45000, "1992-10-03", "2018-03-12", "male"),
    ("Sneha Rastogi", "Compliance Associate", 0, 30000, "1998-08-25", "2023-02-01", "female"),
    ("Karan Mehrotra", "Article Assistant", 2, 12000, "2002-01-19", "2025-08-01", "male"),
    ("Pooja Singh", "Front Office Executive", 4, 18000, "1997-12-11", "2022-11-21", "female"),
]


def cmd_seed_demo(_args) -> None:
    init_db()
    rnd = random.Random(2009)
    today = today_ist()
    with SessionLocal() as db:
        if db.scalar(select(func.count(Employee.id))):
            sys.exit("✗ Employees already exist — demo data is only loaded into an empty HR database.")

        depts = [Department(name=n, description=d) for n, d in DEMO_DEPARTMENTS]
        db.add_all(depts)
        db.flush()

        emps: list[Employee] = []
        for i, (name, desig, d_idx, gross, dob, joined, gender) in enumerate(DEMO_EMPLOYEES, start=1):
            first = name.split()[0].lower()
            email = f"{first}@ewayfinancial.in"
            role = Role.HR if i == 1 else Role.EMPLOYEE
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(name=name, email=email, password_hash=hash_password(DEMO_PASSWORD), role=role)
                db.add(user)
                db.flush()
            e = Employee(
                employee_code=f"EW-{i:04d}", user_id=user.id, full_name=name, email=email,
                phone=f"+91 98{rnd.randint(10000000, 99999999)}", designation=desig,
                department_id=depts[d_idx].id, employment_type="intern" if "Article" in desig else "full_time",
                status="probation" if joined >= "2025-06-01" else "active",
                date_of_joining=date.fromisoformat(joined), date_of_birth=date.fromisoformat(dob), gender=gender,
                address="Bareilly, Uttar Pradesh", monthly_gross=gross,
                monthly_tds=round(gross * 0.05) if gross > 60000 else 0,
                pf_applicable=gross < 80000 and "Article" not in desig,
                pan=f"{''.join(rnd.choice('ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(3))}P{name.split()[-1][0]}{rnd.randint(1000, 9999)}{rnd.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}",
                bank_account=str(rnd.randint(10**11, 10**12 - 1)), bank_ifsc="SBIN0001234",
            )
            db.add(e)
            emps.append(e)
        db.flush()
        # reporting lines
        # reporting lines: the CA leads advisory/tax/accounts, HR manager leads the rest
        for e in emps:
            if e is emps[0] or e is emps[4]:
                continue
            core = e.department_id in (depts[0].id, depts[1].id, depts[2].id)
            e.manager_id = emps[4].id if core else emps[0].id

        # attendance for the last 20 working days
        d = today - timedelta(days=28)
        while d <= today:
            if working_days_between(d, d):
                for e in emps:
                    r = rnd.random()
                    status = "present" if r < 0.82 else "wfh" if r < 0.9 else "half_day" if r < 0.95 else "absent"
                    if d == today and rnd.random() < 0.3:
                        continue
                    ci = datetime(d.year, d.month, d.day, 4, rnd.randint(15, 59), tzinfo=timezone.utc)  # ~10:00 IST
                    co = None if d == today else ci + timedelta(hours=8, minutes=rnd.randint(0, 90))
                    db.add(Attendance(employee_id=e.id, date=d, status=status,
                                      check_in=ci if status != "absent" else None,
                                      check_out=co if status != "absent" else None))
            d += timedelta(days=1)

        # leave requests
        def leave(e, typ, start, end, status, reason):
            db.add(LeaveRequest(employee_id=e.id, leave_type=typ, start_date=start, end_date=end,
                                days=working_days_between(start, end), reason=reason, status=status,
                                reviewed_by_id=emps[0].user_id if status != "pending" else None,
                                reviewed_at=datetime.now(timezone.utc) if status != "pending" else None))

        leave(emps[2], "casual", today + timedelta(days=5), today + timedelta(days=6), "pending", "Family function in Lucknow")
        leave(emps[3], "sick", today - timedelta(days=12), today - timedelta(days=11), "approved", "Viral fever")
        leave(emps[5], "earned", today + timedelta(days=14), today + timedelta(days=20), "pending", "Annual vacation")
        leave(emps[6], "casual", today, today, "approved", "Personal work")
        leave(emps[7], "unpaid", today - timedelta(days=20), today - timedelta(days=19), "approved", "University exams")
        leave(emps[8], "sick", today + timedelta(days=2), today + timedelta(days=2), "pending", "Doctor's appointment")
        leave(emps[1], "casual", today - timedelta(days=40), today - timedelta(days=40), "rejected", "Filing deadline week")

        db.add_all([
            Announcement(title="Welcome to the new EWAY HR Portal",
                         body="Apply for leave, check in/out, and download your payslips here. "
                              "Please update your emergency contact with HR.", pinned=True, created_by_id=emps[0].user_id),
            Announcement(title="Tax audit deadline — 30 September",
                         body="All hands on deck for tax audit filings this month. Leave requests for the last week "
                              "of September will be reviewed case-by-case.", created_by_id=emps[0].user_id),
            Announcement(title="Diwali holidays",
                         body="The office will remain closed for Diwali. The holiday calendar has been shared on email.",
                         created_by_id=emps[0].user_id),
        ])
        db.add_all([
            ContactMessage(name="Ramesh Kumar", email="ramesh@example.com", service="Taxation & GST Advisory",
                           message="Need help with GST registration and monthly return filing for my trading firm."),
            ContactMessage(name="Sunita Traders", email="accounts@sunitatraders.in", service="Loans & Credit Advisory",
                           message="Looking for working capital loan advisory — about ₹50 lakh.", status="read"),
        ])
        db.commit()

        # payroll: last two months paid
        for back in (2, 1):
            y, m = today.year, today.month - back
            while m <= 0:
                m += 12
                y -= 1
            period = f"{y}-{m:02d}"
            run_payroll(db, period)
            for s in db.scalars(select(Payslip).where(Payslip.period == period)):
                s.status, s.paid_at = "paid", datetime.now(timezone.utc)
            db.commit()

    print("✓ Demo data loaded: 5 departments, 9 employees, attendance, leave, payroll, announcements.")
    print(f"  HR login:        priya@ewayfinancial.in / {DEMO_PASSWORD}")
    print(f"  Employee login:  rohit@ewayfinancial.in / {DEMO_PASSWORD}")


def main() -> None:
    parser = argparse.ArgumentParser(description="EWAY Financial management commands")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="Create database tables").set_defaults(func=cmd_init_db)
    sub.add_parser("db-info", help="Show database URL and row counts").set_defaults(func=cmd_db_info)
    p = sub.add_parser("create-admin", help="Create or promote an administrator")
    p.add_argument("--email")
    p.add_argument("--name")
    p.add_argument("--password")
    p.set_defaults(func=cmd_create_admin)
    sub.add_parser("seed-demo", help="Load sample HR data").set_defaults(func=cmd_seed_demo)
    sub.add_parser("import-json", help="Import legacy users.json / messages.json").set_defaults(func=cmd_import_json)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
