/* ============================================================
   EWAY Financial Consultancy — shared helpers used across pages.
   Load after layout.js, before page-specific scripts.
   ============================================================ */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

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

/* ---------- scroll reveal animations ---------- */
function initReveals() {
  const els = $$(".reveal");
  if (!els.length) return;

  if (!("IntersectionObserver" in window)) {
    els.forEach((el) => el.classList.add("revealed"));
    return;
  }

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

/* ---------- contact form (used on homepage + /contact) ---------- */
function initContactForm() {
  const form = $("#contactForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    let valid = true;
    $$(".form-field input, .form-field textarea", form).forEach((field) => {
      field.classList.toggle("invalid", !field.checkValidity());
      if (!field.checkValidity()) valid = false;
    });
    if (!valid) {
      showToast("Please fill in the required fields correctly.", true);
      return;
    }

    const btn = $("#contactSubmit", form);
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

  $$(".form-field input, .form-field textarea", form).forEach((field) => {
    field.addEventListener("input", () => field.classList.remove("invalid"));
  });
}

/* ---------- PDF modal viewer (resources page) ---------- */
function openPdfModal(url, title) {
  let modal = $("#pdfModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "pdfModal";
    modal.className = "pdf-modal";
    modal.innerHTML = `
      <div class="pdf-modal-dialog">
        <div class="pdf-modal-header">
          <h3 id="pdfModalTitle"></h3>
          <button type="button" class="pdf-modal-close" id="pdfModalClose" aria-label="Close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="16" height="16"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <iframe id="pdfModalFrame" title="PDF preview"></iframe>
      </div>`;
    document.body.appendChild(modal);
    $("#pdfModalClose", modal).addEventListener("click", closePdfModal);
    modal.addEventListener("click", (e) => {
      if (e.target === modal) closePdfModal();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closePdfModal();
    });
  }
  $("#pdfModalTitle", modal).textContent = title || "Document preview";
  $("#pdfModalFrame", modal).src = url;
  modal.classList.add("open");
  document.body.style.overflow = "hidden";
}

function closePdfModal() {
  const modal = $("#pdfModal");
  if (!modal) return;
  modal.classList.remove("open");
  document.body.style.overflow = "";
  const frame = $("#pdfModalFrame", modal);
  if (frame) frame.src = "";
}