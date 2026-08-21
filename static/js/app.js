/* ============================================================
   EWAY Financial Consultancy — frontend logic
   All company data is fetched from the FastAPI backend.
   ============================================================ */

document.documentElement.classList.add("js");

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

/* ---------- helpers ---------- */

function formatDate(iso) {
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

function esc(value) {
  const div = document.createElement("div");
  div.textContent = String(value);
  return div.innerHTML;
}

async function fetchJSON(url) {
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`${url} responded with ${res.status}`);
  return res.json();
}

let toastTimer = null;
function showToast(message, isError = false) {
  const toast = $("#toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 4500);
}

/* ---------- renderers ---------- */

function renderCompany(c) {
  // About section — registered details table
  const rows = [
    ["CIN", esc(c.cin)],
    ["Registration No.", esc(c.registration_number)],
    ["Registrar of Companies", esc(c.roc)],
    ["Date of Incorporation", formatDate(c.incorporated_on)],
    ["Category", esc(c.category)],
    ["Class of Company", `${esc(c.class_of_company)} (${esc(c.sub_category)})`],
    ["Stock Exchange", esc(c.listed)],
    ["NIC Code", `${esc(c.nic_code)} — ${esc(c.nic_description)}`],
    ["Authorized Capital", esc(c.authorized_capital_formatted)],
    ["Paid-up Capital", esc(c.paid_up_capital_formatted)],
    ["Registered Address", esc(c.address_line)],
    ["Email", `<a href="mailto:${esc(c.email)}">${esc(c.email)}</a>`],
  ];
  const tbody = $("#detailsTable tbody");
  if (tbody) {
    tbody.innerHTML = rows
      .map(([label, value]) => `<tr><th scope="row">${label}</th><td>${value}</td></tr>`)
      .join("");
  }

  // Contact info + footer
  const addrEl = $("#contactAddress");
  if (addrEl) addrEl.textContent = c.address_line;
  const emailEl = $("#contactEmail");
  if (emailEl) {
    emailEl.textContent = c.email;
    emailEl.href = `mailto:${c.email}`;
  }
  const footerAddr = $("#footerAddress");
  if (footerAddr) footerAddr.textContent = c.address_line;
  const footerEmail = $("#footerEmail");
  if (footerEmail) {
    footerEmail.textContent = c.email;
    footerEmail.href = `mailto:${c.email}`;
  }
  const footerCin = $("#footerCin");
  if (footerCin) footerCin.textContent = `CIN: ${c.cin}`;
}

function renderServices(services) {
  const list = $("#servicesList");
  if (!list) return;
  list.setAttribute("aria-busy", "false");
  list.innerHTML = services
    .map((s, i) => {
      const num = String(i + 1).padStart(2, "0");
      const image = s.image
        ? `<div class="service-image"><img src="/static/${esc(s.image)}" alt="${esc(s.title)}" loading="lazy" /></div>`
        : "";
      return `
      <article class="service-row reveal">
        <div class="service-num" aria-hidden="true">${num}</div>
        <div class="service-body">
          <h3>${esc(s.title)}</h3>
          <p class="service-tagline">${esc(s.tagline)}</p>
          <p>${esc(s.description)}</p>
          <a class="link-arrow" href="#contact">Enquire <span aria-hidden="true">→</span></a>
        </div>
        ${image}
      </article>`;
    })
    .join("");
}

function renderTestimonials(testimonials) {
  const grid = $("#testimonialsGrid");
  if (!grid) return;
  grid.setAttribute("aria-busy", "false");
  const withImage = testimonials.filter((t) => t.image);
  const withoutImage = testimonials.filter((t) => !t.image);
  const cells = [];
  if (withImage.length) {
    const t = withImage[0];
    cells.push(`
      <figure class="testimonial-figure reveal">
        <img src="/static/${esc(t.image)}" alt="Client meeting at EWAY Financial" loading="lazy" />
        <figcaption>Trusted by businesses across Uttar Pradesh</figcaption>
      </figure>`);
  }
  const quotes = withImage.length ? [...withoutImage] : testimonials;
  quotes.forEach((t) => {
    cells.push(`
      <blockquote class="testimonial-card reveal">
        <p class="testimonial-quote">${esc(t.quote)}</p>
        <footer class="testimonial-attr">— ${esc(t.attribution)}</footer>
      </blockquote>`);
  });
  grid.innerHTML = cells.join("");
}

function renderDirectors(directors) {
  const grid = $("#leadersGrid");
  if (!grid) return;
  grid.setAttribute("aria-busy", "false");
  grid.innerHTML = directors
    .map((d) => {
      const avatar = d.photo
        ? `<img class="leader-photo" src="/static/${esc(d.photo)}" alt="Portrait of ${esc(d.name)}" />`
        : `<div class="leader-avatar" aria-hidden="true">${esc(initials(d.name))}</div>`;
      return `
      <article class="leader-card reveal">
        ${avatar}
        <h3>${esc(d.name)}</h3>
        <p class="leader-role">${esc(d.role)}</p>
        <p>${esc(d.bio)}</p>
      </article>`;
    })
    .join("");
}

function renderCompliance(comp) {
  const list = $("#recordsList");
  if (!list) return;
  list.setAttribute("aria-busy", "false");
  const rows = [
    ["Corporate Identification No. (CIN)", esc(comp.cin || "")],
    ["Company Status", `<span class="badge-active">${esc(comp.company_status)}</span>`],
    ["Last Annual General Meeting", formatDate(comp.last_agm)],
    ["Last Filed Balance Sheet", formatDate(comp.last_balance_sheet)],
    ["Registrar of Companies", esc(comp.roc || "")],
    ["Record Source", esc(comp.source)],
  ];
  list.innerHTML = rows
    .map(([label, value]) => `<div class="records-row reveal"><dt>${label}</dt><dd>${value}</dd></div>`)
    .join("");
}

function renderFaq(faqs) {
  const list = $("#faqList");
  if (!list) return;
  list.setAttribute("aria-busy", "false");
  list.innerHTML = faqs
    .map(
      (f) => `
      <details class="faq-item reveal">
        <summary><span>${esc(f.question)}</span><span class="faq-icon" aria-hidden="true">+</span></summary>
        <p class="faq-answer">${esc(f.answer)}</p>
      </details>`
    )
    .join("");
}

function renderStats(stats) {
  const set = (key, value) => $$(`[data-stat="${key}"]`).forEach((el) => (el.textContent = value));
  set("years", `${stats.years_in_business}+`);
  set("auth-full", stats.authorized_capital_formatted);
  set("paid-full", stats.paid_up_capital_formatted);
  set("status", stats.status);
}

/* ---------- navigation ---------- */

function initNav() {
  const header = $("#siteHeader");
  const toggle = $("#navToggle");
  const nav = $("#mainNav");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    $$(".main-nav a").forEach((a) =>
      a.addEventListener("click", () => {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      })
    );
  }

  const onScroll = () => {
    if (header) header.classList.toggle("scrolled", window.scrollY > 24);
    const toTop = $("#toTop");
    if (toTop) toTop.classList.toggle("show", window.scrollY > 640);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const toTop = $("#toTop");
  if (toTop) {
    toTop.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
  }

  // Scroll-spy: highlight the nav link of the section in view
  const links = $$(".main-nav a[href^='#']");
  const byId = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));
  const sections = $$("main section[id]");
  if ("IntersectionObserver" in window && sections.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          links.forEach((a) => a.classList.remove("active"));
          const active = byId.get(entry.target.id);
          if (active) active.classList.add("active");
        });
      },
      { rootMargin: "-40% 0px -55% 0px" }
    );
    sections.forEach((s) => observer.observe(s));
  }
}

/* ---------- contact form ---------- */

function initContactForm() {
  const form = $("#contactForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    // light client-side validation
    let valid = true;
    $$(".form-field input, .form-field textarea", form).forEach((field) => {
      field.classList.toggle("invalid", !field.checkValidity());
      if (!field.checkValidity()) valid = false;
    });
    if (!valid) {
      showToast("Please fill in the required fields correctly.", true);
      return;
    }

    const btn = $("#contactSubmit");
    btn.disabled = true;
    btn.textContent = "Sending…";

    const firstName = form.firstName.value.trim();
    const lastName = form.lastName.value.trim();
    const payload = {
      name: [firstName, lastName].filter(Boolean).join(" "),
      email: form.email.value.trim(),
      phone: null,
      service: form.subject.value.trim() || null,
      message: form.message.value.trim(),
    };

    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
        throw new Error(detail || `Request failed (${res.status})`);
      }
      showToast(data.message || "Message sent! We will be in touch soon.");
      form.reset();
    } catch (err) {
      showToast(`Could not send your message: ${err.message}`, true);
    } finally {
      btn.disabled = false;
      btn.textContent = "Submit";
    }
  });

  // clear invalid state as the user types
  $$(".form-field input, .form-field textarea", form).forEach((field) => {
    field.addEventListener("input", () => field.classList.remove("invalid"));
  });
}

/* ---------- auth (header) ---------- */

function renderGuestAuth() {
  const slot = $("#authSlot");
  if (!slot) return;
  slot.innerHTML = `
    <a href="/login" class="nav-link">Log in</a>
    <a href="/signup" class="btn-pill btn-pill-sm">Sign up</a>`;
}

function renderAuthed(user) {
  const slot = $("#authSlot");
  if (!slot) return;
  const firstName = user.name.trim().split(/\s+/)[0];
  slot.innerHTML = `
    <span class="user-chip" title="${esc(user.email)}">
      <span class="user-avatar" aria-hidden="true">${esc(initials(user.name))}</span>${esc(firstName)}
    </span>
    <a href="#" id="logoutBtn" class="nav-link">Log out</a>`;
  $("#logoutBtn").addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch {
      /* ignore — we redirect regardless */
    }
    window.location.href = "/";
  });
}

async function initAuth() {
  try {
    const res = await fetch("/api/auth/me", { headers: { Accept: "application/json" } });
    if (!res.ok) {
      renderGuestAuth();
      return;
    }
    const data = await res.json();
    renderAuthed(data.user);
  } catch {
    renderGuestAuth();
  }
}

/* ---------- scroll reveal animations ---------- */

function initReveals() {
  const els = $$(".reveal");
  if (!els.length) return;

  if (!("IntersectionObserver" in window)) {
    els.forEach((el) => el.classList.add("revealed"));
    return;
  }

  // stagger siblings that enter the viewport together
  const counters = new Map();
  els.forEach((el) => {
    const parent = el.parentElement;
    const key = parent ? `${parent.tagName}#${parent.id}` : "root";
    const i = counters.get(key) || 0;
    el.style.transitionDelay = `${Math.min(i, 8) * 70}ms`;
    counters.set(key, i + 1);
  });

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("revealed");
        io.unobserve(entry.target);
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
  );
  els.forEach((el) => io.observe(el));
}

/* ---------- init ---------- */

async function init() {
  $("#footerYear").textContent = new Date().getFullYear();
  initNav();
  initContactForm();
  initAuth();

  try {
    const [company, services, directors, compliance, stats, testimonials, faqs] = await Promise.all([
      fetchJSON("/api/company"),
      fetchJSON("/api/services"),
      fetchJSON("/api/directors"),
      fetchJSON("/api/compliance"),
      fetchJSON("/api/stats"),
      fetchJSON("/api/testimonials"),
      fetchJSON("/api/faq"),
    ]);
    // enrich compliance with company fields used in the records section
    compliance.cin = company.cin;
    compliance.roc = company.roc;
    renderCompany(company);
    renderServices(services);
    renderTestimonials(testimonials);
    renderDirectors(directors);
    renderCompliance(compliance);
    renderFaq(faqs);
    renderStats(stats);
  } catch (err) {
    console.error("Failed to load company data:", err);
    showToast("Could not load company data from the server. Please refresh the page.", true);
  }

  initReveals();
}

document.addEventListener("DOMContentLoaded", init);
