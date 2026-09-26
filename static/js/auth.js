/* ============================================================
   Login / Signup page logic.
   Posts to the FastAPI auth endpoints; on success the browser
   receives a session cookie and we redirect to the homepage.
   ============================================================ */

(function () {
  const form = document.getElementById("authForm");
  const errorEl = document.getElementById("authError");
  if (!form) return;

  const mode = form.dataset.mode;           // "login" | "signup"
  const endpoint = mode === "signup" ? "/api/auth/signup" : "/api/auth/login";
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalLabel = submitBtn.textContent;

  function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = false;
  }

  function clearError() {
    errorEl.textContent = "";
    errorEl.hidden = true;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();

    const payload = {
      email: form.email.value.trim(),
      password: form.password.value,
    };

    // Client-side checks (the server validates again)
    if (mode === "signup") {
      payload.name = form.name.value.trim();
      if (payload.name.length < 2) return showError("Please enter your full name.");
      if (payload.password.length < 8) return showError("Password must be at least 8 characters long.");
      if (form.password.value !== form.confirm.value) return showError("Passwords do not match.");
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Please wait…";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg).join(" ")
          : data.detail || "Something went wrong. Please try again.";
        showError(detail);
        return;
      }
      // Cookie was set by the server. Honour ?next=/some/path (same-site only),
      // otherwise go where the server suggests (staff → /hr, clients → /).
      const next = new URLSearchParams(window.location.search).get("next");
      const safeNext = next && next.startsWith("/") && !next.startsWith("//") ? next : null;
      window.location.href = safeNext || data.redirect || "/";
    } catch {
      showError("Could not reach the server. Please try again.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalLabel;
    }
  });
})();
