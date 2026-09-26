"""
Database tables (SQLAlchemy ORM models).

    users ─┬─< sessions
           └── employees ─┬─< leave_requests
                          ├─< attendance
                          └─< payslips
    departments ─< employees
    announcements, contact_messages
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from .database import Base


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC datetimes on every backend (SQLite drops tzinfo otherwise)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------
class Role:
    ADMIN = "admin"        # everything, incl. user & role management
    HR = "hr"              # HR management + enquiries
    EMPLOYEE = "employee"  # self-service portal
    CLIENT = "client"      # public website account (default on signup)

    ALL = (ADMIN, HR, EMPLOYEE, CLIENT)
    STAFF = (ADMIN, HR, EMPLOYEE)
    MANAGERS = (ADMIN, HR)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=Role.CLIENT, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    employee: Mapped["Employee | None"] = relationship(back_populates="user", uselist=False)
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class UserSession(Base):
    """Server-side login session. Only a SHA-256 hash of the cookie token is stored."""

    __tablename__ = "sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(64))

    user: Mapped[User] = relationship(back_populates="sessions")


# ---------------------------------------------------------------------------
# Website
# ---------------------------------------------------------------------------
class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    service: Mapped[str | None] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)  # new|read|replied|archived
    received_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)


# ---------------------------------------------------------------------------
# HR
# ---------------------------------------------------------------------------
class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True
    )
    full_name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    designation: Mapped[str] = mapped_column(String(120))
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), index=True
    )
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    employment_type: Mapped[str] = mapped_column(String(20), default="full_time")  # full_time|part_time|contract|intern
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)  # active|probation|notice|exited
    date_of_joining: Mapped[date] = mapped_column(Date)
    date_of_exit: Mapped[date | None] = mapped_column(Date)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    pan: Mapped[str | None] = mapped_column(String(10))
    emergency_contact: Mapped[str | None] = mapped_column(String(200))
    # Compensation (whole rupees)
    monthly_gross: Mapped[int] = mapped_column(Integer, default=0)
    monthly_tds: Mapped[int] = mapped_column(Integer, default=0)
    pf_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    bank_account: Mapped[str | None] = mapped_column(String(40))
    bank_ifsc: Mapped[str | None] = mapped_column(String(15))

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    user: Mapped[User | None] = relationship(back_populates="employee")
    department: Mapped[Department | None] = relationship(back_populates="employees")
    manager: Mapped["Employee | None"] = relationship(remote_side="Employee.id")
    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", passive_deletes=True
    )
    attendance: Mapped[list["Attendance"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", passive_deletes=True
    )
    payslips: Mapped[list["Payslip"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan", passive_deletes=True
    )


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    leave_type: Mapped[str] = mapped_column(String(20))  # casual|sick|earned|unpaid
    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date)
    days: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending|approved|rejected|cancelled
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    reviewed_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    review_note: Mapped[str | None] = mapped_column(Text)

    employee: Mapped[Employee] = relationship(back_populates="leave_requests")
    reviewed_by: Mapped[User | None] = relationship()


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(20), default="present")  # present|wfh|half_day|absent|leave
    check_in: Mapped[datetime | None] = mapped_column(UTCDateTime)
    check_out: Mapped[datetime | None] = mapped_column(UTCDateTime)
    note: Mapped[str | None] = mapped_column(String(255))

    employee: Mapped[Employee] = relationship(back_populates="attendance")


class Payslip(Base):
    __tablename__ = "payslips"
    __table_args__ = (UniqueConstraint("employee_id", "period", name="uq_payslip_employee_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)  # "YYYY-MM"
    working_days: Mapped[int] = mapped_column(Integer)
    lop_days: Mapped[int] = mapped_column(Integer, default=0)
    # Earnings (whole rupees)
    gross: Mapped[int] = mapped_column(Integer)
    basic: Mapped[int] = mapped_column(Integer)
    hra: Mapped[int] = mapped_column(Integer)
    special_allowance: Mapped[int] = mapped_column(Integer)
    # Deductions
    lop_deduction: Mapped[int] = mapped_column(Integer, default=0)
    pf: Mapped[int] = mapped_column(Integer, default=0)
    tds: Mapped[int] = mapped_column(Integer, default=0)
    net_pay: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft|paid
    generated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    employee: Mapped[Employee] = relationship(back_populates="payslips")


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

    created_by: Mapped[User | None] = relationship()
