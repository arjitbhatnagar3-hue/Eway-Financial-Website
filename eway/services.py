"""
HR business rules — kept out of the route handlers so they're easy to test
and to adapt to the company's actual policy (see HR policy in config.py).
"""
import calendar
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import (
    BASIC_PCT,
    HRA_PCT,
    IST,
    LEAVE_QUOTAS,
    PF_RATE,
    PF_WAGE_CEILING,
    WEEKLY_OFF_DAYS,
)
from .models import Employee, LeaveRequest, Payslip


def today_ist() -> date:
    return datetime.now(IST).date()


def now_ist() -> datetime:
    return datetime.now(IST)


# ---------------------------------------------------------------------------
# Calendar helpers
# ---------------------------------------------------------------------------
def working_days_between(start: date, end: date) -> int:
    """Working days in [start, end] inclusive, excluding weekly offs (Sundays)."""
    if end < start:
        return 0
    days = 0
    d = start
    while d <= end:
        if d.weekday() not in WEEKLY_OFF_DAYS:
            days += 1
        d += timedelta(days=1)
    return days


def month_bounds(period: str) -> tuple[date, date]:
    year, month = map(int, period.split("-"))
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------
def next_employee_code(db: Session) -> str:
    """EW-0001, EW-0002, … (based on the highest existing number)."""
    codes = db.scalars(select(Employee.employee_code).where(Employee.employee_code.like("EW-%"))).all()
    nums = [int(c[3:]) for c in codes if c[3:].isdigit()]
    return f"EW-{(max(nums) + 1) if nums else 1:04d}"


# ---------------------------------------------------------------------------
# Leave
# ---------------------------------------------------------------------------
def leave_balances(db: Session, employee_id: int, year: int | None = None) -> list[dict]:
    """Quota / used / pending / available per leave type for a calendar year."""
    year = year or today_ist().year
    y_start, y_end = date(year, 1, 1), date(year, 12, 31)
    rows = db.execute(
        select(LeaveRequest.leave_type, LeaveRequest.status, func.coalesce(func.sum(LeaveRequest.days), 0))
        .where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.start_date >= y_start,
            LeaveRequest.start_date <= y_end,
            LeaveRequest.status.in_(("approved", "pending")),
        )
        .group_by(LeaveRequest.leave_type, LeaveRequest.status)
    ).all()
    used: dict[str, int] = {}
    pending: dict[str, int] = {}
    for leave_type, status, total in rows:
        (used if status == "approved" else pending)[leave_type] = int(total)

    result = []
    for leave_type, quota in LEAVE_QUOTAS.items():
        u, p = used.get(leave_type, 0), pending.get(leave_type, 0)
        result.append(
            {"type": leave_type, "quota": quota, "used": u, "pending": p, "available": max(0, quota - u - p)}
        )
    result.append(
        {"type": "unpaid", "quota": None, "used": used.get("unpaid", 0),
         "pending": pending.get("unpaid", 0), "available": None}
    )
    return result


def has_overlapping_leave(db: Session, employee_id: int, start: date, end: date) -> bool:
    return bool(
        db.scalar(
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status.in_(("pending", "approved")),
                LeaveRequest.start_date <= end,
                LeaveRequest.end_date >= start,
            )
        )
    )


def unpaid_leave_days_in(db: Session, employee_id: int, start: date, end: date) -> int:
    """Approved loss-of-pay working days that fall inside [start, end]."""
    leaves = db.scalars(
        select(LeaveRequest).where(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == "approved",
            LeaveRequest.leave_type == "unpaid",
            LeaveRequest.start_date <= end,
            LeaveRequest.end_date >= start,
        )
    ).all()
    return sum(working_days_between(max(lv.start_date, start), min(lv.end_date, end)) for lv in leaves)


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------
def compute_payslip(employee: Employee, period: str, lop_days: int) -> dict:
    """
    Salary breakup for one month.

    gross  = monthly_gross (fixed)      basic = 50%, HRA = 20%, special = rest
    LOP    = gross × lop_days / working_days
    PF     = 12% of earned basic, capped at the ₹15,000 wage ceiling (max ₹1,800)
    TDS    = fixed monthly amount set on the employee
    net    = gross − LOP − PF − TDS
    """
    start, end = month_bounds(period)
    # pro-rate for joiners / leavers inside the month
    eff_start = max(start, employee.date_of_joining)
    eff_end = min(end, employee.date_of_exit) if employee.date_of_exit else end
    working_days = working_days_between(start, end)
    payable_span = working_days_between(eff_start, eff_end)
    not_employed_days = working_days - payable_span

    gross = employee.monthly_gross
    basic = round(gross * BASIC_PCT)
    hra = round(gross * HRA_PCT)
    special = gross - basic - hra

    lop_total = min(working_days, lop_days + not_employed_days)
    lop_deduction = round(gross * lop_total / working_days) if working_days else 0
    earned_basic = basic - round(basic * lop_total / working_days) if working_days else basic
    pf = round(min(earned_basic, PF_WAGE_CEILING) * PF_RATE) if employee.pf_applicable else 0
    tds = min(employee.monthly_tds, max(0, gross - lop_deduction - pf))
    net = max(0, gross - lop_deduction - pf - tds)

    return {
        "working_days": working_days,
        "lop_days": lop_total,
        "gross": gross,
        "basic": basic,
        "hra": hra,
        "special_allowance": special,
        "lop_deduction": lop_deduction,
        "pf": pf,
        "tds": tds,
        "net_pay": net,
    }


def run_payroll(db: Session, period: str) -> dict:
    """(Re)generate draft payslips for everyone employed during the month. Paid slips are never touched."""
    start, end = month_bounds(period)
    employees = db.scalars(
        select(Employee).where(
            Employee.date_of_joining <= end,
            (Employee.date_of_exit.is_(None)) | (Employee.date_of_exit >= start),
            Employee.monthly_gross > 0,
        )
    ).all()
    existing = {
        p.employee_id: p for p in db.scalars(select(Payslip).where(Payslip.period == period)).all()
    }
    created = updated = skipped = 0
    for emp in employees:
        if emp.status == "exited" and not emp.date_of_exit:
            skipped += 1
            continue
        slip = existing.get(emp.id)
        if slip and slip.status == "paid":
            skipped += 1
            continue
        values = compute_payslip(emp, period, unpaid_leave_days_in(db, emp.id, start, end))
        if slip:
            for k, v in values.items():
                setattr(slip, k, v)
            slip.generated_at = now_ist()
            updated += 1
        else:
            db.add(Payslip(employee_id=emp.id, period=period, **values))
            created += 1
    db.commit()
    return {"period": period, "created": created, "updated": updated, "skipped": skipped}
