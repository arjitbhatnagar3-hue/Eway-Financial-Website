"""Convert ORM rows into JSON-ready dicts for the API."""
from datetime import date, datetime

from .models import (
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


def _iso(v: date | datetime | None) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat(timespec="seconds")
    return v.isoformat()


def mask(value: str | None, visible: int = 4) -> str | None:
    if not value:
        return value
    return "•" * max(0, len(value) - visible) + value[-visible:]


def user_public(user: User) -> dict:
    emp = user.employee
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_staff": user.role in Role.STAFF,
        "created_at": _iso(user.created_at),
        "last_login_at": _iso(user.last_login_at),
        "employee": (
            {"id": emp.id, "employee_code": emp.employee_code, "designation": emp.designation}
            if emp else None
        ),
    }


def department_out(d: Department, headcount: int | None = None) -> dict:
    out = {"id": d.id, "name": d.name, "description": d.description, "created_at": _iso(d.created_at)}
    if headcount is not None:
        out["headcount"] = headcount
    return out


def employee_summary(e: Employee) -> dict:
    """Fields safe to show every staff member (directory)."""
    return {
        "id": e.id,
        "employee_code": e.employee_code,
        "full_name": e.full_name,
        "email": e.email,
        "phone": e.phone,
        "designation": e.designation,
        "department": e.department.name if e.department else None,
        "department_id": e.department_id,
        "status": e.status,
        "date_of_joining": _iso(e.date_of_joining),
    }


def employee_full(e: Employee, *, sensitive: bool = True) -> dict:
    """Full record. `sensitive=False` masks PAN / bank details."""
    out = employee_summary(e)
    out.update(
        {
            "user_id": e.user_id,
            "has_login": e.user_id is not None,
            "login_role": e.user.role if e.user else None,
            "manager_id": e.manager_id,
            "manager": e.manager.full_name if e.manager else None,
            "employment_type": e.employment_type,
            "date_of_exit": _iso(e.date_of_exit),
            "date_of_birth": _iso(e.date_of_birth),
            "gender": e.gender,
            "address": e.address,
            "emergency_contact": e.emergency_contact,
            "pan": e.pan if sensitive else mask(e.pan),
            "bank_account": e.bank_account if sensitive else mask(e.bank_account),
            "bank_ifsc": e.bank_ifsc,
            "monthly_gross": e.monthly_gross,
            "monthly_tds": e.monthly_tds,
            "pf_applicable": e.pf_applicable,
            "created_at": _iso(e.created_at),
            "updated_at": _iso(e.updated_at),
        }
    )
    return out


def leave_out(lv: LeaveRequest) -> dict:
    return {
        "id": lv.id,
        "employee_id": lv.employee_id,
        "employee_name": lv.employee.full_name if lv.employee else None,
        "employee_code": lv.employee.employee_code if lv.employee else None,
        "leave_type": lv.leave_type,
        "start_date": _iso(lv.start_date),
        "end_date": _iso(lv.end_date),
        "days": lv.days,
        "reason": lv.reason,
        "status": lv.status,
        "created_at": _iso(lv.created_at),
        "reviewed_by": lv.reviewed_by.name if lv.reviewed_by else None,
        "reviewed_at": _iso(lv.reviewed_at),
        "review_note": lv.review_note,
    }


def attendance_out(a: Attendance) -> dict:
    return {
        "id": a.id,
        "employee_id": a.employee_id,
        "date": _iso(a.date),
        "status": a.status,
        "check_in": _iso(a.check_in),
        "check_out": _iso(a.check_out),
        "note": a.note,
    }


def payslip_out(p: Payslip) -> dict:
    e = p.employee
    return {
        "id": p.id,
        "period": p.period,
        "employee": {
            "id": e.id,
            "employee_code": e.employee_code,
            "full_name": e.full_name,
            "designation": e.designation,
            "department": e.department.name if e.department else None,
            "date_of_joining": _iso(e.date_of_joining),
            "pan": mask(e.pan),
            "bank_account": mask(e.bank_account),
        },
        "working_days": p.working_days,
        "lop_days": p.lop_days,
        "gross": p.gross,
        "basic": p.basic,
        "hra": p.hra,
        "special_allowance": p.special_allowance,
        "lop_deduction": p.lop_deduction,
        "pf": p.pf,
        "tds": p.tds,
        "total_deductions": p.lop_deduction + p.pf + p.tds,
        "net_pay": p.net_pay,
        "status": p.status,
        "generated_at": _iso(p.generated_at),
        "paid_at": _iso(p.paid_at),
    }


def announcement_out(a: Announcement) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "body": a.body,
        "pinned": a.pinned,
        "author": a.created_by.name if a.created_by else "HR",
        "created_at": _iso(a.created_at),
    }


def enquiry_out(m: ContactMessage) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "email": m.email,
        "phone": m.phone,
        "service": m.service,
        "message": m.message,
        "status": m.status,
        "received_at": _iso(m.received_at),
    }
