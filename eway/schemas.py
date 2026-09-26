"""Request bodies (validated by Pydantic before any code touches the database)."""
import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")
PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

RoleName = Literal["admin", "hr", "employee", "client"]
EmploymentType = Literal["full_time", "part_time", "contract", "intern"]
EmployeeStatus = Literal["active", "probation", "notice", "exited"]
LeaveType = Literal["casual", "sick", "earned", "unpaid"]
AttendanceStatus = Literal["present", "wfh", "half_day", "absent", "leave"]
EnquiryStatus = Literal["new", "read", "replied", "archived"]


def _email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError("Please provide a valid email address.")
    return v


def _blank_to_none(v):
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        return _email(v)

    @field_validator("name")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# ---------------------------------------------------------------------------
# Contact form
# ---------------------------------------------------------------------------
class ContactMessageIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    service: str | None = Field(default=None, max_length=120)
    message: str = Field(min_length=10, max_length=4000)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        return _email(v)

    @field_validator("name", "message")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class EnquiryUpdate(BaseModel):
    status: EnquiryStatus


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
class UserUpdate(BaseModel):
    role: RoleName | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# HR — departments & employees
# ---------------------------------------------------------------------------
class DepartmentIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("description", mode="before")
    @classmethod
    def _blank(cls, v):
        return _blank_to_none(v)


class EmployeeBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    designation: str = Field(min_length=2, max_length=120)
    department_id: int | None = None
    manager_id: int | None = None
    employment_type: EmploymentType = "full_time"
    status: EmployeeStatus = "active"
    date_of_joining: date
    date_of_exit: date | None = None
    date_of_birth: date | None = None
    gender: Literal["male", "female", "other"] | None = None
    address: str | None = Field(default=None, max_length=500)
    pan: str | None = Field(default=None, max_length=10)
    emergency_contact: str | None = Field(default=None, max_length=200)
    monthly_gross: int = Field(default=0, ge=0, le=10_000_000)
    monthly_tds: int = Field(default=0, ge=0, le=10_000_000)
    pf_applicable: bool = True
    bank_account: str | None = Field(default=None, max_length=40)
    bank_ifsc: str | None = Field(default=None, max_length=15)

    @field_validator(
        "phone", "address", "pan", "emergency_contact", "bank_account", "bank_ifsc",
        "gender", "date_of_birth", "date_of_exit", "department_id", "manager_id",
        mode="before",
    )
    @classmethod
    def _blanks(cls, v):
        return _blank_to_none(v)

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str) -> str:
        return _email(v)

    @field_validator("full_name", "designation")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("pan")
    @classmethod
    def _valid_pan(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper()
        if not PAN_RE.match(v):
            raise ValueError("PAN must look like ABCDE1234F.")
        return v

    @field_validator("bank_ifsc")
    @classmethod
    def _valid_ifsc(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper()
        if not IFSC_RE.match(v):
            raise ValueError("IFSC must look like SBIN0001234.")
        return v

    @model_validator(mode="after")
    def _dates(self):
        if self.date_of_exit and self.date_of_exit < self.date_of_joining:
            raise ValueError("Exit date can't be before the joining date.")
        return self


class EmployeeCreate(EmployeeBase):
    create_login: bool = Field(default=True, description="Also create a portal login")


class EmployeeUpdate(EmployeeBase):
    pass


# ---------------------------------------------------------------------------
# HR — leave, attendance, payroll, announcements
# ---------------------------------------------------------------------------
class LeaveApply(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def _range(self):
        if self.end_date < self.start_date:
            raise ValueError("End date can't be before the start date.")
        if (self.end_date - self.start_date).days > 90:
            raise ValueError("A single request can cover at most 90 days.")
        return self


class LeaveReview(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class AttendanceMark(BaseModel):
    employee_id: int
    date: date
    status: AttendanceStatus
    note: str | None = Field(default=None, max_length=255)


class PayrollRun(BaseModel):
    period: str = Field(description="Month in YYYY-MM format")

    @field_validator("period")
    @classmethod
    def _valid_period(cls, v: str) -> str:
        if not PERIOD_RE.match(v):
            raise ValueError("Period must be in YYYY-MM format.")
        return v


class AnnouncementIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=3, max_length=5000)
    pinned: bool = False
