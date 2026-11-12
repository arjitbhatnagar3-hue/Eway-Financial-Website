/* ============================================================
   EWAY Financial Consultancy — shared site layout
   Builds the header (logo, 5-item nav with dropdowns, search,
   auth slot), the floating social rail, the scroll-triggered
   mini brand mark, and the footer. Included on every page.
   ============================================================ */

(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function esc(value) {
    const div = document.createElement("div");
    div.textContent = String(value);
    return div.innerHTML;
  }

  function initials(name) {
    return name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0].toUpperCase())
      .join("");
  }

  const path = window.location.pathname.replace(/\/+$/, "") || "/";

  function isActive(href) {
    if (href === "/") return path === "/";
    return path === href || path.startsWith(href + "/");
  }

  /* ---------- Nav data ---------- */
  const NAV = [
    { label: "Home", href: "/" },
    {
      label: "About Us",
      href: "/about",
      children: [
        { label: "Company Profile", href: "/about/company-profile", hint: "Registered MCA details" },
        { label: "Team Profile", href: "/about/team", hint: "Meet the people behind EWAY" },
        { label: "Awards & Recognition", href: "/about/awards", hint: "Milestones we're proud of" },
      ],
    },
    { label: "Services", href: "/services", servicesDropdown: true },
    { label: "FAQ", href: "/faq" },
    { label: "Contact Us", href: "/contact" },
  ];

  function renderDropdown(children) {
    return `<div class="dropdown-panel">${children
      .map(
        (c) =>
          `<a href="${c.href}"><span>${esc(c.label)}</span>${c.hint ? `<small>${esc(c.hint)}</small>` : ""}</a>`
      )
      .join("")}</div>`;
  }

  function navItemHTML(item) {
    const active = isActive(item.href) ? " active" : "";
    if (item.children || item.servicesDropdown) {
      return `
        <div class="nav-item${item.servicesDropdown ? " services-item" : ""}">
          <a href="${item.href}" class="has-caret${active}">${esc(item.label)}<span class="nav-caret" aria-hidden="true"></span></a>
          ${item.children ? renderDropdown(item.children) : '<div class="dropdown-panel services-dropdown-panel"><a href="/services">View all services</a></div>'}
        </div>`;
    }
    return `<div class="nav-item"><a href="${item.href}"${active ? ' class="active"' : ""}>${esc(item.label)}</a></div>`;
  }

  function headerHTML() {
    return `
      <div class="container nav-wrap">
        <a href="/" class="brand" aria-label="EWAY Financial Consultancy — home">
          <span class="brand-word">EWAY</span>
          <span class="brand-sub">Financial Consultancy · Bareilly</span>
        </a>

        <nav class="main-nav" id="mainNav" aria-label="Primary">
          ${NAV.map(navItemHTML).join("")}
          <div class="nav-search">
            <button type="button" class="search-toggle" id="searchToggle" aria-label="Search the site">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="17" height="17"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </button>
            <form class="search-form" id="searchForm" role="search" action="/search" method="get">
              <input type="search" name="q" id="searchInput" placeholder="Search services…" maxlength="120" autocomplete="off" />
              <button type="submit" aria-label="Search">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="14" height="14"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              </button>
            </form>
          </div>
          <span class="nav-divider" aria-hidden="true"></span>
          <div class="nav-auth" id="authSlot" aria-label="Account">
            <a href="/login" class="nav-link">Log in</a>
            <a href="/signup" class="btn-pill btn-pill-sm">Sign up</a>
          </div>
        </nav>

        <button class="nav-toggle" id="navToggle" aria-label="Toggle menu" aria-expanded="false" aria-controls="mainNav">
          <span></span><span></span><span></span>
        </button>
      </div>`;
  }

  // Add verified company profile URLs here when available.
  const activeSocialLinks = [];

  function socialRailHTML() {
    if (!activeSocialLinks.length) return "";
    return `<nav class="social-rail" aria-label="Social media">${activeSocialLinks
      .map((s) => `<a href="${s.href}" aria-label="${esc(s.label)}" target="_blank" rel="noopener">${s.svg}</a>`)
      .join("")}</nav>`;
  }

  function footerHTML() {
    return `
      <div class="container footer-grid">
        <div class="footer-brand">
          <span class="brand-word">EWAY</span>
          <span class="brand-sub brand-sub-light">Financial Consultancy</span>
          <p>
            A private financial consultancy based in Bareilly, Uttar Pradesh —
            serving businesses with advisory, compliance, taxation and credit
            solutions since 2009.
          </p>
          <p class="footer-cin" id="footerCin">CIN: U74900UP2009PTC037001</p>
        </div>

        <div class="footer-col">
          <h4>About Us</h4>
          <ul>
            <li><a href="/about">Overview</a></li>
            <li><a href="/about/company-profile">Company Profile</a></li>
            <li><a href="/about/team">Team Profile</a></li>
            <li><a href="/about/awards">Awards &amp; Recognition</a></li>
          </ul>
        </div>

        <div class="footer-col">
          <h4>Services</h4>
          <ul id="footerServices"></ul>
        </div>

        <div class="footer-col">
          <h4>Explore</h4>
          <ul>
            <li><a href="/faq">FAQ</a></li>
            <li><a href="/contact">Contact Us</a></li>
            <li><a href="/hr">Staff Login · HR Portal</a></li>
          </ul>
        </div>

        <div class="footer-col">
          <h4>Reach Us</h4>
          <ul class="footer-contact">
            <li id="footerAddress">Bareilly, Uttar Pradesh, India</li>
            <li><a href="mailto:sanjaybhatnagar@gmail.com" id="footerEmail">sanjaybhatnagar@gmail.com</a></li>
            <li>Mon – Sat · 10:00 AM – 6:00 PM IST</li>
          </ul>
          ${activeSocialLinks.length ? `<div class="social-row" aria-label="Social media">
            ${activeSocialLinks.map((s) => `<a href="${s.href}" aria-label="${esc(s.label)}" target="_blank" rel="noopener">${s.svg}</a>`).join("")}
          </div>` : ""}
        </div>
      </div>

      <div class="container footer-wordmark" aria-hidden="true">EWAY Financial</div>

      <div class="container footer-bottom">
        <p>© <span id="footerYear">2026</span> EWAY Financial Consultancy Private Limited. All rights reserved.</p>
        <p>Built with <span class="accent">FastAPI</span> · <a href="/docs" target="_blank" rel="noopener">API Docs</a></p>
      </div>`;
  }

  /* ---------- Auth slot ---------- */
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
      ${user.is_staff ? '<a href="/hr" class="nav-link">HR Portal</a>' : ""}
      <span class="user-chip" title="${esc(user.email)}">
        <span class="user-avatar" aria-hidden="true">${esc(initials(user.name))}</span>${esc(firstName)}
      </span>
      <a href="#" id="logoutBtn" class="nav-link">Log out</a>`;
    $("#logoutBtn").addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        await fetch("/api/auth/logout", { method: "POST" });
      } catch {
        /* ignore */
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

  /* ---------- Services dropdown (populated from API) ---------- */
  async function hydrateServicesDropdown() {
    const panel = $(".services-dropdown-panel");
    if (!panel) return;
    try {
      const res = await fetch("/api/services", { headers: { Accept: "application/json" } });
      if (!res.ok) return;
      const services = await res.json();
      panel.innerHTML =
        services
          .map((s) => `<a href="/services/${encodeURIComponent(s.id)}"><span>${esc(s.title)}</span><small>${esc(s.tagline)}</small></a>`)
          .join("") + '<a class="dropdown-all" href="/services">View all services →</a>';
    } catch {
      /* keep fallback link */
    }
  }

  async function hydrateFooterServices() {
    const list = $("#footerServices");
    if (!list) return;
    try {
      const res = await fetch("/api/services", { headers: { Accept: "application/json" } });
      if (!res.ok) return;
      const services = await res.json();
      list.innerHTML = services.map((s) => `<li><a href="/services/${encodeURIComponent(s.id)}">${esc(s.title)}</a></li>`).join("");
    } catch {
      /* ignore */
    }
  }

  /* ---------- Behaviours ---------- */
  function initNavToggle() {
    const toggle = $("#navToggle");
    const nav = $("#mainNav");
    if (!toggle || !nav) return;
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    $$(".main-nav > .nav-item > a:not(.has-caret)").forEach((a) =>
      a.addEventListener("click", () => {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      })
    );
    // On mobile, tapping a caret toggles the dropdown instead of navigating away.
    $$(".nav-item > a.has-caret").forEach((a) => {
      a.addEventListener("click", (e) => {
        if (window.innerWidth <= 820) {
          e.preventDefault();
          a.parentElement.classList.toggle("open");
        }
      });
    });
  }

  function initSearch() {
    const toggleBtn = $("#searchToggle");
    const form = $("#searchForm");
    const input = $("#searchInput");
    if (!toggleBtn || !form || !input) return;
    toggleBtn.addEventListener("click", () => {
      const open = form.classList.toggle("open");
      if (open) input.focus();
    });
    document.addEventListener("click", (e) => {
      if (!form.contains(e.target) && e.target !== toggleBtn && form.classList.contains("open") && !input.value) {
        form.classList.remove("open");
      }
    });
    // keep plain GET submit (works without JS too); normal navigation happens.
  }

  function initScroll() {
    const header = $(".site-header");
    const miniLogo = $("#miniLogo");
    const onScroll = () => {
      const scrolled = window.scrollY > 24;
      if (header) header.classList.toggle("scrolled", scrolled);
      if (miniLogo) miniLogo.classList.toggle("show", window.scrollY > 320);
      const toTop = $("#toTop");
      if (toTop) toTop.classList.toggle("show", window.scrollY > 640);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  function mountMiniLogo() {
    if ($("#miniLogo")) return;
    const a = document.createElement("a");
    a.href = "/";
    a.id = "miniLogo";
    a.className = "mini-logo";
    a.setAttribute("aria-label", "EWAY Financial Consultancy — back to home");
    a.textContent = "E";
    document.body.appendChild(a);
  }

  function mountSocialRail() {
    if (!activeSocialLinks.length || $(".social-rail")) return;
    const div = document.createElement("div");
    div.innerHTML = socialRailHTML();
    document.body.appendChild(div.firstElementChild);
  }

  function mountToTop() {
    if ($("#toTop")) return;
    const btn = document.createElement("button");
    btn.id = "toTop";
    btn.className = "to-top";
    btn.setAttribute("aria-label", "Back to top");
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><polyline points="18 15 12 9 6 15"/></svg>';
    btn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
    document.body.appendChild(btn);
  }

  function mountToast() {
    if ($("#toast")) return;
    const div = document.createElement("div");
    div.id = "toast";
    div.className = "toast";
    div.setAttribute("role", "status");
    div.setAttribute("aria-live", "polite");
    document.body.appendChild(div);
  }

  function init() {
    const headerSlot = $("#site-header");
    const footerSlot = $("#site-footer");
    if (headerSlot) {
      headerSlot.outerHTML = `<header class="site-header" id="siteHeader">${headerHTML()}</header>`;
    }
    if (footerSlot) {
      footerSlot.outerHTML = `<footer class="site-footer">${footerHTML()}</footer>`;
    }
    const yearEl = $("#footerYear");
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    mountMiniLogo();
    mountSocialRail();
    mountToTop();
    mountToast();

    initNavToggle();
    initSearch();
    initScroll();
    initAuth();
    hydrateServicesDropdown();
    hydrateFooterServices();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.EwayLayout = { esc, initials };
})();
