"""
HR portal API.

Access levels
  • staff (admin / hr / employee) — dashboard, directory, announcements, own profile,
    own leave / attendance / payslips (self-service)
  • managers (admin / hr)         — employees, departments, leave approvals,
    attendance register, payroll, announcements
  • admin                         — delete employee records
"""
import csv
import io
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..config import LEAVE_TYPES
from ..database import get_db
from ..models import (
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
from ..schemas import (
    AnnouncementIn,
    AttendanceMark,
    DepartmentIn,
    EmployeeCreate,
    EmployeeUpdate,
    LeaveApply,
    LeaveReview,
    PayrollRun,
    PERIOD_RE,
)
from ..security import (
    end_all_sessions,
    generate_temp_password,
    hash_password,
    require_admin,
    require_employee,
    require_manager,
    require_staff,
)
from ..serializers import (
    announcement_out,
    attendance_out,
    department_out,
    employee_full,
    employee_summary,
    leave_out,
    payslip_out,
)
from ..services import (
    has_overlapping_leave,
    leave_balances,
    next_employee_code,
    now_ist,
    run_payroll,
    today_ist,
    working_days_between,
)

router = APIRouter(prefix="/api/hr", tags=["HR Portal"])

ACTIVE_STATUSES = ("active", "probation", "notice")


def _get_or_404(db: Session, model, pk, label: str):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{label} not found.")
    return obj


def _employee_for(db: Session, user: User) -> Employee | None:
    return db.scalar(select(Employee).where(Employee.user_id == user.id))


# ===========================================================================
# Dashboard
# ===========================================================================
@router.get("/dashboard")
def dashboard(user: User = Depends(require_staff), db: Session = Depends(get_db)) -> dict:
    today = today_ist()
    out: dict = {"today": today.isoformat(), "role": user.role}

    announcements = db.scalars(
        select(Announcement)
        .options(selectinload(Announcement.created_by))
        .order_by(Announcement.pinned.desc(), Announcement.created_at.desc())
        .limit(5)
    ).all()
    out["announcements"] = [announcement_out(a) for a in announcements]

    emp = _employee_for(db, user)
    if emp:
        att = db.scalar(select(Attendance).where(Attendance.employee_id == emp.id, Attendance.date == today))
        latest_slip = db.scalar(
            select(Payslip).where(Payslip.employee_id == emp.id).order_by(Payslip.period.desc()).limit(1)
        )
        out["me"] = {
            "employee": employee_summary(emp),
            "attendance_today": attendance_out(att) if att else None,
            "leave_balances": leave_balances(db, emp.id),
            "pending_leave": db.scalar(
                select(func.count(LeaveRequest.id)).where(
                    LeaveRequest.employee_id == emp.id, LeaveRequest.status == "pending"
                )
            ),
            "latest_payslip": payslip_out(latest_slip) if latest_slip else None,
        }

    if user.role in Role.MANAGERS:
        active = select(Employee).where(Employee.status.in_(ACTIVE_STATUSES))
        headcount = db.scalar(select(func.count()).select_from(active.subquery()))
        on_leave_today = db.scalars(
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.employee))
            .where(LeaveRequest.status == "approved", LeaveRequest.start_date <= today, LeaveRequest.end_date >= today)
        ).all()
        present_today = db.scalar(
            select(func.count(Attendance.id)).where(
                Attendance.date == today, Attendance.status.in_(("present", "wfh", "half_day"))
            )
        )
        pending = db.scalars(
            select(LeaveRequest)
            .options(selectinload(LeaveRequest.employee), selectinload(LeaveRequest.reviewed_by))
            .where(LeaveRequest.status == "pending")
            .order_by(LeaveRequest.created_at)
        ).all()
        dept_rows = db.execute(
            select(Department.name, func.count(Employee.id))
            .join(Employee, Employee.department_id == Department.id)
            .where(Employee.status.in_(ACTIVE_STATUSES))
            .group_by(Department.name)
            .order_by(func.count(Employee.id).desc())
        ).all()
        unassigned = db.scalar(
            select(func.count(Employee.id)).where(
                Employee.department_id.is_(None), Employee.status.in_(ACTIVE_STATUSES)
            )
        )
        status_rows = dict(db.execute(select(Employee.status, func.count()).group_by(Employee.status)).all())
        payroll_cost = db.scalar(
            select(func.coalesce(func.sum(Employee.monthly_gross), 0)).where(Employee.status.in_(ACTIVE_STATUSES))
        )
        recent_joiners = db.scalars(
            select(Employee)
            .options(selectinload(Employee.department))
            .where(Employee.date_of_joining >= today - timedelta(days=60))
            .order_by(Employee.date_of_joining.desc())
            .limit(5)
        ).all()

        # birthdays in the next 30 days
        upcoming = []
        for e in db.scalars(
            select(Employee).where(Employee.date_of_birth.is_not(None), Employee.status.in_(ACTIVE_STATUSES))
        ):
            dob = e.date_of_birth
            try:
                nxt = dob.replace(year=today.year)
            except ValueError:  # 29 Feb
                nxt = date(today.year, 3, 1)
            if nxt < today:
                try:
                    nxt = dob.replace(year=today.year + 1)
                except ValueError:
                    nxt = date(today.year + 1, 3, 1)
            if (nxt - today).days <= 30:
                upcoming.append({"id": e.id, "full_name": e.full_name, "date": nxt.isoformat(), "in_days": (nxt - today).days})
        upcoming.sort(key=lambda x: x["in_days"])

        departments = [{"name": n, "count": c} for n, c in dept_rows]
        if unassigned:
            departments.append({"name": "Unassigned", "count": unassigned})

        out["org"] = {
            "headcount": headcount,
            "status_counts": status_rows,
            "present_today": present_today,
            "on_leave_today": [
                {"employee_name": lv.employee.full_name, "leave_type": lv.leave_type, "end_date": lv.end_date.isoformat()}
                for lv in on_leave_today
            ],
            "pending_leave": [leave_out(lv) for lv in pending[:6]],
            "pending_leave_count": len(pending),
            "new_enquiries": db.scalar(select(func.count(ContactMessage.id)).where(ContactMessage.status == "new")),
            "departments": departments,
            "monthly_payroll": payroll_cost,
            "upcoming_birthdays": upcoming[:6],
            "recent_joiners": [employee_summary(e) for e in recent_joiners],
        }
    return out


# ===========================================================================
# Directory & own profile
# ===========================================================================
@router.get("/directory")
def directory(
    q: str | None = Query(default=None, max_length=100),
    _: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> list[dict]:
    stmt = (
        select(Employee)
        .options(selectinload(Employee.department))
        .where(Employee.status.in_(ACTIVE_STATUSES))
        .order_by(Employee.full_name)
    )
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Employee.full_name.ilike(like) | Employee.designation.ilike(like))
    return [employee_summary(e) for e in db.scalars(stmt)]


@router.get("/me")
def my_profile(emp: Employee = Depends(require_employee), db: Session = Depends(get_db)) -> dict:
    return {"employee": employee_full(emp), "leave_balances": leave_balances(db, emp.id)}


# ===========================================================================
# Departments
# ===========================================================================
@router.get("/departments")
def list_departments(_: User = Depends(require_staff), db: Session = Depends(get_db)) -> list[dict]:
    counts = dict(
        db.execute(
            select(Employee.department_id, func.count(Employee.id))
            .where(Employee.status.in_(ACTIVE_STATUSES))
            .group_by(Employee.department_id)
        ).all()
    )
    return [department_out(d, counts.get(d.id, 0)) for d in db.scalars(select(Department).order_by(Department.name))]


@router.post("/departments", status_code=201)
def create_department(payload: DepartmentIn, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(Department).where(func.lower(Department.name) == payload.name.strip().lower())):
        raise HTTPException(status_code=409, detail="A department with this name already exists.")
    d = Department(name=payload.name.strip(), description=payload.description)
    db.add(d)
    db.commit()
    return department_out(d, 0)


@router.patch("/departments/{dept_id}")
def update_department(
    dept_id: int, payload: DepartmentIn, _: User = Depends(require_manager), db: Session = Depends(get_db)
) -> dict:
    d = _get_or_404(db, Department, dept_id, "Department")
    clash = db.scalar(
        select(Department).where(func.lower(Department.name) == payload.name.strip().lower(), Department.id != dept_id)
    )
    if clash:
        raise HTTPException(status_code=409, detail="A department with this name already exists.")
    d.name, d.description = payload.name.strip(), payload.description
    db.commit()
    return department_out(d)


@router.delete("/departments/{dept_id}", status_code=204)
def delete_department(dept_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> None:
    d = _get_or_404(db, Department, dept_id, "Department")
    for e in d.employees:  # keep employees, just unassign them
        e.department_id = None
    db.delete(d)
    db.commit()


# ===========================================================================
# Employees (HR / admin)
# ===========================================================================
def _employee_query(q: str | None, department_id: int | None, status: str | None):
    stmt = select(Employee).options(
        selectinload(Employee.department), selectinload(Employee.manager), selectinload(Employee.user)
    )
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            Employee.full_name.ilike(like)
            | Employee.email.ilike(like)
            | Employee.employee_code.ilike(like)
            | Employee.designation.ilike(like)
        )
    if department_id:
        stmt = stmt.where(Employee.department_id == department_id)
    if status == "current":
        stmt = stmt.where(Employee.status.in_(ACTIVE_STATUSES))
    elif status:
        stmt = stmt.where(Employee.status == status)
    return stmt.order_by(Employee.employee_code)


@router.get("/employees")
def list_employees(
    q: str | None = Query(default=None, max_length=100),
    department_id: int | None = None,
    status: str | None = None,
    _: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [employee_full(e) for e in db.scalars(_employee_query(q, department_id, status))]


@router.get("/employees/export.csv")
def export_employees(
    q: str | None = None,
    department_id: int | None = None,
    status: str | None = None,
    _: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> Response:
    cols = [
        "employee_code", "full_name", "email", "phone", "designation", "department", "manager",
        "employment_type", "status", "date_of_joining", "date_of_exit", "date_of_birth",
        "monthly_gross", "monthly_tds", "pf_applicable", "pan", "bank_account", "bank_ifsc",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for e in db.scalars(_employee_query(q, department_id, status)):
        writer.writerow(employee_full(e))
    filename = f"eway-employees-{today_ist().isoformat()}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _validate_refs(db: Session, payload: EmployeeCreate | EmployeeUpdate, self_id: int | None = None) -> None:
    if payload.department_id and not db.get(Department, payload.department_id):
        raise HTTPException(status_code=422, detail="Selected department doesn't exist.")
    if payload.manager_id:
        if payload.manager_id == self_id:
            raise HTTPException(status_code=422, detail="An employee can't report to themselves.")
        if not db.get(Employee, payload.manager_id):
            raise HTTPException(status_code=422, detail="Selected manager doesn't exist.")
    clash = db.scalar(select(Employee).where(Employee.email == payload.email, Employee.id != (self_id or -1)))
    if clash:
        raise HTTPException(status_code=409, detail=f"{clash.full_name} ({clash.employee_code}) already uses this email.")


def _attach_login(db: Session, emp: Employee) -> dict:
    """Link an existing account with the same email, or create one with a temporary password."""
    user = db.scalar(select(User).where(User.email == emp.email))
    if user:
        other = _employee_for(db, user)
        if other and other.id != emp.id:
            raise HTTPException(status_code=409, detail="That login is already linked to another employee.")
        emp.user_id = user.id
        if user.role == Role.CLIENT:
            user.role = Role.EMPLOYEE
        return {"linked_existing": True, "temp_password": None}
    temp = generate_temp_password()
    user = User(name=emp.full_name, email=emp.email, password_hash=hash_password(temp), role=Role.EMPLOYEE)
    db.add(user)
    db.flush()
    emp.user_id = user.id
    return {"linked_existing": False, "temp_password": temp}


@router.post("/employees", status_code=201)
def create_employee(payload: EmployeeCreate, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    _validate_refs(db, payload)
    data = payload.model_dump(exclude={"create_login"})
    emp = Employee(employee_code=next_employee_code(db), **data)
    db.add(emp)
    db.flush()
    login = _attach_login(db, emp) if payload.create_login else None
    db.commit()
    db.refresh(emp)
    return {"employee": employee_full(emp), "login": login}


@router.get("/employees/{emp_id}")
def get_employee(emp_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    emp = _get_or_404(db, Employee, emp_id, "Employee")
    leaves = db.scalars(
        select(LeaveRequest).where(LeaveRequest.employee_id == emp.id).order_by(LeaveRequest.start_date.desc()).limit(10)
    ).all()
    slips = db.scalars(
        select(Payslip).where(Payslip.employee_id == emp.id).order_by(Payslip.period.desc()).limit(12)
    ).all()
    since = today_ist() - timedelta(days=30)
    att = db.scalars(
        select(Attendance).where(Attendance.employee_id == emp.id, Attendance.date >= since).order_by(Attendance.date.desc())
    ).all()
    reports = db.scalars(select(Employee).where(Employee.manager_id == emp.id).order_by(Employee.full_name)).all()
    return {
        "employee": employee_full(emp),
        "leave_balances": leave_balances(db, emp.id),
        "leave_requests": [leave_out(lv) for lv in leaves],
        "payslips": [payslip_out(p) for p in slips],
        "attendance": [attendance_out(a) for a in att],
        "direct_reports": [employee_summary(r) for r in reports],
    }


@router.patch("/employees/{emp_id}")
def update_employee(
    emp_id: int, payload: EmployeeUpdate, _: User = Depends(require_manager), db: Session = Depends(get_db)
) -> dict:
    emp = _get_or_404(db, Employee, emp_id, "Employee")
    _validate_refs(db, payload, self_id=emp.id)
    data = payload.model_dump()
    if data["status"] == "exited" and not data["date_of_exit"]:
        data["date_of_exit"] = today_ist()
    for k, v in data.items():
        setattr(emp, k, v)
    # an exited employee loses portal access (admins are managed from Users & Roles)
    if emp.status == "exited" and emp.user and emp.user.role != Role.ADMIN:
        emp.user.is_active = False
        end_all_sessions(db, emp.user)
    db.commit()
    db.refresh(emp)
    return {"employee": employee_full(emp)}


@router.post("/employees/{emp_id}/login")
def create_or_reset_login(emp_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    """Create a portal login for the employee, or reset their password to a new temporary one."""
    emp = _get_or_404(db, Employee, emp_id, "Employee")
    if emp.user:
        if emp.user.role == Role.ADMIN:
            raise HTTPException(status_code=403, detail="Admin passwords can't be reset from the HR portal.")
        temp = generate_temp_password()
        emp.user.password_hash = hash_password(temp)
        emp.user.is_active = True
        end_all_sessions(db, emp.user)
        db.commit()
        return {"reset": True, "email": emp.user.email, "temp_password": temp}
    login = _attach_login(db, emp)
    db.commit()
    return {"reset": False, "email": emp.email, **login}


@router.delete("/employees/{emp_id}", status_code=204)
def delete_employee(emp_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> None:
    """Permanently delete an employee and their HR records (prefer status = exited)."""
    emp = _get_or_404(db, Employee, emp_id, "Employee")
    for r in db.scalars(select(Employee).where(Employee.manager_id == emp.id)):
        r.manager_id = None
    db.delete(emp)
    db.commit()


# ===========================================================================
# Leave
# ===========================================================================
def _leave_query():
    return select(LeaveRequest).options(selectinload(LeaveRequest.employee), selectinload(LeaveRequest.reviewed_by))


@router.get("/leave")
def list_leave(
    status: str | None = None,
    employee_id: int | None = None,
    _: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict:
    stmt = _leave_query()
    if status:
        stmt = stmt.where(LeaveRequest.status == status)
    if employee_id:
        stmt = stmt.where(LeaveRequest.employee_id == employee_id)
    stmt = stmt.order_by(LeaveRequest.status != "pending", LeaveRequest.start_date.desc())
    counts = dict(db.execute(select(LeaveRequest.status, func.count()).group_by(LeaveRequest.status)).all())
    return {"items": [leave_out(lv) for lv in db.scalars(stmt.limit(500))], "counts": counts}


@router.get("/leave/mine")
def my_leave(emp: Employee = Depends(require_employee), db: Session = Depends(get_db)) -> dict:
    items = db.scalars(
        _leave_query().where(LeaveRequest.employee_id == emp.id).order_by(LeaveRequest.start_date.desc())
    ).all()
    return {
        "items": [leave_out(lv) for lv in items],
        "balances": leave_balances(db, emp.id),
        "leave_types": LEAVE_TYPES,
    }


@router.post("/leave", status_code=201)
def apply_leave(payload: LeaveApply, emp: Employee = Depends(require_employee), db: Session = Depends(get_db)) -> dict:
    days = working_days_between(payload.start_date, payload.end_date)
    if days == 0:
        raise HTTPException(status_code=422, detail="The selected dates fall entirely on weekly offs.")
    if payload.start_date < today_ist() - timedelta(days=30):
        raise HTTPException(status_code=422, detail="Leave can be back-dated by at most 30 days.")
    if payload.start_date.year != payload.end_date.year:
        raise HTTPException(status_code=422, detail="Please split leave that spans two calendar years.")
    if has_overlapping_leave(db, emp.id, payload.start_date, payload.end_date):
        raise HTTPException(status_code=409, detail="You already have leave requested for some of these dates.")
    if payload.leave_type != "unpaid":
        bal = next(b for b in leave_balances(db, emp.id, payload.start_date.year) if b["type"] == payload.leave_type)
        if days > bal["available"]:
            raise HTTPException(
                status_code=422,
                detail=f"Not enough {payload.leave_type} leave: {bal['available']} day(s) available, {days} requested.",
            )
    lv = LeaveRequest(employee_id=emp.id, days=days, **payload.model_dump())
    db.add(lv)
    db.commit()
    db.refresh(lv)
    return leave_out(lv)


def _review(db: Session, leave_id: int, reviewer: User, status: str, note: str | None) -> dict:
    lv = _get_or_404(db, LeaveRequest, leave_id, "Leave request")
    if lv.status != "pending":
        raise HTTPException(status_code=409, detail=f"This request is already {lv.status}.")
    if lv.employee.user_id == reviewer.id:
        raise HTTPException(status_code=403, detail="You can't approve or reject your own leave.")
    lv.status = status
    lv.review_note = note
    lv.reviewed_by_id = reviewer.id
    lv.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(lv)
    return leave_out(lv)


@router.post("/leave/{leave_id}/approve")
def approve_leave(
    leave_id: int, payload: LeaveReview | None = None, user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> dict:
    return _review(db, leave_id, user, "approved", payload.note if payload else None)


@router.post("/leave/{leave_id}/reject")
def reject_leave(
    leave_id: int, payload: LeaveReview | None = None, user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> dict:
    return _review(db, leave_id, user, "rejected", payload.note if payload else None)


@router.post("/leave/{leave_id}/cancel")
def cancel_leave(leave_id: int, emp: Employee = Depends(require_employee), db: Session = Depends(get_db)) -> dict:
    lv = _get_or_404(db, LeaveRequest, leave_id, "Leave request")
    if lv.employee_id != emp.id:
        raise HTTPException(status_code=404, detail="Leave request not found.")
    if lv.status == "pending" or (lv.status == "approved" and lv.start_date > today_ist()):
        lv.status = "cancelled"
        db.commit()
        db.refresh(lv)
        return leave_out(lv)
    raise HTTPException(status_code=409, detail="Only pending or upcoming approved leave can be cancelled.")


# ===========================================================================
# Attendance
# ===========================================================================
@router.post("/attendance/check-in")
def check_in(emp: Employee = Depends(require_employee), db: Session = Depends(get_db)) -> dict:
    today = today_ist()
    att = db.scalar(select(Attendance).where(Attendance.employee_id == emp.id, Attendance.date == today))
    if att and att.check_in:
        raise HTTPException(status_code=409, detail="You've already checked in today.")
    if not att:
        att = Attendance(employee_id=emp.id, date=today, status="present")
        db.add(att)
    att.check_in = now_ist()
    if att.status in ("absent", "leave"):
        att.status = "present"
    db.commit()
    return attendance_out(att)


@router.post("/attendance/check-out")
def check_out(emp: Employee = Depends(require_employee), db: Session = Depends(get_db)) -> dict:
    att = db.scalar(select(Attendance).where(Attendance.employee_id == emp.id, Attendance.date == today_ist()))
    if not att or not att.check_in:
        raise HTTPException(status_code=409, detail="Please check in first.")
    if att.check_out:
        raise HTTPException(status_code=409, detail="You've already checked out today.")
    att.check_out = now_ist()
    db.commit()
    return attendance_out(att)


def _month_range(month: str | None) -> tuple[date, date]:
    if month:
        if not PERIOD_RE.match(month):
            raise HTTPException(status_code=422, detail="Month must be YYYY-MM.")
        y, m = map(int, month.split("-"))
    else:
        t = today_ist()
        y, m = t.year, t.month
    start = date(y, m, 1)
    end = (date(y + (m == 12), m % 12 + 1, 1)) - timedelta(days=1)
    return start, end


@router.get("/attendance/mine")
def my_attendance(
    month: str | None = None, emp: Employee = Depends(require_employee), db: Session = Depends(get_db)
) -> dict:
    start, end = _month_range(month)
    rows = db.scalars(
        select(Attendance)
        .where(Attendance.employee_id == emp.id, Attendance.date >= start, Attendance.date <= end)
        .order_by(Attendance.date.desc())
    ).all()
    today = db.scalar(select(Attendance).where(Attendance.employee_id == emp.id, Attendance.date == today_ist()))
    summary: dict[str, int] = {}
    for r in rows:
        summary[r.status] = summary.get(r.status, 0) + 1
    return {
        "month": start.strftime("%Y-%m"),
        "working_days": working_days_between(start, min(end, today_ist())) if start <= today_ist() else 0,
        "today": attendance_out(today) if today else None,
        "summary": summary,
        "items": [attendance_out(r) for r in rows],
    }


@router.get("/attendance")
def attendance_register(
    day: date | None = Query(default=None, alias="date"),
    _: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict:
    """Everyone's attendance for one day (approved leave is shown automatically)."""
    day = day or today_ist()
    employees = db.scalars(
        select(Employee)
        .options(selectinload(Employee.department))
        .where(Employee.status.in_(ACTIVE_STATUSES), Employee.date_of_joining <= day)
        .order_by(Employee.full_name)
    ).all()
    records = {
        a.employee_id: a for a in db.scalars(select(Attendance).where(Attendance.date == day)).all()
    }
    on_leave = {
        lv.employee_id: lv.leave_type
        for lv in db.scalars(
            select(LeaveRequest).where(
                LeaveRequest.status == "approved", LeaveRequest.start_date <= day, LeaveRequest.end_date >= day
            )
        )
    }
    rows = []
    for e in employees:
        a = records.get(e.id)
        rows.append(
            {
                "employee": employee_summary(e),
                "attendance": attendance_out(a) if a else None,
                "on_leave": on_leave.get(e.id),
                "effective_status": a.status if a else ("leave" if e.id in on_leave else None),
            }
        )
    summary: dict[str, int] = {}
    for r in rows:
        key = r["effective_status"] or "unmarked"
        summary[key] = summary.get(key, 0) + 1
    return {"date": day.isoformat(), "is_weekly_off": working_days_between(day, day) == 0, "summary": summary, "rows": rows}


@router.put("/attendance")
def mark_attendance(payload: AttendanceMark, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    _get_or_404(db, Employee, payload.employee_id, "Employee")
    if payload.date > today_ist():
        raise HTTPException(status_code=422, detail="Attendance can't be marked for a future date.")
    att = db.scalar(
        select(Attendance).where(Attendance.employee_id == payload.employee_id, Attendance.date == payload.date)
    )
    if not att:
        att = Attendance(employee_id=payload.employee_id, date=payload.date)
        db.add(att)
    att.status = payload.status
    att.note = payload.note
    db.commit()
    return attendance_out(att)


# ===========================================================================
# Payroll
# ===========================================================================
def _slip_query():
    return select(Payslip).options(selectinload(Payslip.employee).selectinload(Employee.department))


@router.post("/payroll/run")
def payroll_run(payload: PayrollRun, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    """Generate (or refresh) draft payslips for a month. Paid payslips are never changed."""
    return run_payroll(db, payload.period)


@router.get("/payroll")
def payroll_list(period: str, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    if not PERIOD_RE.match(period):
        raise HTTPException(status_code=422, detail="Period must be YYYY-MM.")
    slips = db.scalars(_slip_query().where(Payslip.period == period)).all()
    slips = sorted(slips, key=lambda p: p.employee.employee_code)
    totals = {k: sum(getattr(p, k) for p in slips) for k in ("gross", "lop_deduction", "pf", "tds", "net_pay")}
    return {
        "period": period,
        "items": [payslip_out(p) for p in slips],
        "totals": totals,
        "paid": sum(1 for p in slips if p.status == "paid"),
        "count": len(slips),
    }


@router.post("/payroll/{slip_id}/pay")
def payroll_mark_paid(slip_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    slip = _get_or_404(db, Payslip, slip_id, "Payslip")
    if slip.status != "paid":
        slip.status = "paid"
        slip.paid_at = datetime.now(timezone.utc)
        db.commit()
    return payslip_out(slip)


@router.post("/payroll/pay-all")
def payroll_pay_all(payload: PayrollRun, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    now = datetime.now(timezone.utc)
    slips = db.scalars(select(Payslip).where(Payslip.period == payload.period, Payslip.status == "draft")).all()
    for s in slips:
        s.status, s.paid_at = "paid", now
    db.commit()
    return {"period": payload.period, "marked_paid": len(slips)}


@router.get("/payslips/mine")
def my_payslips(emp: Employee = Depends(require_employee), db: Session = Depends(get_db)) -> list[dict]:
    slips = db.scalars(
        _slip_query().where(Payslip.employee_id == emp.id, Payslip.status == "paid").order_by(Payslip.period.desc())
    ).all()
    return [payslip_out(p) for p in slips]


@router.get("/payslips/{slip_id}")
def get_payslip(slip_id: int, user: User = Depends(require_staff), db: Session = Depends(get_db)) -> dict:
    slip = _get_or_404(db, Payslip, slip_id, "Payslip")
    is_owner = slip.employee.user_id == user.id and slip.status == "paid"
    if not (is_owner or user.role in Role.MANAGERS):
        raise HTTPException(status_code=404, detail="Payslip not found.")
    return payslip_out(slip)


# ===========================================================================
# Announcements
# ===========================================================================
@router.get("/announcements")
def list_announcements(_: User = Depends(require_staff), db: Session = Depends(get_db)) -> list[dict]:
    items = db.scalars(
        select(Announcement)
        .options(selectinload(Announcement.created_by))
        .order_by(Announcement.pinned.desc(), Announcement.created_at.desc())
        .limit(100)
    ).all()
    return [announcement_out(a) for a in items]


@router.post("/announcements", status_code=201)
def create_announcement(payload: AnnouncementIn, user: User = Depends(require_manager), db: Session = Depends(get_db)) -> dict:
    a = Announcement(**payload.model_dump(), created_by_id=user.id)
    db.add(a)
    db.commit()
    db.refresh(a)
    return announcement_out(a)


@router.delete("/announcements/{ann_id}", status_code=204)
def delete_announcement(ann_id: int, _: User = Depends(require_manager), db: Session = Depends(get_db)) -> None:
    a = _get_or_404(db, Announcement, ann_id, "Announcement")
    db.delete(a)
    db.commit()