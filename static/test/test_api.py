from datetime import date, timedelta

from eway.models import Employee
from eway.services import compute_payslip, working_days_between


# --------------------------------------------------------------------------- public
def test_health_reports_database(anon):
    r = anon.get("/api/health")
    assert r.status_code == 200
    assert r.json()["database"]["status"] == "ok"


def test_public_pages_and_company(anon):
    assert anon.get("/api/company").json()["cin"] == "U74900UP2009PTC037001"
    assert anon.get("/hr").status_code == 200
    assert "HR Portal" in anon.get("/hr/employees").text


def test_contact_saved_and_visible_to_admin(anon, admin):
    r = anon.post("/api/contact", json={"name": "Test Person", "email": "t@example.com",
                                         "message": "Please call me about GST."})
    assert r.status_code == 201
    items = admin.get("/api/admin/enquiries").json()["items"]
    assert any(i["email"] == "t@example.com" for i in items)


# --------------------------------------------------------------------------- auth / roles
def test_signup_is_client_and_blocked_from_hr(anon):
    r = anon.post("/api/auth/signup", json={"name": "Client One", "email": "client1@x.in", "password": "password1"})
    assert r.status_code == 201
    assert r.json()["user"]["role"] == "client"
    assert r.json()["redirect"] == "/"
    assert anon.get("/api/hr/dashboard").status_code == 403
    assert anon.get("/api/hr/employees").status_code == 403


def test_anonymous_gets_401(anon):
    assert anon.get("/api/hr/dashboard").status_code == 401


def test_admin_redirects_to_portal(anon):
    r = anon.post("/api/auth/login", json={"email": "admin@test.in", "password": "Admin@12345"})
    assert r.json()["redirect"] == "/hr"


def test_wrong_password(anon):
    r = anon.post("/api/auth/login", json={"email": "admin@test.in", "password": "nope"})
    assert r.status_code == 401


# --------------------------------------------------------------------------- HR flow
def _employee_payload(**kw):
    base = {
        "full_name": "Rahul Test", "email": "rahul@test.in", "designation": "Tax Associate",
        "date_of_joining": "2024-04-01", "monthly_gross": 30000, "pan": "abcpr1234k",
    }
    base.update(kw)
    return base


def test_full_hr_flow(admin, make_client):
    # department
    d = admin.post("/api/hr/departments", json={"name": "Taxation"})
    assert d.status_code == 201
    dept_id = d.json()["id"]
    assert admin.post("/api/hr/departments", json={"name": "taxation"}).status_code == 409

    # employee + login
    r = admin.post("/api/hr/employees", json=_employee_payload(department_id=dept_id))
    assert r.status_code == 201, r.text
    body = r.json()
    emp = body["employee"]
    assert emp["employee_code"].startswith("EW-")
    assert emp["pan"] == "ABCPR1234K"
    temp = body["login"]["temp_password"]
    assert temp

    # duplicate email rejected
    assert admin.post("/api/hr/employees", json=_employee_payload()).status_code == 409

    # employee logs in and lands on portal
    e = make_client()
    r = e.post("/api/auth/login", json={"email": "rahul@test.in", "password": temp})
    assert r.status_code == 200 and r.json()["redirect"] == "/hr"
    assert e.get("/api/hr/employees").status_code == 403  # not a manager
    assert e.get("/api/hr/me").json()["employee"]["employee_code"] == emp["employee_code"]

    # check in / out
    assert e.post("/api/hr/attendance/check-in").status_code == 200
    assert e.post("/api/hr/attendance/check-in").status_code == 409
    assert e.post("/api/hr/attendance/check-out").status_code == 200

    # leave: apply, over-quota rejected, approve
    start = date.today() + timedelta(days=10)
    while start.weekday() == 6:
        start += timedelta(days=1)
    r = e.post("/api/hr/leave", json={"leave_type": "casual", "start_date": str(start),
                                      "end_date": str(start), "reason": "Personal work"})
    assert r.status_code == 201, r.text
    leave_id = r.json()["id"]
    assert e.post("/api/hr/leave", json={"leave_type": "casual", "start_date": str(start),
                                         "end_date": str(start), "reason": "dup"}).status_code == 409
    far = start + timedelta(days=30)
    r = e.post("/api/hr/leave", json={"leave_type": "sick", "start_date": str(far),
                                      "end_date": str(far + timedelta(days=40)), "reason": "Too long"})
    assert r.status_code == 422
    r = admin.post(f"/api/hr/leave/{leave_id}/approve", json={"note": "Enjoy"})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    bal = {b["type"]: b for b in e.get("/api/hr/leave/mine").json()["balances"]}
    assert bal["casual"]["used"] == 1

    # payroll
    period = date.today().strftime("%Y-%m")
    r = admin.post("/api/hr/payroll/run", json={"period": period})
    assert r.status_code == 200 and r.json()["created"] >= 1
    slips = admin.get(f"/api/hr/payroll?period={period}").json()
    slip = next(s for s in slips["items"] if s["employee"]["id"] == emp["id"])
    assert slip["net_pay"] > 0
    assert e.get("/api/hr/payslips/mine").json() == []  # drafts aren't visible
    assert e.get(f"/api/hr/payslips/{slip['id']}").status_code == 404
    admin.post(f"/api/hr/payroll/{slip['id']}/pay")
    assert len(e.get("/api/hr/payslips/mine").json()) == 1

    # dashboard
    dash = admin.get("/api/hr/dashboard").json()
    assert dash["org"]["headcount"] >= 1
    assert e.get("/api/hr/dashboard").json()["me"]["employee"]["id"] == emp["id"]

    # csv export
    r = admin.get("/api/hr/employees/export.csv")
    assert r.status_code == 200 and "rahul@test.in" in r.text

    # exit → login disabled
    upd = _employee_payload(department_id=dept_id, status="exited")
    assert admin.patch(f"/api/hr/employees/{emp['id']}", json=upd).status_code == 200
    assert e.get("/api/hr/me").status_code == 401


def test_admin_role_management(admin, make_client):
    c = make_client()
    c.post("/api/auth/signup", json={"name": "Future HR", "email": "futurehr@x.in", "password": "password1"})
    users = admin.get("/api/admin/users?q=futurehr").json()
    uid = users[0]["id"]
    assert admin.patch(f"/api/admin/users/{uid}", json={"role": "hr"}).json()["role"] == "hr"
    assert c.get("/api/hr/employees").status_code == 200
    me = admin.get("/api/auth/me").json()["user"]
    assert admin.patch(f"/api/admin/users/{me['id']}", json={"role": "client"}).status_code == 400


# --------------------------------------------------------------------------- payroll maths
def test_payslip_calculation():
    e = Employee(monthly_gross=30000, monthly_tds=1000, pf_applicable=True,
                 date_of_joining=date(2020, 1, 1), date_of_exit=None)
    s = compute_payslip(e, "2026-09", lop_days=0)
    assert s["basic"] == 15000 and s["hra"] == 6000 and s["special_allowance"] == 9000
    assert s["pf"] == 1800
    assert s["net_pay"] == 30000 - 1800 - 1000
    wd = working_days_between(date(2026, 9, 1), date(2026, 9, 30))
    s2 = compute_payslip(e, "2026-09", lop_days=2)
    assert s2["lop_deduction"] == round(30000 * 2 / wd)


def test_payslip_prorated_for_mid_month_joiner():
    e = Employee(monthly_gross=26000, monthly_tds=0, pf_applicable=False,
                 date_of_joining=date(2026, 9, 16), date_of_exit=None)
    s = compute_payslip(e, "2026-09", lop_days=0)
    assert s["lop_days"] == working_days_between(date(2026, 9, 1), date(2026, 9, 15))
    assert 0 < s["net_pay"] < 26000