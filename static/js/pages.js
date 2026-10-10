/* ============================================================
   EWAY Financial Consultancy — per-page rendering logic.
   Each page sets <body data-page="..."> and this file calls the
   matching init function once the DOM (and layout.js) is ready.
   Requires common.js to be loaded first.
   ============================================================ */

function lastPathSegment() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  return decodeURIComponent(parts[parts.length - 1] || "");
}

function qsParam(name) {
  return new URLSearchParams(window.location.search).get(name) || "";
}

/* ======================= HOME ======================= */
function renderHomeServices(services) {
  const list = $("#servicesList");
  if (!list) return;
  list.setAttribute("aria-busy", "false");
  list.innerHTML = services
    .map(
      (s, i) => `
      <a class="service-row reveal" href="/services/${encodeURIComponent(s.id)}">
        <span class="service-num">${String(i + 1).padStart(2, "0")}</span>
        <div class="service-body">
          <h3>${esc(s.title)}</h3>
          <p class="service-tagline">${esc(s.tagline)}</p>
          <p>${esc(s.description)}</p>
          <span class="link-arrow">Learn more <span aria-hidden="true">→</span></span>
        </div>
        ${s.image ? `<div class="service-image"><img src="/static/${s.image}" alt="${esc(s.title)}" loading="lazy" /></div>` : "<div></div>"}
      </a>`
    )
    .join("");
}

function renderHomeTestimonials(testimonials) {
  const grid = $("#testimonialsGrid");
  if (!grid) return;
  grid.setAttribute("aria-busy", "false");
  grid.innerHTML = testimonials
    .map(
      (t) => `
      <figure class="testimonial-card reveal">
        ${
          t.image
            ? `<div class="testimonial-figure"><img src="/static/${t.image}" alt="" loading="lazy" /><figcaption>${esc(t.attribution)}</figcaption></div>`
            : ""
        }
        <blockquote class="testimonial-quote">${esc(t.quote)}</blockquote>
        ${!t.image ? `<figcaption class="testimonial-attr">${esc(t.attribution)}</figcaption>` : ""}
      </figure>`
    )
    .join("");
}

function renderHomeStats(stats) {
  const set = (id, value) => {
    const el = document.querySelector(`[data-stat="${id}"]`);
    if (el) el.textContent = value;
  };
  set("years", `${stats.years_in_business}+`);
  set("auth-full", stats.authorized_capital_formatted);
  set("paid-full", stats.paid_up_capital_formatted);
  set("status", stats.status);
}

function renderHomeArticles(articles) {
  const grid = $("#articlesPreviewGrid");
  if (!grid) return;
  grid.setAttribute("aria-busy", "false");
  grid.innerHTML = articles
    .slice(0, 3)
    .map(
      (a) => `
      <a class="article-card reveal" href="/articles/${encodeURIComponent(a.slug)}">
        ${a.image ? `<div class="article-image"><img src="/static/${a.image}" alt="" loading="lazy" /></div>` : ""}
        <div class="article-body">
          <p class="article-category">${esc(a.category)}</p>
          <h3>${esc(a.title)}</h3>
          <p class="excerpt">${esc(a.excerpt)}</p>
          <div class="article-meta"><span>${esc(a.author)}</span><span>${formatDate(a.date)}</span></div>
        </div>
      </a>`
    )
    .join("");
}

function renderHomeWorkshops(workshops) {
  const grid = $("#workshopsPreviewGrid");
  if (!grid) return;
  grid.setAttribute("aria-busy", "false");
  grid.innerHTML = workshops
    .slice(0, 3)
    .map(
      (w) => `
      <div class="workshop-card reveal">
        ${w.image ? `<div class="workshop-image"><img src="/static/${w.image}" alt="" loading="lazy" /></div>` : ""}
        <div class="workshop-body">
          <span class="workshop-mode">${esc(w.mode)}</span>
          <h3>${esc(w.title)}</h3>
          <p class="desc">${esc(w.description)}</p>
          <p class="workshop-facts">${esc(w.duration)} · ${esc(w.audience)}</p>
        </div>
      </div>`
    )
    .join("");
}

function renderHomeFaqTeaser(faqs) {
  const list = $("#faqTeaserList");
  if (!list) return;
  list.setAttribute("aria-busy", "false");
  list.innerHTML = faqs
    .slice(0, 3)
    .map(
      (f, i) => `
      <details class="faq-item reveal" ${i === 0 ? "open" : ""}>
        <summary>${esc(f.question)}<span class="faq-icon" aria-hidden="true">+</span></summary>
        <p class="faq-answer">${esc(f.answer)}</p>
      </details>`
    )
    .join("");
}

async function initHome() {
  initContactForm();
  try {
    const [company, services, stats, testimonials, faqs, articles, workshops] = await Promise.all([
      fetchJSON("/api/company"),
      fetchJSON("/api/services"),
      fetchJSON("/api/stats"),
      fetchJSON("/api/testimonials"),
      fetchJSON("/api/faq"),
      fetchJSON("/api/articles"),
      fetchJSON("/api/workshops"),
    ]);
    $$("#contactAddress, #heroAddress").forEach((el) => (el.textContent = company.address_line));
    renderHomeStats(stats);
    renderHomeServices(services);
    renderHomeTestimonials(testimonials);
    renderHomeFaqTeaser(faqs);
    renderHomeArticles(articles);
    renderHomeWorkshops(workshops);
  } catch (err) {
    console.error("Failed to load homepage data:", err);
    showToast("Could not load some content from the server. Please refresh.", true);
  }
  initReveals();
}

/* ======================= ABOUT (overview) ======================= */
async function initAbout() {
  initReveals();
}

/* ======================= ABOUT: COMPANY PROFILE ======================= */
function companyDetailRows(c) {
  return [
    ["CIN", esc(c.cin)],
    ["Registration No.", esc(c.registration_number)],
    ["Registrar of Companies", esc(c.roc)],
    ["Date of Incorporation", formatDate(c.incorporated_on)],
    ["Category", esc(c.category)],
    ["Class of Company", `${esc(c.class_of_company)} (${esc(c.sub_category)})`],
    ["Listed Status", esc(c.listed)],
    ["NIC Code / Description", `${esc(c.nic_code)} — ${esc(c.nic_description)}`],
    ["Authorized Capital", `${esc(c.authorized_capital_formatted)} (${esc(c.authorized_capital_short)})`],
    ["Paid-up Capital", `${esc(c.paid_up_capital_formatted)} (${esc(c.paid_up_capital_short)})`],
    ["Registered Office", esc(c.address_line)],
    ["Email", `<a href="mailto:${esc(c.email)}">${esc(c.email)}</a>`],
  ];
}

async function initAboutCompanyProfile() {
  try {
    const [company, compliance] = await Promise.all([fetchJSON("/api/company"), fetchJSON("/api/compliance")]);
    const tbody = $("#companyDetailsTable tbody");
    if (tbody) {
      tbody.innerHTML = companyDetailRows(company)
        .map(([label, value]) => `<tr><th>${label}</th><td>${value}</td></tr>`)
        .join("");
    }
    const compTbody = $("#complianceTable tbody");
    if (compTbody) {
      compTbody.innerHTML = [
        ["Company Status", esc(compliance.company_status)],
        ["Last AGM", formatDate(compliance.last_agm)],
        ["Last Balance Sheet Filed", formatDate(compliance.last_balance_sheet)],
        ["Number of Members", String(compliance.number_of_members)],
        ["Source", esc(compliance.source)],
      ]
        .map(([label, value]) => `<tr><th>${label}</th><td>${value}</td></tr>`)
        .join("");
    }
  } catch (err) {
    console.error(err);
    showToast("Could not load company records.", true);
  }
  initReveals();
}

/* ======================= ABOUT: TEAM ======================= */
async function initAboutTeam() {
  try {
    const team = await fetchJSON("/api/team");
    const grid = $("#teamGrid");
    if (grid) {
      grid.innerHTML = team
        .map(
          (m) => `
          <div class="team-card reveal">
            <div class="team-photo">
              ${
                m.photo
                  ? `<img src="/static/${m.photo}" alt="${esc(m.name)}" loading="lazy" />`
                  : `<div class="team-initials">${esc(initials(m.name))}</div>`
              }
            </div>
            <div class="team-body">
              <h3>${esc(m.name)}</h3>
              <p class="team-role">${esc(m.role)}</p>
              <p class="bio">${esc(m.bio)}</p>
              ${m.email ? `<p class="bio"><a href="mailto:${esc(m.email)}">${esc(m.email)}</a></p>` : ""}
            </div>
          </div>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    showToast("Could not load team profiles.", true);
  }
  initReveals();
}

/* ======================= ABOUT: AWARDS ======================= */
async function initAboutAwards() {
  try {
    const awards = await fetchJSON("/api/awards");
    const grid = $("#awardsGrid");
    if (grid) {
      grid.innerHTML = awards
        .map(
          (a) => `
          <div class="award-card reveal">
            ${a.image ? `<div class="award-image"><img src="/static/${a.image}" alt="${esc(a.title)}" loading="lazy" /></div>` : ""}
            <div class="award-body">
              <span class="award-year">${a.year}</span>
              <h3>${esc(a.title)}</h3>
              <p class="award-issuer">${esc(a.issuer)}</p>
              <p class="desc">${esc(a.description)}</p>
            </div>
          </div>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    showToast("Could not load awards.", true);
  }
  initReveals();
}

/* ======================= ABOUT: MEDIA ======================= */
async function initAboutMedia() {
  try {
    const media = await fetchJSON("/api/media");
    const list = $("#mediaList");
    if (list) {
      list.innerHTML = media
        .map(
          (m) => `
          <article class="media-item reveal">
            <div class="media-meta">
              <span class="media-outlet">${esc(m.outlet)}</span>
              <span class="media-date">${formatDate(m.date)}</span>
            </div>
            <div class="media-body">
              <h3>${esc(m.title)}</h3>
              <p>${esc(m.excerpt)}</p>
            </div>
          </article>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    showToast("Could not load media mentions.", true);
  }
  initReveals();
}

/* ======================= SERVICES (list) ======================= */
async function initServices() {
  try {
    const services = await fetchJSON("/api/services");
    renderHomeServices.call(null, services); // reuse same markup/behaviour
    const list = $("#servicesList");
    if (list) list.removeAttribute("aria-busy");
  } catch (err) {
    console.error(err);
    showToast("Could not load services.", true);
  }
  initReveals();
}

/* ======================= SERVICE DETAIL ======================= */
async function initServiceDetail() {
  const slug = lastPathSegment();
  try {
    const [service, all] = await Promise.all([fetchJSON(`/api/services/${encodeURIComponent(slug)}`), fetchJSON("/api/services")]);
    document.title = `${service.title} — EWAY Financial Consultancy`;
    const titleEl = $("#serviceTitle");
    if (titleEl) titleEl.textContent = service.title;
    const crumbEl = $("#serviceTitleCrumb");
    if (crumbEl) crumbEl.textContent = service.title;
    const taglineEl = $("#serviceTagline");
    if (taglineEl) taglineEl.textContent = service.tagline;
    const descEl = $("#serviceDescription");
    if (descEl) descEl.textContent = service.description;
    const imgWrap = $("#serviceImageWrap");
    if (imgWrap && service.image) {
      imgWrap.innerHTML = `<img src="/static/${service.image}" alt="${esc(service.title)}" />`;
    }
    const related = $("#relatedServices");
    if (related) {
      related.innerHTML = all
        .filter((s) => s.id !== service.id)
        .slice(0, 3)
        .map(
          (s) => `
          <a class="about-tile reveal" href="/services/${encodeURIComponent(s.id)}">
            <h3>${esc(s.title)}</h3>
            <p>${esc(s.tagline)}</p>
            <span class="tile-link link-arrow">View service <span aria-hidden="true">→</span></span>
          </a>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    const titleEl = $("#serviceTitle");
    if (titleEl) titleEl.textContent = "Service not found";
    showToast("That service could not be found.", true);
  }
  initReveals();
}

/* ======================= RESOURCES (PDFs) ======================= */
async function initResources() {
  try {
    const resources = await fetchJSON("/api/resources");
    const grid = $("#resourceGrid");
    if (grid) {
      grid.innerHTML = resources
        .map(
          (r) => `
          <div class="resource-card reveal">
            <div class="resource-icon">PDF</div>
            <div class="resource-body">
              <p class="resource-category">${esc(r.category)}</p>
              <h3>${esc(r.title)}</h3>
              <p>${esc(r.description)} · ${r.pages} page${r.pages === 1 ? "" : "s"}</p>
              <div class="resource-actions">
                <button type="button" class="btn-pill btn-pill-sm" data-view-pdf="/static/${r.file}" data-title="${esc(r.title)}">View PDF</button>
                <a class="btn-outline" href="/static/${r.file}" download>Download</a>
              </div>
            </div>
          </div>`
        )
        .join("");
      grid.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-view-pdf]");
        if (!btn) return;
        openPdfModal(btn.getAttribute("data-view-pdf"), btn.getAttribute("data-title"));
      });
    }
  } catch (err) {
    console.error(err);
    showToast("Could not load the resource library.", true);
  }
  initReveals();
}

/* ======================= WORKSHOPS & TRAINING ======================= */
async function initWorkshops() {
  try {
    const workshops = await fetchJSON("/api/workshops");
    const grid = $("#workshopGrid");
    if (grid) {
      grid.innerHTML = workshops
        .map(
          (w) => `
          <div class="workshop-card reveal">
            ${w.image ? `<div class="workshop-image"><img src="/static/${w.image}" alt="${esc(w.title)}" loading="lazy" /></div>` : ""}
            <div class="workshop-body">
              <span class="workshop-mode">${esc(w.mode)}</span>
              <h3>${esc(w.title)}</h3>
              <p class="desc">${esc(w.description)}</p>
              <p class="workshop-facts">
                <span>Duration: ${esc(w.duration)}</span>
                <span>Audience: ${esc(w.audience)}</span>
                ${w.next_batch ? `<span>Next batch: ${esc(w.next_batch)}</span>` : ""}
              </p>
              <div class="topic-chips">${w.topics.map((t) => `<span>${esc(t)}</span>`).join("")}</div>
              <a class="btn-pill btn-pill-sm" style="margin-top:8px; align-self:flex-start;" href="/contact">Register Interest</a>
            </div>
          </div>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    showToast("Could not load workshops.", true);
  }
  initReveals();
}

/* ======================= ARTICLES (list) ======================= */
async function initArticles() {
  try {
    const articles = await fetchJSON("/api/articles");
    const grid = $("#articleGrid");
    if (grid) {
      grid.classList.add("article-grid");
      grid.innerHTML = articles
        .map(
          (a) => `
          <a class="article-card reveal" href="/articles/${encodeURIComponent(a.slug)}">
            ${a.image ? `<div class="article-image"><img src="/static/${a.image}" alt="" loading="lazy" /></div>` : ""}
            <div class="article-body">
              <p class="article-category">${esc(a.category)}</p>
              <h3>${esc(a.title)}</h3>
              <p class="excerpt">${esc(a.excerpt)}</p>
              <div class="article-meta"><span>By ${esc(a.author)}</span><span>${esc(a.read_minutes)} min read</span></div>
            </div>
          </a>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    showToast("Could not load articles.", true);
  }
  initReveals();
}

/* ======================= ARTICLE DETAIL ======================= */
async function initArticleDetail() {
  const slug = lastPathSegment();
  try {
    const [article, all] = await Promise.all([fetchJSON(`/api/articles/${encodeURIComponent(slug)}`), fetchJSON("/api/articles")]);
    document.title = `${article.title} — EWAY Financial Consultancy`;
    $("#articleCategory") && ($("#articleCategory").textContent = article.category);
    $("#articleTitle") && ($("#articleTitle").textContent = article.title);
    $("#articleMeta") && ($("#articleMeta").textContent = `By ${article.author} · ${formatDate(article.date)} · ${article.read_minutes} min read`);
    const imgWrap = $("#articleImageWrap");
    if (imgWrap && article.image) imgWrap.innerHTML = `<img src="/static/${article.image}" alt="${esc(article.title)}" />`;
    const body = $("#articleBody");
    if (body) body.innerHTML = article.body.map((p) => `<p>${esc(p)}</p>`).join("");

    const more = $("#moreArticles");
    if (more) {
      more.innerHTML = all
        .filter((a) => a.slug !== article.slug)
        .slice(0, 3)
        .map(
          (a) => `
          <a class="article-card reveal" href="/articles/${encodeURIComponent(a.slug)}">
            ${a.image ? `<div class="article-image"><img src="/static/${a.image}" alt="" loading="lazy" /></div>` : ""}
            <div class="article-body">
              <p class="article-category">${esc(a.category)}</p>
              <h3>${esc(a.title)}</h3>
              <p class="excerpt">${esc(a.excerpt)}</p>
            </div>
          </a>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    $("#articleTitle") && ($("#articleTitle").textContent = "Article not found");
    showToast("That article could not be found.", true);
  }
  initReveals();
}

/* ======================= FAQ (full page) ======================= */
async function initFaq() {
  try {
    const faqs = await fetchJSON("/api/faq");
    const list = $("#faqFullList");
    if (list) {
      list.innerHTML = faqs
        .map(
          (f, i) => `
          <details class="faq-item reveal" ${i === 0 ? "open" : ""}>
            <summary>${esc(f.question)}<span class="faq-icon" aria-hidden="true">+</span></summary>
            <p class="faq-answer">${esc(f.answer)}</p>
          </details>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    showToast("Could not load the FAQ.", true);
  }
  initReveals();
}

/* ======================= CONTACT ======================= */
async function initContact() {
  initContactForm();
  try {
    const company = await fetchJSON("/api/company");
    $$("#contactAddress").forEach((el) => (el.textContent = company.address_line));
    $$("#contactEmail").forEach((el) => {
      el.textContent = company.email;
      el.href = `mailto:${company.email}`;
    });
  } catch (err) {
    console.error(err);
  }
  initReveals();
}

/* ======================= SEARCH ======================= */
async function initSearch() {
  const q = qsParam("q");
  const input = $("#searchPageInput");
  if (input) input.value = q;
  const heading = $("#searchHeading");
  const list = $("#searchResultsList");
  const empty = $("#searchEmpty");
  const form = $("#searchPageForm");
  if (form) {
    form.addEventListener("submit", (e) => {
      // let it navigate normally via GET ?q=
    });
  }
  if (!q) {
    if (heading) heading.textContent = "Search EWAY Financial";
    if (empty) {
      empty.hidden = false;
      empty.textContent = "Type a search term above — try “GST”, “loan”, “workshop” or a team member's name.";
    }
    return;
  }
  if (heading) heading.textContent = `Results for “${q}”`;
  try {
    const data = await fetchJSON(`/api/search?q=${encodeURIComponent(q)}`);
    if (!data.results.length) {
      if (empty) {
        empty.hidden = false;
        empty.textContent = `No results found for “${q}”. Try a different term.`;
      }
      return;
    }
    if (empty) empty.hidden = true;
    if (list) {
      list.innerHTML = data.results
        .map(
          (r) => `
          <a class="search-result-item reveal" href="${r.url}">
            <p class="result-type">${esc(r.type)}</p>
            <h3>${esc(r.title)}</h3>
            <p>${esc(r.description)}</p>
          </a>`
        )
        .join("");
    }
  } catch (err) {
    console.error(err);
    showToast("Search is temporarily unavailable.", true);
  }
  initReveals();
}

/* ======================= dispatch ======================= */
const PAGE_INIT = {
  home: initHome,
  about: initAbout,
  "about-company-profile": initAboutCompanyProfile,
  "about-team": initAboutTeam,
  "about-awards": initAboutAwards,
  "about-media": initAboutMedia,
  services: initServices,
  "service-detail": initServiceDetail,
  resources: initResources,
  workshops: initWorkshops,
  articles: initArticles,
  "article-detail": initArticleDetail,
  faq: initFaq,
  contact: initContact,
  search: initSearch,
};

document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;
  const fn = PAGE_INIT[page];
  if (fn) {
    fn();
  } else {
    initReveals();
  }
});