/* ============================================================
   EWAY Financial — HR Portal (single-page app, vanilla JS)

   Routes (all under /hr):
     /                     dashboard            (all staff)
     /directory            staff directory      (all staff)
     /announcements        notices              (all staff; HR posts)
     /profile              my profile + password
     /leave                my leave             (employees)
     /attendance           my attendance        (employees)
     /payslips             my payslips          (employees)
     /payslips/:id         payslip document
     /employees[/:id]      employee records     (HR / admin)
     /leave-requests       approvals            (HR / admin)
     /attendance-register  daily register       (HR / admin)
     /payroll              payroll runs         (HR / admin)
     /departments          departments          (HR / admin)
     /enquiries            website enquiries    (HR / admin)
     /users                users & roles        (admin)
   ============================================================ */
"use strict";

/* ---------- tiny helpers ---------- */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const STAFF = ["admin", "hr", "employee"];
const MANAGERS = ["admin", "hr"];
const state = { user: null, counts: { pendingLeave: 0, newEnquiries: 0 } };
let clockTimer = null;

/* ---------- API ---------- */
async function api(path, { method = "GET", body } = {}) {
  const opts = { method, headers: { Accept: "application/json" }, credentials: "same-origin" };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  if (res.status === 401) {
    window.location.href = "/login?next=" + encodeURIComponent(location.pathname + location.search);
    throw new Error("Your session has expired. Please log in again.");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    const msg = Array.isArray(d)
      ? d.map((x) => String(x.msg || "").replace(/^Value error, /, "")).join(" ")
      : d || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

/* ---------- formatting ---------- */
const LABELS = {
  full_time: "Full-time", part_time: "Part-time", contract: "Contract", intern: "Intern",
  half_day: "Half day", wfh: "Work from home", casual: "Casual", sick: "Sick", earned: "Earned",
  unpaid: "Unpaid (LOP)", hr: "HR", admin: "Admin", employee: "Employee", client: "Client",
};
const label = (v) => (v == null || v === "" ? "—" : LABELS[v] || String(v).replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase()));
const TONES = {
  active: "green", approved: "green", paid: "green", present: "green", replied: "green", employee: "green",
  probation: "blue", wfh: "blue", new: "blue", leave: "blue", hr: "blue",
  pending: "amber", notice: "amber", draft: "amber", half_day: "amber",
  rejected: "red", absent: "red", admin: "dark",
};
const badge = (v, text) => `<span class="badge ${TONES[v] || ""}">${esc(text || label(v))}</span>`;
const inr = (n) => (n == null ? "—" : "₹" + Number(n).toLocaleString("en-IN"));
const parseDate = (iso) => new Date(iso.length === 10 ? iso + "T00:00:00" : iso);
const fmtDate = (iso) =>
  iso ? parseDate(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—";
const fmtShort = (iso) => (iso ? parseDate(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "—");
const fmtDay = (iso) => parseDate(iso).toLocaleDateString("en-IN", { weekday: "short" });
const fmtTime = (iso) =>
  iso ? new Date(iso).toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit", timeZone: "Asia/Kolkata" }) : "—";
const fmtDateTime = (iso) => (iso ? `${fmtDate(iso)}, ${fmtTime(iso)}` : "—");
const todayISO = () => new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
const currentPeriod = () => todayISO().slice(0, 7);
const periodLabel = (p) => {
  const [y, m] = p.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
};
const shiftDate = (iso, days) => {
  const d = parseDate(iso);
  d.setDate(d.getDate() + days);
  return d.toLocaleDateString("en-CA");
};
const shiftPeriod = (p, n) => {
  const [y, m] = p.split("-").map(Number);
  const d = new Date(y, m - 1 + n, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};
const hoursBetween = (a, b) => {
  if (!a || !b) return "—";
  const mins = Math.round((new Date(b) - new Date(a)) / 60000);
  return `${Math.floor(mins / 60)}h ${String(mins % 60).padStart(2, "0")}m`;
};
const workingDays = (start, end) => {
  if (!start || !end || end < start) return 0;
  let n = 0;
  for (let d = parseDate(start); d <= parseDate(end); d.setDate(d.getDate() + 1)) if (d.getDay() !== 0) n++;
  return n;
};
function initials(name) {
  const p = String(name || "?").trim().split(/\s+/);
  return ((p[0]?.[0] || "") + (p.length > 1 ? p[p.length - 1][0] : "")).toUpperCase();
}
function avatar(name, size = "") {
  let h = 0;
  for (const c of String(name)) h = (h * 31 + c.charCodeAt(0)) % 997;
  return `<span class="avatar ${size}" data-tone="${h % 6}" aria-hidden="true">${esc(initials(name))}</span>`;
}
function personCell(name, sub, size = "") {
  return `<div class="person">${avatar(name, size)}<div><div class="p-name">${esc(name)}</div>${sub ? `<div class="p-sub">${esc(sub)}</div>` : ""}</div></div>`;
}
function inrWords(num) {
  let n = Math.round(Number(num) || 0);
  if (n === 0) return "Zero";
  const ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
    "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"];
  const tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];
  const two = (x) => (x < 20 ? ones[x] : tens[Math.floor(x / 10)] + (x % 10 ? " " + ones[x % 10] : ""));
  const three = (x) =>
    (x >= 100 ? ones[Math.floor(x / 100)] + " Hundred" + (x % 100 ? " " : "") : "") + (x % 100 ? two(x % 100) : "");
  const parts = [];
  const crore = Math.floor(n / 1e7); n %= 1e7;
  const lakh = Math.floor(n / 1e5); n %= 1e5;
  const thousand = Math.floor(n / 1e3); n %= 1e3;
  if (crore) parts.push(three(crore) + " Crore");
  if (lakh) parts.push(two(lakh) + " Lakh");
  if (thousand) parts.push(two(thousand) + " Thousand");
  if (n) parts.push(three(n));
  return parts.join(" ");
}

/* ---------- icons ---------- */
const I = (d) =>
  `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
const ICONS = {
  grid: I('<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>'),
  users: I('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>'),
  megaphone: I('<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>'),
  user: I('<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a7 7 0 0 1 14 0v1"/>'),
  calendar: I('<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>'),
  clock: I('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
  wallet: I('<path d="M20 7H5a2 2 0 0 1 0-4h13v4"/><path d="M3 5v14a2 2 0 0 0 2 2h15V7"/><circle cx="16" cy="14" r="1.2"/>'),
  briefcase: I('<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>'),
  check: I('<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'),
  register: I('<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>'),
  building: I('<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4M8 6h.01M16 6h.01M12 6h.01M12 10h.01M12 14h.01M16 10h.01M16 14h.01M8 10h.01M8 14h.01"/>'),
  inbox: I('<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>'),
  shield: I('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'),
  logout: I('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>'),
  plus: I('<path d="M12 5v14M5 12h14"/>'),
  download: I('<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>'),
  search: I('<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>'),
  left: I('<path d="m15 18-6-6 6-6"/>'),
  right: I('<path d="m9 18 6-6-6-6"/>'),
  print: I('<path d="M6 9V2h12v7M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>'),
  back: I('<path d="M19 12H5M12 19l-7-7 7-7"/>'),
  play: I('<polygon points="6 4 20 12 6 20 6 4"/>'),
};

/* ---------- toast ---------- */
let toastTimer;
function toast(msg, isError = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.toggle("error", isError);
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), isError ? 5000 : 3200);
}

/* ---------- modal ---------- */
const modal = $("#modal");
let modalHandler = null;
let modalOnClose = null;

function openModal({ title, body, submitLabel = "Save", cancelLabel = "Cancel", closeLabel = "Done", wide = false, danger = false, onSubmit = null, onOpen = null, onClose = null }) {
  $("#modalTitle").textContent = title;
  $("#modalBody").innerHTML = body;
  $("#modalError").hidden = true;
  modal.classList.toggle("wide", wide);
  $("#modalFoot").innerHTML = onSubmit
    ? `<button type="button" class="btn" data-close>${esc(cancelLabel)}</button>
       <button type="submit" class="btn ${danger ? "btn-danger" : "btn-primary"}" id="modalSubmit">${esc(submitLabel)}</button>`
    : `<button type="button" class="btn btn-primary" data-close>${esc(closeLabel)}</button>`;
  modalHandler = onSubmit;
  modalOnClose = onClose;
  if (!modal.open) modal.showModal();
  const first = $("#modalBody input:not([type=hidden]), #modalBody select, #modalBody textarea");
  if (first) first.focus();
  if (onOpen) onOpen($("#modalBody"));
}
function closeModal() {
  if (modal.open) modal.close();
}
modal.addEventListener("close", () => {
  const cb = modalOnClose;
  modalOnClose = null;
  modalHandler = null;
  if (cb) cb();
});
modal.addEventListener("click", (e) => {
  if (e.target.closest("[data-close]") || e.target === modal) closeModal();
});
$("#modalForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!modalHandler) return closeModal();
  const btn = $("#modalSubmit");
  const errEl = $("#modalError");
  errEl.hidden = true;
  btn.disabled = true;
  try {
    const result = await modalHandler($("#modalForm"));
    if (result !== false && modal.open && modalHandler) closeModal();
  } catch (err) {
    errEl.textContent = err.message;
    errEl.hidden = false;
  } finally {
    if (btn.isConnected) btn.disabled = false;
  }
});

function confirmAction({ title, message, confirmLabel = "Confirm", danger = false }) {
  return new Promise((resolve) => {
    let ok = false;
    openModal({
      title,
      body: `<p>${message}</p>`,
      submitLabel: confirmLabel,
      danger,
      onSubmit: () => { ok = true; },
      onClose: () => resolve(ok),
    });
  });
}

function formValues(form) {
  const out = {};
  $$("[name]", form).forEach((el) => {
    if (el.type === "checkbox") out[el.name] = el.checked;
    else if (el.type === "number") out[el.name] = el.value === "" ? 0 : Number(el.value);
    else out[el.name] = el.value.trim();
  });
  return out;
}

/* ---------- field builders ---------- */
function field(name, lbl, { type = "text", value = "", required = false, full = false, help = "", attrs = "", placeholder = "" } = {}) {
  return `<div class="field ${full ? "full" : ""}">
    <label for="f_${name}">${esc(lbl)}${required ? "" : ' <span class="opt">(optional)</span>'}</label>
    <input class="input" id="f_${name}" name="${name}" type="${type}" value="${esc(value ?? "")}" ${required ? "required" : ""} placeholder="${esc(placeholder)}" ${attrs} />
    ${help ? `<p class="help">${help}</p>` : ""}
  </div>`;
}
function selectField(name, lbl, options, { value = "", required = false, full = false, empty = null } = {}) {
  const opts = (empty !== null ? `<option value="">${esc(empty)}</option>` : "") +
    options.map(([v, t]) => `<option value="${esc(v)}" ${String(v) === String(value ?? "") ? "selected" : ""}>${esc(t)}</option>`).join("");
  return `<div class="field ${full ? "full" : ""}">
    <label for="f_${name}">${esc(lbl)}${required || empty === null ? "" : ' <span class="opt">(optional)</span>'}</label>
    <select class="select" id="f_${name}" name="${name}">${opts}</select>
  </div>`;
}
function textareaField(name, lbl, { value = "", required = false, full = true, placeholder = "", rows = 4 } = {}) {
  return `<div class="field ${full ? "full" : ""}">
    <label for="f_${name}">${esc(lbl)}${required ? "" : ' <span class="opt">(optional)</span>'}</label>
    <textarea class="textarea" id="f_${name}" name="${name}" rows="${rows}" placeholder="${esc(placeholder)}" ${required ? "required" : ""}>${esc(value ?? "")}</textarea>
  </div>`;
}

/* ---------- navigation ---------- */
function navSections() {
  const u = state.user;
  const isMgr = MANAGERS.includes(u.role);
  const hasEmp = !!u.employee;
  return [
    { title: "Overview", items: [
      { path: "", label: "Dashboard", icon: "grid" },
      { path: "directory", label: "Directory", icon: "users" },
      { path: "announcements", label: "Announcements", icon: "megaphone" },
    ] },
    { title: "My Workspace", items: [
      { path: "profile", label: "My Profile", icon: "user" },
      hasEmp && { path: "leave", label: "My Leave", icon: "calendar" },
      hasEmp && { path: "attendance", label: "My Attendance", icon: "clock" },
      hasEmp && { path: "payslips", label: "My Payslips", icon: "wallet" },
    ].filter(Boolean) },
    isMgr && { title: "HR Management", items: [
      { path: "employees", label: "Employees", icon: "briefcase" },
      { path: "leave-requests", label: "Leave Approvals", icon: "check", count: state.counts.pendingLeave },
      { path: "attendance-register", label: "Attendance Register", icon: "register" },
      { path: "payroll", label: "Payroll", icon: "wallet" },
      { path: "departments", label: "Departments", icon: "building" },
    ] },
    isMgr && { title: "Administration", items: [
      { path: "enquiries", label: "Website Enquiries", icon: "inbox", count: state.counts.newEnquiries },
      u.role === "admin" && { path: "users", label: "Users & Roles", icon: "shield" },
    ].filter(Boolean) },
  ].filter(Boolean);
}

function renderNav() {
  const path = currentPath();
  const top = path.split("/")[0];
  $("#sbNav").innerHTML = navSections()
    .map((s) => `<div class="sb-section"><h3>${esc(s.title)}</h3>${s.items
      .map((it) => {
        const active = it.path === top;
        return `<a href="/hr${it.path ? "/" + it.path : ""}" class="sb-link ${active ? "active" : ""}" data-link ${active ? 'aria-current="page"' : ""}>
          ${ICONS[it.icon]}<span>${esc(it.label)}</span>${it.count ? `<span class="sb-count">${it.count}</span>` : ""}</a>`;
      })
      .join("")}</div>`)
    .join("");
}

function renderTopUser() {
  const u = state.user;
  $("#topUser").innerHTML = `
    <a href="/hr/profile" class="user-pill" data-link title="${esc(u.email)}">
      ${avatar(u.name, "sm")}
      <span class="who"><strong>${esc(u.name)}</strong><small>${esc(label(u.role))}${u.employee ? " · " + esc(u.employee.employee_code) : ""}</small></span>
    </a>
    <button class="icon-btn" id="logoutBtn" title="Log out" aria-label="Log out">${ICONS.logout}</button>`;
  $("#logoutBtn").onclick = async () => {
    try { await fetch("/api/auth/logout", { method: "POST" }); } catch { /* ignore */ }
    window.location.href = "/login";
  };
}

async function refreshCounts() {
  if (!MANAGERS.includes(state.user.role)) return;
  try {
    const d = await api("/api/hr/dashboard");
    state.counts = { pendingLeave: d.org.pending_leave_count, newEnquiries: d.org.new_enquiries };
    renderNav();
  } catch { /* non-critical */ }
}

/* ---------- router ---------- */
const ROUTES = [
  { re: /^$/, view: viewDashboard, title: "Dashboard" },
  { re: /^directory$/, view: viewDirectory, title: "Directory" },
  { re: /^announcements$/, view: viewAnnouncements, title: "Announcements" },
  { re: /^profile$/, view: viewProfile, title: "My Profile" },
  { re: /^leave$/, view: viewMyLeave, title: "My Leave", employee: true },
  { re: /^attendance$/, view: viewMyAttendance, title: "My Attendance", employee: true },
  { re: /^payslips$/, view: viewMyPayslips, title: "My Payslips", employee: true },
  { re: /^payslips\/(\d+)$/, view: viewPayslip, title: "Payslip" },
  { re: /^employees$/, view: viewEmployees, title: "Employees", roles: MANAGERS },
  { re: /^employees\/(\d+)$/, view: viewEmployee, title: "Employee", roles: MANAGERS },
  { re: /^leave-requests$/, view: viewLeaveApprovals, title: "Leave Approvals", roles: MANAGERS },
  { re: /^attendance-register$/, view: viewRegister, title: "Attendance Register", roles: MANAGERS },
  { re: /^payroll$/, view: viewPayroll, title: "Payroll", roles: MANAGERS },
  { re: /^departments$/, view: viewDepartments, title: "Departments", roles: MANAGERS },
  { re: /^enquiries$/, view: viewEnquiries, title: "Website Enquiries", roles: MANAGERS },
  { re: /^users$/, view: viewUsers, title: "Users & Roles", roles: ["admin"] },
];

const currentPath = () => location.pathname.replace(/^\/hr\/?/, "").replace(/\/+$/, "");
const qs = () => new URLSearchParams(location.search);

function navigate(path, { replace = false } = {}) {
  const url = "/hr" + (path ? "/" + path.replace(/^\//, "") : "");
  history[replace ? "replaceState" : "pushState"]({}, "", url);
  render();
}

let renderToken = 0;
async function render() {
  const token = ++renderToken;
  clearInterval(clockTimer);
  document.body.classList.remove("nav-open");
  const path = currentPath();
  const view = $("#view");
  let match = null;
  const route = ROUTES.find((r) => (match = path.match(r.re)));
  renderNav();

  const ctx = {
    paint(html) {
      if (token !== renderToken) return false;
      view.innerHTML = html;
      return true;
    },
    get stale() { return token !== renderToken; },
  };

  if (!route) {
    setTitle("Not found");
    ctx.paint(emptyState("Page not found", "The page you're looking for doesn't exist.", `<a href="/hr" class="btn btn-primary" data-link>Go to dashboard</a>`));
    return;
  }
  setTitle(route.title);
  if (route.roles && !route.roles.includes(state.user.role)) {
    ctx.paint(emptyState("Restricted", "You don't have access to this section."));
    return;
  }
  if (route.employee && !state.user.employee) {
    ctx.paint(noProfileCard());
    return;
  }
  view.innerHTML = `<div class="card card-empty">Loading…</div>`;
  try {
    await route.view(ctx, ...match.slice(1));
  } catch (err) {
    ctx.paint(emptyState("Something went wrong", esc(err.message), `<button class="btn" onclick="location.reload()">Retry</button>`));
  }
  if (!ctx.stale) view.focus({ preventScroll: true });
}

function setTitle(title) {
  $("#pageTitle").textContent = title;
  document.title = `${title} — EWAY HR Portal`;
  window.scrollTo(0, 0);
}

function emptyState(title, text, action = "") {
  return `<div class="card card-pad" style="text-align:center;padding:48px 24px">
    <h2 style="font-size:1.2rem;margin-bottom:6px">${esc(title)}</h2>
    <p class="muted">${text}</p>${action ? `<div style="margin-top:18px">${action}</div>` : ""}</div>`;
}
function noProfileCard() {
  return emptyState(
    "No employee profile linked",
    "Your login isn't connected to an employee record yet, so self-service features (leave, attendance, payslips) aren't available. Please ask HR to add you as an employee using this email address."
  );
}

document.addEventListener("click", (e) => {
  const a = e.target.closest("a[data-link]");
  if (!a || e.metaKey || e.ctrlKey || e.shiftKey || a.target === "_blank") return;
  e.preventDefault();
  const url = new URL(a.href);
  history.pushState({}, "", url.pathname + url.search);
  render();
});
window.addEventListener("popstate", render);
$("#menuBtn").addEventListener("click", () => document.body.classList.toggle("nav-open"));
$("#sbScrim").addEventListener("click", () => document.body.classList.remove("nav-open"));

/* ============================================================
   Shared widgets
   ============================================================ */
function todayCard(att) {
  const cin = att?.check_in;
  const cout = att?.check_out;
  const btn = !cin
    ? `<button class="btn btn-primary btn-lg" data-act="check-in">${ICONS.play} Check in</button>`
    : !cout
      ? `<button class="btn btn-lg" data-act="check-out">Check out</button>`
      : `<span class="badge green">Day complete · ${hoursBetween(cin, cout)}</span>`;
  const d = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", timeZone: "Asia/Kolkata" });
  return `<div class="card card-pad"><div class="today-card">
      <div><p class="crumb">${esc(d)}</p><div class="clock" data-clock>--:--</div></div>
      <div class="today-meta"><div class="today-times">
        <div><span>Check in</span><strong>${fmtTime(cin)}</strong></div>
        <div><span>Check out</span><strong>${fmtTime(cout)}</strong></div>
        <div><span>Status</span><strong>${att ? esc(label(att.status)) : "Not marked"}</strong></div>
      </div></div>
      <div>${btn}</div>
    </div></div>`;
}
function bindTodayCard(root, onDone) {
  const tick = () => {
    const el = $("[data-clock]", root);
    if (el) el.textContent = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "Asia/Kolkata" });
  };
  tick();
  clearInterval(clockTimer);
  clockTimer = setInterval(tick, 1000);
  $$("[data-act=check-in], [data-act=check-out]", root).forEach((b) => {
    b.onclick = async () => {
      b.disabled = true;
      try {
        const r = await api(`/api/hr/attendance/${b.dataset.act}`, { method: "POST" });
        toast(b.dataset.act === "check-in" ? `Checked in at ${fmtTime(r.check_in)}. Have a great day!` : `Checked out at ${fmtTime(r.check_out)}.`);
        onDone();
      } catch (err) {
        toast(err.message, true);
        b.disabled = false;
      }
    };
  });
}

function balancesHTML(bals) {
  return `<div class="balances">${bals
    .filter((b) => b.quota != null)
    .map((b) => {
      const pct = b.quota ? Math.min(100, ((b.used + b.pending) / b.quota) * 100) : 0;
      return `<div class="balance"><div class="label">${esc(label(b.type))} leave</div>
        <div class="value">${b.available}<small> of ${b.quota} left</small></div>
        <div class="meter"><span style="width:${pct}%"></span></div>
        <div class="foot">${b.used} used${b.pending ? ` · ${b.pending} pending` : ""}</div></div>`;
    })
    .join("")}</div>`;
}

function leaveTable(items, { showEmployee = false, actions = null } = {}) {
  if (!items.length) return `<div class="card-empty">No leave requests here.</div>`;
  return `<div class="table-wrap"><table class="table"><thead><tr>
      ${showEmployee ? "<th>Employee</th>" : ""}<th>Type</th><th>Dates</th><th class="num">Days</th><th>Reason</th><th>Status</th>${actions ? "<th></th>" : ""}
    </tr></thead><tbody>${items
      .map((lv) => `<tr>
        ${showEmployee ? `<td>${personCell(lv.employee_name, lv.employee_code, "sm")}</td>` : ""}
        <td class="nowrap">${esc(label(lv.leave_type))}</td>
        <td class="nowrap">${fmtShort(lv.start_date)}${lv.end_date !== lv.start_date ? " – " + fmtDate(lv.end_date) : ", " + parseDate(lv.start_date).getFullYear()}</td>
        <td class="num">${lv.days}</td>
        <td><div class="truncate" title="${esc(lv.reason)}">${esc(lv.reason)}</div>${lv.review_note ? `<div class="p-sub muted" style="font-size:.78rem">“${esc(lv.review_note)}” — ${esc(lv.reviewed_by || "HR")}</div>` : ""}</td>
        <td>${badge(lv.status)}</td>
        ${actions ? `<td class="nowrap" style="text-align:right">${actions(lv)}</td>` : ""}
      </tr>`)
      .join("")}</tbody></table></div>`;
}

function reviewLeave(lv, decision, after) {
  const approve = decision === "approve";
  openModal({
    title: approve ? "Approve leave" : "Reject leave",
    body: `<p style="margin-bottom:14px"><strong>${esc(lv.employee_name)}</strong> · ${esc(label(lv.leave_type))} leave · ${lv.days} day(s)<br>
      <span class="muted">${fmtDate(lv.start_date)} – ${fmtDate(lv.end_date)} — “${esc(lv.reason)}”</span></p>
      ${textareaField("note", approve ? "Note to employee" : "Reason for rejection", { rows: 3, placeholder: approve ? "e.g. Approved — please hand over pending filings." : "e.g. Critical filing deadline that week." })}`,
    submitLabel: approve ? "Approve" : "Reject",
    danger: !approve,
    onSubmit: async (form) => {
      const note = form.note.value.trim() || null;
      await api(`/api/hr/leave/${lv.id}/${decision}`, { method: "POST", body: { note } });
      toast(approve ? "Leave approved." : "Leave rejected.");
      refreshCounts();
      after();
    },
  });
}

/* ============================================================
   Dashboard
   ============================================================ */
async function viewDashboard(ctx) {
  const d = await api("/api/hr/dashboard");
  if (d.org) {
    state.counts = { pendingLeave: d.org.pending_leave_count, newEnquiries: d.org.new_enquiries };
    renderNav();
  }
  const first = state.user.name.trim().split(/\s+/)[0];
  const hour = Number(new Date().toLocaleString("en-IN", { hour: "numeric", hour12: false, timeZone: "Asia/Kolkata" }));
  const greet = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const longDate = parseDate(d.today).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  const isMgr = !!d.org;

  let html = `<div class="welcome"><div><h2>${greet}, ${esc(first)}</h2><p>${esc(longDate)}</p></div>
    <div class="actions">
      ${d.me ? `<a href="/hr/leave?apply=1" class="btn" data-link>${ICONS.calendar} Apply for leave</a>` : ""}
      ${isMgr ? `<a href="/hr/employees?add=1" class="btn btn-primary" data-link>${ICONS.plus} Add employee</a>` : ""}
    </div></div>`;

  if (isMgr) {
    const o = d.org;
    html += `<div class="stats">
      <a href="/hr/employees" class="stat dark" data-link><div class="label">Headcount</div><div class="value">${o.headcount}</div><div class="hint">${o.status_counts.probation || 0} on probation · ${o.status_counts.notice || 0} on notice</div></a>
      <a href="/hr/attendance-register" class="stat" data-link><div class="label">Present today</div><div class="value">${o.present_today}<span class="muted" style="font-size:1rem;font-weight:600"> / ${o.headcount}</span></div><div class="hint">Checked in or marked</div></a>
      <div class="stat"><div class="label">On leave today</div><div class="value">${o.on_leave_today.length}</div><div class="hint">Approved leave</div></div>
      <a href="/hr/leave-requests" class="stat" data-link><div class="label">Pending approvals</div><div class="value">${o.pending_leave_count}</div><div class="hint">Leave requests</div></a>
      <a href="/hr/enquiries" class="stat" data-link><div class="label">New enquiries</div><div class="value">${o.new_enquiries}</div><div class="hint">From the website</div></a>
      <a href="/hr/payroll" class="stat" data-link><div class="label">Monthly payroll</div><div class="value" style="font-size:1.45rem">${inr(o.monthly_payroll)}</div><div class="hint">Gross, current staff</div></a>
    </div>`;
  }

  const left = [];
  const right = [];

  if (d.me) {
    left.push(`<div id="todayWrap">${todayCard(d.me.attendance_today)}</div>`);
    left.push(`<div class="card"><div class="card-head"><h3>My leave balance · ${parseDate(d.today).getFullYear()}</h3><a href="/hr/leave" class="btn btn-sm" data-link>View all</a></div>
      <div class="card-body">${balancesHTML(d.me.leave_balances)}</div></div>`);
  } else if (!isMgr) {
    left.push(noProfileCard());
  }

  if (isMgr) {
    const o = d.org;
    left.push(`<div class="card"><div class="card-head"><h3>Pending leave approvals</h3><a href="/hr/leave-requests" class="btn btn-sm" data-link>Open queue</a></div>
      ${o.pending_leave.length ? `<div class="list">${o.pending_leave
        .map((lv, i) => `<div class="list-item">${avatar(lv.employee_name, "sm")}
          <div class="grow"><div class="title">${esc(lv.employee_name)} <span class="muted" style="font-weight:500">· ${esc(label(lv.leave_type))}, ${lv.days} day${lv.days > 1 ? "s" : ""}</span></div>
          <div class="sub">${fmtShort(lv.start_date)}${lv.end_date !== lv.start_date ? " – " + fmtShort(lv.end_date) : ""} · ${esc(lv.reason)}</div></div>
          ${lv.employee_id === state.user.employee?.id ? `<span class="badge amber">Yours</span>` : `<button class="btn btn-sm btn-success" data-review="approve" data-i="${i}">Approve</button>
          <button class="btn btn-sm btn-danger" data-review="reject" data-i="${i}">Reject</button>`}</div>`)
        .join("")}</div>` : `<div class="card-empty">All caught up — no pending requests.</div>`}</div>`);

    left.push(`<div class="card"><div class="card-head"><h3>Who's out today</h3></div>
      ${o.on_leave_today.length ? `<div class="list">${o.on_leave_today
        .map((x) => `<div class="list-item">${avatar(x.employee_name, "sm")}<div class="grow"><div class="title">${esc(x.employee_name)}</div><div class="sub">${esc(label(x.leave_type))} leave · back after ${fmtShort(x.end_date)}</div></div></div>`)
        .join("")}</div>` : `<div class="card-empty">Everyone's in today.</div>`}</div>`);
  }

  right.push(`<div class="card"><div class="card-head"><h3>Announcements</h3><a href="/hr/announcements" class="btn btn-sm" data-link>All</a></div>
    ${d.announcements.length ? d.announcements.slice(0, 3).map(announcementHTML).join("") : `<div class="card-empty">No announcements yet.</div>`}</div>`);

  if (d.me?.latest_payslip) {
    const p = d.me.latest_payslip;
    right.push(`<a href="/hr/payslips/${p.id}" class="card card-pad" data-link style="display:block">
      <p class="crumb">Latest payslip · ${esc(periodLabel(p.period))}</p>
      <div style="display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin-top:6px">
        <strong style="font-size:1.6rem;letter-spacing:-.02em">${inr(p.net_pay)}</strong>${badge(p.status)}</div>
      <p class="muted" style="font-size:.82rem">Net pay · Gross ${inr(p.gross)}</p></a>`);
  }

  if (isMgr) {
    const o = d.org;
    const max = Math.max(1, ...o.departments.map((x) => x.count));
    right.push(`<div class="card"><div class="card-head"><h3>Team by department</h3><a href="/hr/departments" class="btn btn-sm" data-link>Manage</a></div>
      <div class="card-body">${o.departments.length ? `<div class="bars">${o.departments
        .map((x) => `<div class="bar-row"><span class="truncate">${esc(x.name)}</span><div class="track"><span style="width:${(x.count / max) * 100}%"></span></div><span class="n">${x.count}</span></div>`)
        .join("")}</div>` : `<p class="muted">No employees yet.</p>`}</div></div>`);

    right.push(`<div class="card"><div class="card-head"><h3>Upcoming birthdays</h3><span class="sub">Next 30 days</span></div>
      ${o.upcoming_birthdays.length ? `<div class="list">${o.upcoming_birthdays
        .map((b) => `<div class="list-item">${avatar(b.full_name, "sm")}<div class="grow"><div class="title">${esc(b.full_name)}</div><div class="sub">${fmtShort(b.date)}</div></div>
          <span class="badge plain">${b.in_days === 0 ? "Today 🎉" : b.in_days === 1 ? "Tomorrow" : `in ${b.in_days} days`}</span></div>`)
        .join("")}</div>` : `<div class="card-empty">No birthdays coming up.</div>`}</div>`);

    if (o.recent_joiners.length) {
      right.push(`<div class="card"><div class="card-head"><h3>Recent joiners</h3></div><div class="list">${o.recent_joiners
        .map((e) => `<a href="/hr/employees/${e.id}" class="list-item" data-link>${avatar(e.full_name, "sm")}<div class="grow"><div class="title">${esc(e.full_name)}</div><div class="sub">${esc(e.designation)} · joined ${fmtDate(e.date_of_joining)}</div></div></a>`)
        .join("")}</div></div>`);
    }
  }

  html += left.length
    ? `<div class="grid grid-main"><div class="stack">${left.join("")}</div><div class="stack">${right.join("")}</div></div>`
    : `<div class="grid grid-2">${right.join("")}</div>`;

  if (!ctx.paint(html)) return;
  const view = $("#view");
  if (d.me) bindTodayCard(view, () => render());
  $$("[data-review]", view).forEach((b) => {
    b.onclick = () => reviewLeave(d.org.pending_leave[+b.dataset.i], b.dataset.review, () => render());
  });
}

function announcementHTML(a, canDelete = false) {
  return `<div class="announcement">
    <h4>${a.pinned ? `<span class="badge dark plain">Pinned</span>` : ""}${esc(a.title)}</h4>
    <p>${esc(a.body)}</p>
    <div class="meta"><span>${esc(a.author)} · ${fmtDate(a.created_at)}</span>
      ${canDelete ? `<button class="btn btn-sm btn-ghost btn-danger" data-del-ann="${a.id}">Delete</button>` : ""}</div>
  </div>`;
}

/* ============================================================
   Directory
   ============================================================ */
async function viewDirectory(ctx) {
  const people = await api("/api/hr/directory");
  const html = `<div class="page-intro"><div><h2>Staff directory</h2><p>${people.length} colleagues at EWAY Financial</p></div>
      <div class="search">${ICONS.search}<input class="input" id="dirSearch" type="search" placeholder="Search name, role or department…" /></div></div>
    <div class="people" id="people"></div>`;
  if (!ctx.paint(html)) return;
  const draw = (q = "") => {
    const t = q.toLowerCase();
    const list = people.filter((p) => !t || [p.full_name, p.designation, p.department, p.email].join(" ").toLowerCase().includes(t));
    $("#people").innerHTML = list.length
      ? list.map((p) => `<div class="person-card">${avatar(p.full_name, "lg")}
          <h3>${esc(p.full_name)}</h3><p class="role">${esc(p.designation)}</p>
          ${p.department ? `<p style="margin-top:8px"><span class="badge plain">${esc(p.department)}</span></p>` : ""}
          <div class="contact"><a href="mailto:${esc(p.email)}">${esc(p.email)}</a>${p.phone ? `<a href="tel:${esc(p.phone.replace(/\s/g, ""))}">${esc(p.phone)}</a>` : ""}</div></div>`).join("")
      : `<div class="card card-empty" style="grid-column:1/-1">No one matches “${esc(q)}”.</div>`;
  };
  draw();
  $("#dirSearch").addEventListener("input", (e) => draw(e.target.value));
}

/* ============================================================
   Announcements
   ============================================================ */
async function viewAnnouncements(ctx) {
  const items = await api("/api/hr/announcements");
  const isMgr = MANAGERS.includes(state.user.role);
  const html = `<div class="page-intro"><div><h2>Announcements</h2><p>Company notices and updates</p></div>
      ${isMgr ? `<button class="btn btn-primary" id="newAnn">${ICONS.plus} New announcement</button>` : ""}</div>
    <div class="card">${items.length ? items.map((a) => announcementHTML(a, isMgr)).join("") : `<div class="card-empty">No announcements yet.</div>`}</div>`;
  if (!ctx.paint(html)) return;
  $("#newAnn")?.addEventListener("click", () =>
    openModal({
      title: "New announcement",
      body: `<div class="form-grid">${field("title", "Title", { required: true, full: true, attrs: 'maxlength="200"' })}
        ${textareaField("body", "Message", { required: true, rows: 6 })}
        <label class="check full"><input type="checkbox" name="pinned" /> Pin to the top of everyone's dashboard</label></div>`,
      submitLabel: "Publish",
      onSubmit: async (form) => {
        await api("/api/hr/announcements", { method: "POST", body: formValues(form) });
        toast("Announcement published.");
        render();
      },
    })
  );
  $$("[data-del-ann]").forEach((b) => {
    b.onclick = async () => {
      if (!(await confirmAction({ title: "Delete announcement?", message: "This removes it for everyone.", confirmLabel: "Delete", danger: true }))) return;
      try {
        await api(`/api/hr/announcements/${b.dataset.delAnn}`, { method: "DELETE" });
        toast("Announcement deleted.");
        render();
      } catch (err) { toast(err.message, true); }
    };
  });
}

/* ============================================================
   Profile
   ============================================================ */
async function viewProfile(ctx) {
  const u = state.user;
  const profile = u.employee ? await api("/api/hr/me") : null;
  const e = profile?.employee;
  const html = `<div class="card card-pad" style="margin-bottom:20px"><div class="profile-head">${avatar(u.name, "lg")}
      <div class="grow"><h2>${esc(u.name)}</h2><div class="meta"><span>${esc(u.email)}</span>${badge(u.role)}${e ? `<span>${esc(e.employee_code)} · ${esc(e.designation)}</span>` : ""}</div></div></div></div>
    <div class="grid grid-main"><div class="stack">
      ${e ? `<div class="card"><div class="card-head"><h3>Employment details</h3><span class="sub">Contact HR to update</span></div><div class="card-body"><dl class="dl">
        <dt>Department</dt><dd>${esc(e.department || "—")}</dd>
        <dt>Reporting manager</dt><dd>${esc(e.manager || "—")}</dd>
        <dt>Employment type</dt><dd>${esc(label(e.employment_type))}</dd>
        <dt>Status</dt><dd>${badge(e.status)}</dd>
        <dt>Date of joining</dt><dd>${fmtDate(e.date_of_joining)}</dd>
        <dt>Phone</dt><dd>${esc(e.phone || "—")}</dd>
        <dt>Date of birth</dt><dd>${fmtDate(e.date_of_birth)}</dd>
        <dt>Address</dt><dd>${esc(e.address || "—")}</dd>
        <dt>Emergency contact</dt><dd>${esc(e.emergency_contact || "—")}</dd>
        <dt>PAN</dt><dd>${esc(e.pan || "—")}</dd>
        <dt>Bank account</dt><dd>${esc(e.bank_account || "—")}${e.bank_ifsc ? ` · ${esc(e.bank_ifsc)}` : ""}</dd>
      </dl></div></div>
      <div class="card"><div class="card-head"><h3>Leave balance</h3></div><div class="card-body">${balancesHTML(profile.leave_balances)}</div></div>`
      : `<div class="card"><div class="card-head"><h3>Account</h3></div><div class="card-body"><dl class="dl">
        <dt>Role</dt><dd>${esc(label(u.role))}</dd><dt>Member since</dt><dd>${fmtDate(u.created_at)}</dd><dt>Last login</dt><dd>${fmtDateTime(u.last_login_at)}</dd></dl></div></div>`}
    </div><div class="stack">
      <div class="card"><div class="card-head"><h3>Change password</h3></div>
        <form class="card-body" id="pwForm" novalidate><div class="form-grid" style="grid-template-columns:1fr">
          ${field("current_password", "Current password", { type: "password", required: true, attrs: 'autocomplete="current-password"' })}
          ${field("new_password", "New password", { type: "password", required: true, help: "At least 8 characters.", attrs: 'autocomplete="new-password" minlength="8"' })}
          ${field("confirm", "Confirm new password", { type: "password", required: true, attrs: 'autocomplete="new-password"' })}
        </div><div class="form-error" id="pwError" hidden style="margin:14px 0 0"></div>
        <button class="btn btn-primary" style="margin-top:16px" type="submit">Update password</button></form></div>
    </div></div>`;
  if (!ctx.paint(html)) return;
  $("#pwForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const f = ev.target;
    const err = $("#pwError");
    err.hidden = true;
    const v = formValues(f);
    const fail = (m) => { err.textContent = m; err.hidden = false; };
    if (v.new_password.length < 8) return fail("New password must be at least 8 characters.");
    if (v.new_password !== v.confirm) return fail("New passwords don't match.");
    const btn = $("button[type=submit]", f);
    btn.disabled = true;
    try {
      const r = await api("/api/auth/change-password", { method: "POST", body: { current_password: v.current_password, new_password: v.new_password } });
      toast(r.message);
      f.reset();
    } catch (e2) { fail(e2.message); } finally { btn.disabled = false; }
  });
}

/* ============================================================
   My leave
   ============================================================ */
async function viewMyLeave(ctx) {
  const data = await api("/api/hr/leave/mine");
  const html = `<div class="page-intro"><div><h2>My leave</h2><p>Balances for ${new Date().getFullYear()} · weekly off: Sunday</p></div>
      <button class="btn btn-primary" id="applyBtn">${ICONS.plus} Apply for leave</button></div>
    <div style="margin-bottom:20px">${balancesHTML(data.balances)}</div>
    <div class="card"><div class="card-head"><h3>My requests</h3><span class="sub">${data.items.length} total</span></div>
      ${leaveTable(data.items, {
        actions: (lv) => lv.status === "pending" || (lv.status === "approved" && lv.start_date > todayISO())
          ? `<button class="btn btn-sm btn-danger" data-cancel="${lv.id}">Cancel</button>` : "",
      })}</div>`;
  if (!ctx.paint(html)) return;

  const openApply = () => {
    const avail = Object.fromEntries(data.balances.map((b) => [b.type, b.available]));
    const opts = data.leave_types.map((t) => [t, avail[t] != null ? `${label(t)} — ${avail[t]} day(s) available` : label(t)]);
    const minDate = shiftDate(todayISO(), -30);
    openModal({
      title: "Apply for leave",
      body: `<div class="form-grid">
        ${selectField("leave_type", "Leave type", opts, { full: true })}
        ${field("start_date", "From", { type: "date", required: true, value: todayISO(), attrs: `min="${minDate}"` })}
        ${field("end_date", "To", { type: "date", required: true, value: todayISO(), attrs: `min="${minDate}"` })}
        <p class="full muted" id="daysHint" style="font-size:.85rem"></p>
        ${textareaField("reason", "Reason", { required: true, rows: 3, placeholder: "Briefly describe the reason" })}</div>`,
      submitLabel: "Submit request",
      onOpen: (body) => {
        const s = $("[name=start_date]", body), e = $("[name=end_date]", body), hint = $("#daysHint", body);
        const upd = () => {
          if (e.value < s.value) e.value = s.value;
          e.min = s.value;
          const n = workingDays(s.value, e.value);
          hint.textContent = n ? `${n} working day${n > 1 ? "s" : ""} (Sundays excluded)` : "The selected dates are all weekly offs.";
        };
        s.addEventListener("change", upd); e.addEventListener("change", upd); upd();
      },
      onSubmit: async (form) => {
        const v = formValues(form);
        if (v.reason.length < 3) throw new Error("Please add a short reason.");
        await api("/api/hr/leave", { method: "POST", body: v });
        toast("Leave request submitted to HR.");
        history.replaceState({}, "", "/hr/leave");
        render();
      },
    });
  };
  $("#applyBtn").onclick = openApply;
  if (qs().get("apply")) openApply();

  $$("[data-cancel]").forEach((b) => {
    b.onclick = async () => {
      if (!(await confirmAction({ title: "Cancel this leave request?", message: "HR will see it as cancelled.", confirmLabel: "Cancel request", danger: true }))) return;
      try {
        await api(`/api/hr/leave/${b.dataset.cancel}/cancel`, { method: "POST" });
        toast("Leave request cancelled.");
        render();
      } catch (err) { toast(err.message, true); }
    };
  });
}

/* ============================================================
   Leave approvals (HR)
   ============================================================ */
async function viewLeaveApprovals(ctx) {
  const status = qs().get("status") ?? "pending";
  const data = await api("/api/hr/leave" + (status !== "all" ? `?status=${status}` : ""));
  const total = Object.values(data.counts).reduce((a, b) => a + b, 0);
  const tabs = [["pending", "Pending"], ["approved", "Approved"], ["rejected", "Rejected"], ["cancelled", "Cancelled"], ["all", "All"]];
  const html = `<div class="page-intro"><div><h2>Leave approvals</h2><p>Review and respond to leave requests</p></div></div>
    <div class="card"><div class="toolbar"><div class="tabs">${tabs
      .map(([k, t]) => `<a class="tab ${k === status ? "active" : ""}" href="/hr/leave-requests?status=${k}" data-link>${t}<span class="n">${k === "all" ? total : data.counts[k] || 0}</span></a>`)
      .join("")}</div></div>
      ${leaveTable(data.items, {
        showEmployee: true,
        actions: (lv) => lv.status === "pending" && lv.employee_id !== state.user.employee?.id
          ? `<button class="btn btn-sm btn-success" data-review="approve" data-id="${lv.id}">Approve</button> <button class="btn btn-sm btn-danger" data-review="reject" data-id="${lv.id}">Reject</button>`
          : `<span class="muted" style="font-size:.78rem">${lv.reviewed_at ? fmtDate(lv.reviewed_at) : lv.status === "pending" ? "Needs another approver" : ""}</span>`,
      })}</div>`;
  if (!ctx.paint(html)) return;
  $$("[data-review]").forEach((b) => {
    b.onclick = () => reviewLeave(data.items.find((x) => x.id === +b.dataset.id), b.dataset.review, () => render());
  });
}

/* ============================================================
   My attendance
   ============================================================ */
async function viewMyAttendance(ctx) {
  const month = qs().get("month") || currentPeriod();
  const data = await api(`/api/hr/attendance/mine?month=${month}`);
  const s = data.summary;
  const html = `<div id="todayWrap" style="margin-bottom:20px">${todayCard(data.today)}</div>
    <div class="card"><div class="toolbar">
      <a class="icon-btn" href="/hr/attendance?month=${shiftPeriod(month, -1)}" data-link aria-label="Previous month">${ICONS.left}</a>
      <strong style="min-width:150px;text-align:center">${esc(periodLabel(month))}</strong>
      ${month < currentPeriod() ? `<a class="icon-btn" href="/hr/attendance?month=${shiftPeriod(month, 1)}" data-link aria-label="Next month">${ICONS.right}</a>` : `<span style="width:36px"></span>`}
      <span class="grow"></span>
      ${badge("present", `Present ${s.present || 0}`)} ${badge("wfh", `WFH ${s.wfh || 0}`)} ${badge("half_day", `Half day ${s.half_day || 0}`)} ${badge("absent", `Absent ${s.absent || 0}`)}
    </div>
    ${data.items.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Date</th><th>Day</th><th>Status</th><th>Check in</th><th>Check out</th><th class="num">Hours</th><th>Note</th></tr></thead><tbody>
      ${data.items.map((a) => `<tr><td class="nowrap">${fmtDate(a.date)}</td><td>${fmtDay(a.date)}</td><td>${badge(a.status)}</td>
        <td>${fmtTime(a.check_in)}</td><td>${fmtTime(a.check_out)}</td><td class="num">${hoursBetween(a.check_in, a.check_out)}</td><td class="muted">${esc(a.note || "")}</td></tr>`).join("")}
    </tbody></table></div>` : `<div class="card-empty">No attendance recorded for ${esc(periodLabel(month))}.</div>`}</div>`;
  if (!ctx.paint(html)) return;
  bindTodayCard($("#view"), () => render());
}

/* ============================================================
   My payslips
   ============================================================ */
async function viewMyPayslips(ctx) {
  const slips = await api("/api/hr/payslips/mine");
  const html = `<div class="page-intro"><div><h2>My payslips</h2><p>Payslips appear here once HR releases salary for the month</p></div></div>
    <div class="card">${slips.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Month</th><th class="num">Gross</th><th class="num">Deductions</th><th class="num">Net pay</th><th>Paid on</th><th></th></tr></thead><tbody>
      ${slips.map((p) => `<tr class="clickable" data-go="payslips/${p.id}"><td><strong>${esc(periodLabel(p.period))}</strong></td><td class="num">${inr(p.gross)}</td>
        <td class="num">${inr(p.total_deductions)}</td><td class="num"><strong>${inr(p.net_pay)}</strong></td><td>${fmtDate(p.paid_at)}</td>
        <td style="text-align:right"><a class="btn btn-sm" href="/hr/payslips/${p.id}" data-link>View</a></td></tr>`).join("")}
    </tbody></table></div>` : `<div class="card-empty">No payslips yet.</div>`}</div>`;
  if (!ctx.paint(html)) return;
  bindRowLinks();
}

function bindRowLinks() {
  $$("tr[data-go]").forEach((tr) => {
    tr.addEventListener("click", (e) => {
      if (e.target.closest("a, button, select, input")) return;
      navigate(tr.dataset.go);
    });
  });
}

/* ============================================================
   Payslip document
   ============================================================ */
async function viewPayslip(ctx, id) {
  const [p, company] = await Promise.all([api(`/api/hr/payslips/${id}`), api("/api/company")]);
  const e = p.employee;
  const backHref = MANAGERS.includes(state.user.role) && e.id !== state.user.employee?.id ? `/hr/payroll?period=${p.period}` : "/hr/payslips";
  const html = `<div class="page-intro no-print"><a href="${backHref}" class="btn btn-ghost" data-link>${ICONS.back} Back</a>
      <div class="actions">${badge(p.status)}<button class="btn btn-primary" id="printBtn">${ICONS.print} Print / Save PDF</button></div></div>
    <article class="payslip">
      <header class="ps-head">
        <div class="ps-brand"><span class="boot-mark" style="animation:none">E</span>
          <div><h2>${esc(company.name)}</h2><p>${esc(company.address_line)}</p><p>CIN: ${esc(company.cin)}</p></div></div>
        <div class="ps-title"><h3>Payslip</h3><strong>${esc(periodLabel(p.period))}</strong></div>
      </header>
      <section class="ps-emp">
        <div><span>Employee</span><strong>${esc(e.full_name)}</strong></div>
        <div><span>Employee ID</span><strong>${esc(e.employee_code)}</strong></div>
        <div><span>Designation</span><strong>${esc(e.designation)}</strong></div>
        <div><span>Department</span><strong>${esc(e.department || "—")}</strong></div>
        <div><span>Date of joining</span><strong>${fmtDate(e.date_of_joining)}</strong></div>
        <div><span>PAN</span><strong>${esc(e.pan || "—")}</strong></div>
        <div><span>Bank A/C</span><strong>${esc(e.bank_account || "—")}</strong></div>
        <div><span>Paid days</span><strong>${p.working_days - p.lop_days} / ${p.working_days}${p.lop_days ? ` (LOP ${p.lop_days})` : ""}</strong></div>
      </section>
      <section class="ps-tables">
        <table><thead><tr><th>Earnings</th><th>Amount</th></tr></thead><tbody>
          <tr><td>Basic salary</td><td>${inr(p.basic)}</td></tr>
          <tr><td>House rent allowance</td><td>${inr(p.hra)}</td></tr>
          <tr><td>Special allowance</td><td>${inr(p.special_allowance)}</td></tr>
        </tbody><tfoot><tr><td>Gross earnings</td><td>${inr(p.gross)}</td></tr></tfoot></table>
        <table><thead><tr><th>Deductions</th><th>Amount</th></tr></thead><tbody>
          <tr><td>Provident fund (employee)</td><td>${inr(p.pf)}</td></tr>
          <tr><td>Income tax (TDS)</td><td>${inr(p.tds)}</td></tr>
          <tr><td>Loss of pay${p.lop_days ? ` (${p.lop_days} day${p.lop_days > 1 ? "s" : ""})` : ""}</td><td>${inr(p.lop_deduction)}</td></tr>
        </tbody><tfoot><tr><td>Total deductions</td><td>${inr(p.total_deductions)}</td></tr></tfoot></table>
      </section>
      <div class="ps-net"><div><span>Net pay</span><strong>${inr(p.net_pay)}</strong></div>
        <div class="words">Rupees ${esc(inrWords(p.net_pay))} Only</div></div>
      <p class="ps-foot">This is a computer-generated payslip and does not require a signature.${p.paid_at ? ` Paid on ${fmtDate(p.paid_at)}.` : " Status: draft — not yet paid."}</p>
    </article>`;
  if (!ctx.paint(html)) return;
  setTitle(`Payslip · ${periodLabel(p.period)}`);
  $("#printBtn").onclick = () => window.print();
}

/* ============================================================
   Employees (HR)
   ============================================================ */
async function viewEmployees(ctx) {
  const [emps, depts] = await Promise.all([api("/api/hr/employees"), api("/api/hr/departments")]);
  const params = qs();
  const html = `<div class="page-intro"><div><h2>Employees</h2><p>${emps.filter((e) => e.status !== "exited").length} current · ${emps.length} total records</p></div>
      <div class="actions"><a class="btn" id="exportBtn" href="/api/hr/employees/export.csv" download>${ICONS.download} Export CSV</a>
      <button class="btn btn-primary" id="addEmp">${ICONS.plus} Add employee</button></div></div>
    <div class="card"><div class="toolbar">
      <div class="search">${ICONS.search}<input class="input" id="empSearch" type="search" placeholder="Search name, email, code, designation…" value="${esc(params.get("q") || "")}" /></div>
      <select class="select" id="empDept"><option value="">All departments</option>${depts.map((d) => `<option value="${d.id}">${esc(d.name)}</option>`).join("")}</select>
      <select class="select" id="empStatus">
        <option value="current">Current staff</option><option value="">All statuses</option><option value="active">Active</option>
        <option value="probation">Probation</option><option value="notice">Notice period</option><option value="exited">Exited</option></select>
    </div><div id="empTable"></div></div>`;
  if (!ctx.paint(html)) return;

  const draw = () => {
    const q = $("#empSearch").value.trim().toLowerCase();
    const dept = $("#empDept").value;
    const st = $("#empStatus").value;
    const list = emps.filter((e) =>
      (!q || [e.full_name, e.email, e.employee_code, e.designation].join(" ").toLowerCase().includes(q)) &&
      (!dept || String(e.department_id) === dept) &&
      (!st || (st === "current" ? e.status !== "exited" : e.status === st)));
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (dept) p.set("department_id", dept);
    if (st) p.set("status", st);
    $("#exportBtn").href = "/api/hr/employees/export.csv?" + p;
    $("#empTable").innerHTML = list.length
      ? `<div class="table-wrap"><table class="table"><thead><tr><th>Employee</th><th>ID</th><th>Department</th><th>Designation</th><th>Type</th><th>Status</th><th>Joined</th><th>Portal</th></tr></thead><tbody>
        ${list.map((e) => `<tr class="clickable" data-go="employees/${e.id}">
          <td>${personCell(e.full_name, e.email)}</td><td class="nowrap">${esc(e.employee_code)}</td>
          <td>${esc(e.department || "—")}</td><td>${esc(e.designation)}</td><td class="nowrap">${esc(label(e.employment_type))}</td>
          <td>${badge(e.status)}</td><td class="nowrap">${fmtDate(e.date_of_joining)}</td>
          <td>${e.has_login ? badge(e.login_role) : `<span class="muted">No login</span>`}</td></tr>`).join("")}
        </tbody></table></div>`
      : `<div class="card-empty">${emps.length ? "No employees match these filters." : "No employees yet — add your first team member."}</div>`;
    bindRowLinks();
  };
  if (params.get("department_id")) $("#empDept").value = params.get("department_id");
  if (params.has("status")) $("#empStatus").value = params.get("status");
  $("#empSearch").addEventListener("input", draw);
  $("#empDept").addEventListener("change", draw);
  $("#empStatus").addEventListener("change", draw);
  draw();
  $("#addEmp").onclick = () => employeeForm(null);
  if (params.get("add")) {
    history.replaceState({}, "", "/hr/employees");
    employeeForm(null);
  }
}

async function employeeForm(emp) {
  const [depts, all] = await Promise.all([api("/api/hr/departments"), api("/api/hr/employees?status=current")]);
  const v = emp || { employment_type: "full_time", status: "active", date_of_joining: todayISO(), monthly_gross: 0, monthly_tds: 0, pf_applicable: true };
  const managers = all.filter((m) => !emp || m.id !== emp.id).map((m) => [m.id, `${m.full_name} (${m.employee_code})`]);
  openModal({
    title: emp ? `Edit ${emp.full_name}` : "Add employee",
    wide: true,
    submitLabel: emp ? "Save changes" : "Create employee",
    body: `<div class="form-grid">
      <p class="form-section">Personal</p>
      ${field("full_name", "Full name", { value: v.full_name, required: true })}
      ${field("email", "Work email", { type: "email", value: v.email, required: true, help: emp ? "" : "Also used as their portal login." })}
      ${field("phone", "Phone", { type: "tel", value: v.phone, placeholder: "+91 98765 43210" })}
      ${field("date_of_birth", "Date of birth", { type: "date", value: v.date_of_birth })}
      ${selectField("gender", "Gender", [["female", "Female"], ["male", "Male"], ["other", "Other"]], { value: v.gender, empty: "Prefer not to say" })}
      ${field("emergency_contact", "Emergency contact", { value: v.emergency_contact, placeholder: "Name · relation · phone" })}
      ${textareaField("address", "Address", { value: v.address, rows: 2 })}
      <p class="form-section">Job</p>
      ${field("designation", "Designation", { value: v.designation, required: true, placeholder: "e.g. Tax Associate" })}
      ${selectField("department_id", "Department", depts.map((d) => [d.id, d.name]), { value: v.department_id, empty: "— Unassigned —" })}
      ${selectField("manager_id", "Reporting manager", managers, { value: v.manager_id, empty: "— None —" })}
      ${selectField("employment_type", "Employment type", [["full_time", "Full-time"], ["part_time", "Part-time"], ["contract", "Contract"], ["intern", "Intern / Article"]], { value: v.employment_type })}
      ${selectField("status", "Status", [["active", "Active"], ["probation", "Probation"], ["notice", "Notice period"], ["exited", "Exited"]], { value: v.status })}
      ${field("date_of_joining", "Date of joining", { type: "date", value: v.date_of_joining, required: true })}
      ${field("date_of_exit", "Date of exit", { type: "date", value: v.date_of_exit, help: "Set when an employee leaves." })}
      <p class="form-section">Compensation &amp; statutory</p>
      ${field("monthly_gross", "Monthly gross salary (₹)", { type: "number", value: v.monthly_gross, required: true, attrs: 'min="0" step="100"', help: "Split as Basic 50% · HRA 20% · Special 30%." })}
      ${field("monthly_tds", "Monthly TDS (₹)", { type: "number", value: v.monthly_tds, attrs: 'min="0" step="100"' })}
      ${field("pan", "PAN", { value: v.pan, placeholder: "ABCDE1234F", attrs: 'maxlength="10" style="text-transform:uppercase"' })}
      ${field("bank_account", "Bank account no.", { value: v.bank_account })}
      ${field("bank_ifsc", "IFSC", { value: v.bank_ifsc, placeholder: "SBIN0001234", attrs: 'maxlength="11" style="text-transform:uppercase"' })}
      <div class="field" style="align-self:end"><label class="check"><input type="checkbox" name="pf_applicable" ${v.pf_applicable ? "checked" : ""}/> Deduct provident fund (12% of basic)</label></div>
      ${emp ? "" : `<p class="form-section">Portal access</p>
      <label class="check full"><input type="checkbox" name="create_login" checked /> Create an HR Portal login for this employee (a temporary password will be shown once)</label>`}
    </div>`,
    onSubmit: async (form) => {
      const body = formValues(form);
      ["department_id", "manager_id"].forEach((k) => (body[k] = body[k] ? Number(body[k]) : null));
      if (emp) {
        await api(`/api/hr/employees/${emp.id}`, { method: "PATCH", body });
        toast("Employee updated.");
        render();
        return;
      }
      const r = await api("/api/hr/employees", { method: "POST", body });
      navigate(`employees/${r.employee.id}`);
      if (r.login?.temp_password) {
        showCredentials(r.employee.email, r.login.temp_password, `${r.employee.full_name} added`);
        return false;
      }
      toast(r.login?.linked_existing ? "Employee added and linked to their existing account." : "Employee added.");
    },
  });
}

function showCredentials(email, password, title) {
  const text = `EWAY HR Portal\nLogin: ${location.origin}/login\nEmail: ${email}\nTemporary password: ${password}`;
  openModal({
    title,
    body: `<p>Share these sign-in details with the employee securely. The temporary password is shown <strong>only once</strong> — ask them to change it from <em>My Profile</em> after logging in.</p>
      <div class="credential">
        <div class="row"><span class="muted">Login page</span><code>${esc(location.origin)}/login</code></div>
        <div class="row"><span class="muted">Email</span><code>${esc(email)}</code></div>
        <div class="row"><span class="muted">Temporary password</span><code>${esc(password)}</code></div>
      </div>
      <button type="button" class="btn btn-sm" id="copyCred" style="margin-top:14px">Copy details</button>`,
    onOpen: (body) => {
      $("#copyCred", body).onclick = async () => {
        try { await navigator.clipboard.writeText(text); toast("Copied to clipboard."); } catch { toast("Couldn't copy — please copy manually.", true); }
      };
    },
  });
}

async function viewEmployee(ctx, id) {
  const d = await api(`/api/hr/employees/${id}`);
  const e = d.employee;
  const isAdmin = state.user.role === "admin";
  const html = `<div class="page-intro" style="margin-bottom:14px"><a href="/hr/employees" class="btn btn-ghost" data-link>${ICONS.back} All employees</a></div>
    <div class="card card-pad" style="margin-bottom:20px"><div class="profile-head">${avatar(e.full_name, "lg")}
      <div class="grow"><h2>${esc(e.full_name)}</h2>
        <div class="meta"><span>${esc(e.employee_code)}</span><span>·</span><span>${esc(e.designation)}${e.department ? " · " + esc(e.department) : ""}</span>${badge(e.status)}</div></div>
      <div class="actions">
        <button class="btn" id="loginBtn">${e.has_login ? "Reset password" : "Create portal login"}</button>
        <button class="btn btn-primary" id="editBtn">Edit</button>
        ${isAdmin ? `<button class="btn btn-danger" id="delBtn">Delete</button>` : ""}
      </div></div></div>
    <div class="grid grid-main"><div class="stack">
      <div class="grid grid-2">
        <div class="card"><div class="card-head"><h3>Contact &amp; personal</h3></div><div class="card-body"><dl class="dl">
          <dt>Email</dt><dd><a href="mailto:${esc(e.email)}">${esc(e.email)}</a></dd>
          <dt>Phone</dt><dd>${esc(e.phone || "—")}</dd>
          <dt>Date of birth</dt><dd>${fmtDate(e.date_of_birth)}</dd>
          <dt>Gender</dt><dd>${esc(label(e.gender))}</dd>
          <dt>Address</dt><dd>${esc(e.address || "—")}</dd>
          <dt>Emergency</dt><dd>${esc(e.emergency_contact || "—")}</dd></dl></div></div>
        <div class="card"><div class="card-head"><h3>Employment</h3></div><div class="card-body"><dl class="dl">
          <dt>Type</dt><dd>${esc(label(e.employment_type))}</dd>
          <dt>Manager</dt><dd>${e.manager_id ? `<a href="/hr/employees/${e.manager_id}" data-link>${esc(e.manager)}</a>` : "—"}</dd>
          <dt>Joined</dt><dd>${fmtDate(e.date_of_joining)}</dd>
          <dt>Exit date</dt><dd>${fmtDate(e.date_of_exit)}</dd>
          <dt>Portal login</dt><dd>${e.has_login ? badge(e.login_role) : "No login"}</dd>
          <dt>Record updated</dt><dd>${fmtDate(e.updated_at)}</dd></dl></div></div>
      </div>
      <div class="card"><div class="card-head"><h3>Leave balance · ${new Date().getFullYear()}</h3></div><div class="card-body">${balancesHTML(d.leave_balances)}</div></div>
      <div class="card"><div class="card-head"><h3>Recent leave</h3></div>${leaveTable(d.leave_requests)}</div>
      <div class="card"><div class="card-head"><h3>Payslips</h3></div>
        ${d.payslips.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Month</th><th class="num">Gross</th><th class="num">Net</th><th>Status</th></tr></thead><tbody>
          ${d.payslips.map((p) => `<tr class="clickable" data-go="payslips/${p.id}"><td>${esc(periodLabel(p.period))}</td><td class="num">${inr(p.gross)}</td><td class="num"><strong>${inr(p.net_pay)}</strong></td><td>${badge(p.status)}</td></tr>`).join("")}
        </tbody></table></div>` : `<div class="card-empty">No payslips generated yet.</div>`}</div>
    </div><div class="stack">
      <div class="card"><div class="card-head"><h3>Compensation</h3></div><div class="card-body"><dl class="dl">
        <dt>Monthly gross</dt><dd><strong>${inr(e.monthly_gross)}</strong></dd>
        <dt>Annual CTC</dt><dd>${inr(e.monthly_gross * 12)}</dd>
        <dt>Monthly TDS</dt><dd>${inr(e.monthly_tds)}</dd>
        <dt>PF</dt><dd>${e.pf_applicable ? "Applicable" : "Not applicable"}</dd>
        <dt>PAN</dt><dd>${esc(e.pan || "—")}</dd>
        <dt>Bank</dt><dd>${esc(e.bank_account || "—")}${e.bank_ifsc ? `<br><span class="muted">${esc(e.bank_ifsc)}</span>` : ""}</dd></dl></div></div>
      <div class="card"><div class="card-head"><h3>Attendance · last 30 days</h3></div>
        ${d.attendance.length ? `<div class="list">${d.attendance.slice(0, 10).map((a) => `<div class="list-item"><div class="grow"><div class="title">${fmtDate(a.date)} <span class="muted" style="font-weight:500">${fmtDay(a.date)}</span></div>
          <div class="sub">${fmtTime(a.check_in)} – ${fmtTime(a.check_out)}</div></div>${badge(a.status)}</div>`).join("")}</div>` : `<div class="card-empty">No attendance records.</div>`}</div>
      ${d.direct_reports.length ? `<div class="card"><div class="card-head"><h3>Direct reports</h3></div><div class="list">${d.direct_reports
        .map((r) => `<a class="list-item" href="/hr/employees/${r.id}" data-link>${avatar(r.full_name, "sm")}<div class="grow"><div class="title">${esc(r.full_name)}</div><div class="sub">${esc(r.designation)}</div></div></a>`).join("")}</div></div>` : ""}
    </div></div>`;
  if (!ctx.paint(html)) return;
  setTitle(e.full_name);
  bindRowLinks();
  $("#editBtn").onclick = () => employeeForm(e);
  $("#loginBtn").onclick = async () => {
    const reset = e.has_login;
    if (!(await confirmAction({
      title: reset ? "Reset password?" : "Create portal login?",
      message: reset
        ? `${esc(e.full_name)} will be signed out everywhere and given a new temporary password.`
        : `A login will be created for <strong>${esc(e.email)}</strong> with a temporary password.`,
      confirmLabel: reset ? "Reset password" : "Create login",
    }))) return;
    try {
      const r = await api(`/api/hr/employees/${e.id}/login`, { method: "POST" });
      if (r.temp_password) showCredentials(r.email, r.temp_password, reset ? "Password reset" : "Login created");
      else toast("Linked to the employee's existing account.");
      if (!reset) render();
    } catch (err) { toast(err.message, true); }
  };
  $("#delBtn")?.addEventListener("click", async () => {
    if (!(await confirmAction({
      title: "Permanently delete this employee?",
      message: `This deletes ${esc(e.full_name)}'s record, leave, attendance and payslips. For people who've left, set status to <strong>Exited</strong> instead to keep history.`,
      confirmLabel: "Delete permanently",
      danger: true,
    }))) return;
    try {
      await api(`/api/hr/employees/${e.id}`, { method: "DELETE" });
      toast("Employee deleted.");
      navigate("employees");
    } catch (err) { toast(err.message, true); }
  });
}

/* ============================================================
   Attendance register (HR)
   ============================================================ */
async function viewRegister(ctx) {
  const day = qs().get("date") || todayISO();
  const data = await api(`/api/hr/attendance?date=${day}`);
  const statuses = [["", "— Not marked —"], ["present", "Present"], ["wfh", "Work from home"], ["half_day", "Half day"], ["absent", "Absent"], ["leave", "On leave"]];
  const html = `<div class="page-intro"><div><h2>Attendance register</h2><p>Mark or correct attendance for any day</p></div></div>
    <div class="card"><div class="toolbar">
      <a class="icon-btn" href="/hr/attendance-register?date=${shiftDate(day, -1)}" data-link aria-label="Previous day">${ICONS.left}</a>
      <input class="input" type="date" id="regDate" value="${day}" max="${todayISO()}" style="min-width:0;width:auto" />
      ${day < todayISO() ? `<a class="icon-btn" href="/hr/attendance-register?date=${shiftDate(day, 1)}" data-link aria-label="Next day">${ICONS.right}</a>` : ""}
      <strong>${parseDate(day).toLocaleDateString("en-IN", { weekday: "long" })}</strong>
      ${data.is_weekly_off ? `<span class="badge plain">Weekly off</span>` : ""}
      <span class="grow"></span><div id="regSummary" class="actions"></div>
    </div>
    ${data.rows.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Employee</th><th>Department</th><th>Check in</th><th>Check out</th><th>Status</th></tr></thead><tbody>
      ${data.rows.map((r) => `<tr><td>${personCell(r.employee.full_name, r.employee.employee_code, "sm")}</td><td>${esc(r.employee.department || "—")}</td>
        <td>${fmtTime(r.attendance?.check_in)}</td><td>${fmtTime(r.attendance?.check_out)}</td>
        <td><select class="select" data-emp="${r.employee.id}" style="min-width:170px">${statuses.map(([v, t]) => `<option value="${v}" ${v === (r.effective_status || "") ? "selected" : ""}>${t}</option>`).join("")}</select>
        ${r.on_leave ? `<div class="p-sub muted" style="font-size:.75rem;margin-top:4px">Approved ${esc(label(r.on_leave))} leave</div>` : ""}</td></tr>`).join("")}
    </tbody></table></div>` : `<div class="card-empty">No employees on the rolls for this date.</div>`}</div>`;
  if (!ctx.paint(html)) return;
  const drawSummary = () => {
    const counts = {};
    $$("select[data-emp]").forEach((s) => (counts[s.value || "unmarked"] = (counts[s.value || "unmarked"] || 0) + 1));
    $("#regSummary").innerHTML = ["present", "wfh", "half_day", "leave", "absent", "unmarked"]
      .filter((k) => counts[k]).map((k) => badge(k === "unmarked" ? "" : k, `${label(k)} ${counts[k]}`)).join(" ");
  };
  drawSummary();
  $("#regDate").addEventListener("change", (e) => e.target.value && navigate(`attendance-register?date=${e.target.value}`));
  $$("select[data-emp]").forEach((s) => {
    let prev = s.value;
    s.addEventListener("change", async () => {
      if (!s.value) { s.value = prev; return toast("Choose a status to mark attendance.", true); }
      try {
        await api("/api/hr/attendance", { method: "PUT", body: { employee_id: +s.dataset.emp, date: day, status: s.value } });
        prev = s.value;
        drawSummary();
        toast("Attendance saved.");
      } catch (err) { s.value = prev; toast(err.message, true); }
    });
  });
}

/* ============================================================
   Payroll (HR)
   ============================================================ */
async function viewPayroll(ctx) {
  const period = qs().get("period") || currentPeriod();
  const data = await api(`/api/hr/payroll?period=${period}`);
  const t = data.totals;
  const drafts = data.count - data.paid;
  const html = `<div class="page-intro"><div><h2>Payroll</h2><p>Generate salary slips from each employee's monthly gross, approved unpaid leave and statutory deductions</p></div></div>
    <div class="card" style="margin-bottom:20px"><div class="toolbar" style="border-bottom:0">
      <a class="icon-btn" href="/hr/payroll?period=${shiftPeriod(period, -1)}" data-link aria-label="Previous month">${ICONS.left}</a>
      <input class="input" type="month" id="periodInput" value="${period}" style="min-width:0;width:auto" />
      <a class="icon-btn" href="/hr/payroll?period=${shiftPeriod(period, 1)}" data-link aria-label="Next month">${ICONS.right}</a>
      <strong>${esc(periodLabel(period))}</strong>
      <span class="grow"></span>
      <button class="btn" id="runBtn">${ICONS.play} ${data.count ? "Re-run payroll" : "Run payroll"}</button>
      <button class="btn btn-primary" id="payAllBtn" ${drafts ? "" : "disabled"}>Mark ${drafts || ""} as paid</button>
    </div></div>
    ${data.count ? `<div class="stats">
      <div class="stat dark"><div class="label">Net payable</div><div class="value" style="font-size:1.5rem">${inr(t.net_pay)}</div><div class="hint">${data.count} employees</div></div>
      <div class="stat"><div class="label">Gross</div><div class="value" style="font-size:1.5rem">${inr(t.gross)}</div></div>
      <div class="stat"><div class="label">PF</div><div class="value" style="font-size:1.5rem">${inr(t.pf)}</div></div>
      <div class="stat"><div class="label">TDS</div><div class="value" style="font-size:1.5rem">${inr(t.tds)}</div></div>
      <div class="stat"><div class="label">Paid</div><div class="value">${data.paid}<span class="muted" style="font-size:1rem;font-weight:600"> / ${data.count}</span></div></div>
    </div>
    <div class="card"><div class="table-wrap"><table class="table"><thead><tr><th>Employee</th><th class="num">Paid days</th><th class="num">Gross</th><th class="num">LOP</th><th class="num">PF</th><th class="num">TDS</th><th class="num">Net pay</th><th>Status</th><th></th></tr></thead><tbody>
      ${data.items.map((p) => `<tr class="clickable" data-go="payslips/${p.id}"><td>${personCell(p.employee.full_name, `${p.employee.employee_code} · ${p.employee.designation}`, "sm")}</td>
        <td class="num">${p.working_days - p.lop_days}/${p.working_days}</td><td class="num">${inr(p.gross)}</td><td class="num">${p.lop_deduction ? inr(p.lop_deduction) : "—"}</td>
        <td class="num">${inr(p.pf)}</td><td class="num">${inr(p.tds)}</td><td class="num"><strong>${inr(p.net_pay)}</strong></td><td>${badge(p.status)}</td>
        <td class="nowrap" style="text-align:right">${p.status === "draft" ? `<button class="btn btn-sm" data-pay="${p.id}">Mark paid</button>` : `<span class="muted" style="font-size:.78rem">${fmtDate(p.paid_at)}</span>`}</td></tr>`).join("")}
    </tbody><tfoot><tr><td>Total</td><td></td><td class="num">${inr(t.gross)}</td><td class="num">${inr(t.lop_deduction)}</td><td class="num">${inr(t.pf)}</td><td class="num">${inr(t.tds)}</td><td class="num">${inr(t.net_pay)}</td><td colspan="2"></td></tr></tfoot></table></div></div>`
    : emptyState(`No payroll for ${periodLabel(period)} yet`, "Run payroll to generate draft payslips for everyone employed this month. You can review and re-run as often as needed until you mark them paid.", `<button class="btn btn-primary" id="runBtn2">${ICONS.play} Run payroll for ${esc(periodLabel(period))}</button>`)}`;
  if (!ctx.paint(html)) return;
  bindRowLinks();
  $("#periodInput").addEventListener("change", (e) => e.target.value && navigate(`payroll?period=${e.target.value}`));
  const run = async () => {
    if (data.count && !(await confirmAction({ title: "Re-run payroll?", message: `Draft payslips for ${esc(periodLabel(period))} will be recalculated from current salaries and approved leave. Paid payslips are never changed.`, confirmLabel: "Re-run" }))) return;
    try {
      const r = await api("/api/hr/payroll/run", { method: "POST", body: { period } });
      toast(`Payroll ready: ${r.created} created, ${r.updated} updated${r.skipped ? `, ${r.skipped} skipped (already paid)` : ""}.`);
      render();
    } catch (err) { toast(err.message, true); }
  };
  $("#runBtn").onclick = run;
  $("#runBtn2")?.addEventListener("click", run);
  $("#payAllBtn").onclick = async () => {
    if (!(await confirmAction({ title: `Release salary for ${periodLabel(period)}?`, message: `${drafts} draft payslip(s) totalling ${inr(data.items.filter((p) => p.status === "draft").reduce((a, p) => a + p.net_pay, 0))} will be marked as paid and become visible to employees.`, confirmLabel: "Mark as paid" }))) return;
    try {
      const r = await api("/api/hr/payroll/pay-all", { method: "POST", body: { period } });
      toast(`${r.marked_paid} payslip(s) marked as paid.`);
      render();
    } catch (err) { toast(err.message, true); }
  };
  $$("[data-pay]").forEach((b) => {
    b.onclick = async () => {
      try {
        await api(`/api/hr/payroll/${b.dataset.pay}/pay`, { method: "POST" });
        toast("Marked as paid.");
        render();
      } catch (err) { toast(err.message, true); }
    };
  });
}

/* ============================================================
   Departments (HR)
   ============================================================ */
async function viewDepartments(ctx) {
  const depts = await api("/api/hr/departments");
  const html = `<div class="page-intro"><div><h2>Departments</h2><p>${depts.length} departments</p></div>
      <button class="btn btn-primary" id="addDept">${ICONS.plus} Add department</button></div>
    <div class="card">${depts.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>Department</th><th>Description</th><th class="num">Headcount</th><th></th></tr></thead><tbody>
      ${depts.map((d) => `<tr><td><strong>${esc(d.name)}</strong></td><td class="muted">${esc(d.description || "—")}</td><td class="num">${d.headcount}</td>
        <td class="nowrap" style="text-align:right"><a class="btn btn-sm btn-ghost" href="/hr/employees?department_id=${d.id}" data-link>View staff</a>
        <button class="btn btn-sm" data-edit="${d.id}">Edit</button> <button class="btn btn-sm btn-danger" data-del="${d.id}">Delete</button></td></tr>`).join("")}
    </tbody></table></div>` : `<div class="card-empty">No departments yet.</div>`}</div>`;
  if (!ctx.paint(html)) return;
  const form = (d) => openModal({
    title: d ? "Edit department" : "Add department",
    body: `<div class="form-grid">${field("name", "Name", { value: d?.name, required: true, full: true })}${textareaField("description", "Description", { value: d?.description, rows: 3 })}</div>`,
    onSubmit: async (f) => {
      await api(d ? `/api/hr/departments/${d.id}` : "/api/hr/departments", { method: d ? "PATCH" : "POST", body: formValues(f) });
      toast(d ? "Department updated." : "Department added.");
      render();
    },
  });
  $("#addDept").onclick = () => form(null);
  $$("[data-edit]").forEach((b) => (b.onclick = () => form(depts.find((d) => d.id === +b.dataset.edit))));
  $$("[data-del]").forEach((b) => {
    b.onclick = async () => {
      const d = depts.find((x) => x.id === +b.dataset.del);
      if (!(await confirmAction({ title: `Delete ${esc(d.name)}?`, message: d.headcount ? `${d.headcount} employee(s) will become unassigned.` : "This department has no employees.", confirmLabel: "Delete", danger: true }))) return;
      try {
        await api(`/api/hr/departments/${d.id}`, { method: "DELETE" });
        toast("Department deleted.");
        render();
      } catch (err) { toast(err.message, true); }
    };
  });
}

/* ============================================================
   Website enquiries
   ============================================================ */
async function viewEnquiries(ctx) {
  const status = qs().get("status") ?? "new";
  const data = await api("/api/admin/enquiries" + (status !== "all" ? `?status=${status}` : ""));
  const total = Object.values(data.counts).reduce((a, b) => a + b, 0);
  const tabs = [["new", "New"], ["read", "Read"], ["replied", "Replied"], ["archived", "Archived"], ["all", "All"]];
  const isAdmin = state.user.role === "admin";
  const html = `<div class="page-intro"><div><h2>Website enquiries</h2><p>Messages submitted through the contact form on the public site</p></div></div>
    <div class="card"><div class="toolbar"><div class="tabs">${tabs
      .map(([k, t]) => `<a class="tab ${k === status ? "active" : ""}" href="/hr/enquiries?status=${k}" data-link>${t}<span class="n">${k === "all" ? total : data.counts[k] || 0}</span></a>`)
      .join("")}</div></div>
    ${data.items.length ? data.items.map((m) => `<div class="announcement" data-id="${m.id}">
      <div style="display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap">
        ${avatar(m.name)}
        <div style="flex:1;min-width:220px"><h4>${esc(m.name)} ${badge(m.status)}</h4>
          <div class="meta" style="margin-top:2px"><a href="mailto:${esc(m.email)}">${esc(m.email)}</a>${m.phone ? `<span>· ${esc(m.phone)}</span>` : ""}<span>· ${fmtDateTime(m.received_at)}</span></div>
          ${m.service ? `<p style="margin-top:6px"><strong>${esc(m.service)}</strong></p>` : ""}
          <div class="enquiry-msg">${esc(m.message)}</div></div>
        <div class="actions">
          <a class="btn btn-sm" href="mailto:${esc(m.email)}?subject=${encodeURIComponent("Re: " + (m.service || "Your enquiry") + " — EWAY Financial")}" data-reply="${m.id}">Reply by email</a>
          <select class="select" data-status="${m.id}" style="width:auto;min-width:130px;padding-top:6px;padding-bottom:6px">
            ${["new", "read", "replied", "archived"].map((s) => `<option value="${s}" ${s === m.status ? "selected" : ""}>${label(s)}</option>`).join("")}</select>
          ${isAdmin ? `<button class="btn btn-sm btn-ghost btn-danger" data-del="${m.id}">Delete</button>` : ""}
        </div></div></div>`).join("")
    : `<div class="card-empty">No ${status === "all" ? "" : status + " "}enquiries.</div>`}</div>`;
  if (!ctx.paint(html)) return;
  const setStatus = async (id, s) => {
    await api(`/api/admin/enquiries/${id}`, { method: "PATCH", body: { status: s } });
    refreshCounts();
  };
  $$("[data-status]").forEach((sel) => {
    sel.addEventListener("change", async () => {
      try { await setStatus(sel.dataset.status, sel.value); toast(`Marked as ${sel.value}.`); render(); } catch (err) { toast(err.message, true); }
    });
  });
  $$("[data-reply]").forEach((a) => a.addEventListener("click", () => setStatus(a.dataset.reply, "replied").catch(() => {})));
  $$("[data-del]").forEach((b) => {
    b.onclick = async () => {
      if (!(await confirmAction({ title: "Delete enquiry?", message: "This can't be undone.", confirmLabel: "Delete", danger: true }))) return;
      try { await api(`/api/admin/enquiries/${b.dataset.del}`, { method: "DELETE" }); toast("Enquiry deleted."); refreshCounts(); render(); } catch (err) { toast(err.message, true); }
    };
  });
}

/* ============================================================
   Users & roles (admin)
   ============================================================ */
async function viewUsers(ctx) {
  const users = await api("/api/admin/users");
  const roles = [["admin", "Admin"], ["hr", "HR"], ["employee", "Employee"], ["client", "Client"]];
  const html = `<div class="page-intro"><div><h2>Users &amp; roles</h2><p>Everyone who can sign in. New sign-ups are <strong>clients</strong>; grant HR or admin access here. Employees get logins from the Employees page.</p></div></div>
    <div class="card"><div class="toolbar"><div class="search">${ICONS.search}<input class="input" id="userSearch" type="search" placeholder="Search name or email…" /></div>
      <select class="select" id="roleFilter"><option value="">All roles</option>${roles.map(([v, t]) => `<option value="${v}">${t}</option>`).join("")}</select></div>
    <div id="userTable"></div></div>`;
  if (!ctx.paint(html)) return;
  const draw = () => {
    const q = $("#userSearch").value.toLowerCase();
    const r = $("#roleFilter").value;
    const list = users.filter((u) => (!q || (u.name + " " + u.email).toLowerCase().includes(q)) && (!r || u.role === r));
    $("#userTable").innerHTML = list.length ? `<div class="table-wrap"><table class="table"><thead><tr><th>User</th><th>Employee</th><th>Role</th><th>Active</th><th>Last login</th><th>Joined</th></tr></thead><tbody>
      ${list.map((u) => `<tr><td>${personCell(u.name, u.email, "sm")}</td>
        <td>${u.employee ? `<a href="/hr/employees/${u.employee.id}" data-link>${esc(u.employee.employee_code)}</a>` : `<span class="muted">—</span>`}</td>
        <td><select class="select" data-role="${u.id}" style="width:auto;min-width:130px;padding-top:6px;padding-bottom:6px" ${u.id === state.user.id ? "disabled" : ""}>
          ${roles.map(([v, t]) => `<option value="${v}" ${v === u.role ? "selected" : ""}>${t}</option>`).join("")}</select></td>
        <td><label class="check"><input type="checkbox" data-active="${u.id}" ${u.is_active ? "checked" : ""} ${u.id === state.user.id ? "disabled" : ""}/> ${u.is_active ? "Active" : "Disabled"}</label></td>
        <td class="nowrap muted">${u.last_login_at ? fmtDateTime(u.last_login_at) : "Never"}</td><td class="nowrap muted">${fmtDate(u.created_at)}</td></tr>`).join("")}
    </tbody></table></div>` : `<div class="card-empty">No users match.</div>`;
    $$("[data-role]").forEach((s) => {
      s.addEventListener("change", async () => {
        const u = users.find((x) => x.id === s.dataset.role);
        try { Object.assign(u, await api(`/api/admin/users/${u.id}`, { method: "PATCH", body: { role: s.value } })); toast(`${u.name} is now ${label(u.role)}.`); }
        catch (err) { s.value = u.role; toast(err.message, true); }
      });
    });
    $$("[data-active]").forEach((c) => {
      c.addEventListener("change", async () => {
        const u = users.find((x) => x.id === c.dataset.active);
        try { Object.assign(u, await api(`/api/admin/users/${u.id}`, { method: "PATCH", body: { is_active: c.checked } })); toast(c.checked ? "Account enabled." : "Account disabled and signed out."); draw(); }
        catch (err) { c.checked = u.is_active; toast(err.message, true); }
      });
    });
  };
  $("#userSearch").addEventListener("input", draw);
  $("#roleFilter").addEventListener("change", draw);
  draw();
}

/* ============================================================
   Boot
   ============================================================ */
(async function boot() {
  try {
    const res = await fetch("/api/auth/me", { headers: { Accept: "application/json" } });
    if (res.status === 401) {
      window.location.href = "/login?next=" + encodeURIComponent(location.pathname + location.search);
      return;
    }
    state.user = (await res.json()).user;
  } catch {
    $("#boot p").textContent = "Couldn't reach the server. Please refresh.";
    return;
  }
  if (!STAFF.includes(state.user.role)) {
    $("#boot").innerHTML = `<div class="boot-mark" style="animation:none">E</div>
      <h2 style="color:var(--ink);font-size:1.3rem">HR Portal is for EWAY staff</h2>
      <p style="max-width:420px;text-align:center">You're signed in as ${esc(state.user.email)}, which doesn't have staff access. If you work at EWAY Financial, ask HR to add you as an employee.</p>
      <a class="btn btn-primary" href="/">Back to website</a>`;
    return;
  }
  $("#boot").remove();
  $("#shell").hidden = false;
  renderTopUser();
  render();
})();
