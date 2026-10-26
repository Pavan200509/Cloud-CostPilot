(() => {
  const TOKEN_KEY = "costpilot_token";
  const root = document.getElementById("app");

  const state = {
    view: "landing",
    user: null,
    busy: false,
    busyMsg: "",
    error: "",
    status: "",
    clouds: [],
    projects: [],
    projectId: "",
    manualProject: "",
    section: "vms",
    vms: [],
    findings: [],
    recs: [],
    authMode: "register",
    form: { name: "", email: "", password: "" },
  };

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || "";
  }

  function setToken(token) {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  }

  async function api(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(path, { ...options, headers });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const detail = body.detail;
      const msg = Array.isArray(detail)
        ? detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
        : detail || `Request failed (${res.status})`;
      const err = new Error(msg);
      err.status = res.status;
      throw err;
    }
    return res.json();
  }

  function esc(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function brand(size = 36) {
    return `<div class="brand-mark"><img src="/assets/costpilot-icon.png" alt="" width="${size}" height="${size}" /><span>Cloud CostPilot</span></div>`;
  }

  function busyOverlay() {
    if (!state.busy) return "";
    return `<div class="loading-overlay"><div class="loading-card"><div class="spinner"></div><p>${esc(state.busyMsg || "Working…")}</p></div></div>`;
  }

  function renderLanding() {
    return `
      <div class="shell landing">
        <nav class="topnav">
          ${brand()}
          <div class="nav-actions">
            <button type="button" class="ghost" data-go="login">Log in</button>
            <button type="button" class="primary" data-go="register">Get started</button>
          </div>
        </nav>
        <section class="hero-plane">
          <div class="hero-copy">
            <h1 class="brand-hero">Cloud CostPilot</h1>
            <p class="hero-line">See what your cloud is costing you — before you change a thing.</p>
            <p class="hero-sub">
              Connect Google Cloud, discover Compute VMs automatically, and get Gemini-backed rightsizing advice.
              Cloud CostPilot never mutates your infrastructure.
            </p>
            <div class="cta-row">
              <button type="button" class="primary large" data-go="register">Create account</button>
              <button type="button" class="ghost large" data-go="login">I already have an account</button>
            </div>
          </div>
          <div class="hero-visual" aria-hidden="true"></div>
        </section>
      </div>`;
  }

  function renderAuth() {
    const isRegister = state.authMode === "register";
    return `
      <div class="shell auth">
        <div class="auth-panel">
          <div class="brand-mark center"><img src="/assets/costpilot-icon.png" alt="" width="40" height="40" /><span>Cloud CostPilot</span></div>
          <h2>${isRegister ? "Create your account" : "Welcome back"}</h2>
          <p class="muted">Recommendation-only cloud cost guidance.</p>
          <form id="auth-form">
            ${
              isRegister
                ? `<label>Name<input name="name" value="${esc(state.form.name)}" placeholder="Alex" /></label>`
                : ""
            }
            <label>Email<input name="email" type="email" required value="${esc(state.form.email)}" placeholder="you@company.com" /></label>
            <label>Password<input name="password" type="password" required minlength="6" value="${esc(state.form.password)}" placeholder="At least 6 characters" /></label>
            ${state.error ? `<p class="err">${esc(state.error)}</p>` : ""}
            <button type="submit" class="primary wide" ${state.busy ? "disabled" : ""}>
              ${state.busy ? "Please wait…" : isRegister ? "Register" : "Log in"}
            </button>
          </form>
          <button type="button" class="linkish" data-switch-auth>
            ${isRegister ? "Already registered? Log in" : "Need an account? Register"}
          </button>
        </div>
      </div>${busyOverlay()}`;
  }

  function renderConnect() {
    const cloudTiles = (state.clouds.length
      ? state.clouds
      : [
          { id: "gcp", name: "Google Cloud", enabled: true },
          { id: "aws", name: "Amazon Web Services", enabled: false },
          { id: "azure", name: "Microsoft Azure", enabled: false },
        ]
    )
      .map(
        (c) => `
        <div class="cloud-tile ${c.enabled ? "on" : "off"}">
          <strong>${esc(c.name)}</strong>
          <span>${c.enabled ? "Available" : "Coming soon"}</span>
        </div>`
      )
      .join("");

    const projectOptions = state.projects
      .map(
        (p) =>
          `<option value="${esc(p.project_id)}" ${p.project_id === state.projectId ? "selected" : ""}>${esc(p.name)} (${esc(p.project_id)})</option>`
      )
      .join("");

    return `
      <div class="shell connect">
        <div class="connect-panel">
          ${brand(32)}
          <h2>Connect your cloud</h2>
          <p class="muted">
            Hi ${esc(state.user?.name || "there")}. Pick Google Cloud, then enter the project Cloud CostPilot should analyze.
            Discovery and Gemini recommendations run automatically — no Execute button.
          </p>
          <div class="cloud-grid">${cloudTiles}</div>
          <div class="connect-row">
            <button type="button" class="ghost" id="list-projects" ${state.busy ? "disabled" : ""}>List my GCP projects</button>
            <span class="hint">Uses ADC locally, or the Cloud Run service account in prod.</span>
          </div>
          ${
            state.projects.length
              ? `<label>Project<select id="project-select">${projectOptions}</select></label>`
              : ""
          }
          <label>Or type project id
            <input id="manual-project" value="${esc(state.manualProject)}" placeholder="my-gcp-project" ${state.busy ? "disabled" : ""} />
          </label>
          ${state.error ? `<p class="err">${esc(state.error)}</p>` : ""}
          <button type="button" class="primary wide" id="connect-btn" ${state.busy ? "disabled" : ""}>
            ${state.busy ? "Discovering & analyzing…" : "Connect & analyze"}
          </button>
        </div>
      </div>${busyOverlay()}`;
  }

  function renderDashboard() {
    const vmsRows = state.vms.length
      ? state.vms
          .map(
            (r) => `
          <tr>
            <td>${esc(r.name)}</td>
            <td class="mono">${esc(r.machine_type)}</td>
            <td>${esc(r.zone)}</td>
            <td>${r.cpu_cores ?? "—"}</td>
            <td>${r.memory_gb ?? "—"}</td>
            <td><span class="pill">${esc(r.status)}</span></td>
          </tr>`
          )
          .join("")
      : "";

    const findings = state.findings.length
      ? state.findings
          .map(
            (f) => `
          <li>
            <span class="sev ${esc(f.severity || "info")}">${esc(f.severity || "info")}</span>
            <div>
              <strong>${esc(f.finding_type)}</strong>
              <p>${esc(f.summary)}</p>
            </div>
          </li>`
          )
          .join("")
      : `<li class="empty">No findings yet.</li>`;

    const recs = state.recs.length
      ? state.recs
          .map(
            (r) => `
          <li>
            <strong>${esc(r.resource_name)}</strong>
            <span class="provider">${esc(r.provider)}</span>
            <p>${esc(r.recommendation)}</p>
          </li>`
          )
          .join("")
      : `<li class="empty">Recommendations appear after connect/refresh.</li>`;

    const main =
      state.section === "vms"
        ? `<div class="table-wrap">${
            state.vms.length
              ? `<table>
                  <thead><tr><th>Name</th><th>Type</th><th>Zone</th><th>vCPU</th><th>Mem GB</th><th>Status</th></tr></thead>
                  <tbody>${vmsRows}</tbody>
                </table>`
              : `<p class="empty">No VMs yet. Connect a project or hit Refresh.</p>`
          }</div>`
        : `<ul class="find-list">${findings}</ul>`;

    return `
      <div class="shell dash">
        <aside class="sidebar">
          ${brand(28)}
          <p class="project-chip">${esc(state.projectId || state.user?.gcp_project_id || "No project")}</p>
          <nav class="side-nav">
            <div class="nav-group">Compute</div>
            <button type="button" class="${state.section === "vms" ? "active" : ""}" data-section="vms">VMs</button>
            <button type="button" class="${state.section === "findings" ? "active" : ""}" data-section="findings">Findings</button>
          </nav>
          <div class="side-foot">
            <button type="button" class="ghost small" data-go="connect">Change project</button>
            <button type="button" class="ghost small" id="logout-btn">Log out</button>
          </div>
        </aside>
        <main class="dash-main">
          <header class="dash-head">
            <div>
              <h2>${state.section === "vms" ? "Compute · VMs" : "Findings"}</h2>
              <p class="muted">Read-only · auto-analyzed with Gemini</p>
            </div>
            <button type="button" class="primary" id="refresh-btn" ${state.busy ? "disabled" : ""}>
              ${state.busy ? "Working…" : "Refresh"}
            </button>
          </header>
          ${state.status ? `<p class="ok">${esc(state.status)}</p>` : ""}
          ${state.error ? `<p class="err">${esc(state.error)}</p>` : ""}
          ${main}
        </main>
        <aside class="rec-rail">
          <h3>Recommendations</h3>
          <p class="muted small">Gemini · advisory only</p>
          <ul class="rec-list">${recs}</ul>
        </aside>
      </div>${busyOverlay()}`;
  }

  function render() {
    let html = "";
    if (state.view === "landing") html = renderLanding();
    else if (state.view === "login" || state.view === "register") {
      state.authMode = state.view;
      html = renderAuth();
    } else if (state.view === "connect") html = renderConnect();
    else html = renderDashboard();
    root.innerHTML = html;
    bind();
  }

  async function loadDashboardData() {
    const [r, a, rec] = await Promise.all([
      api("/resources"),
      api("/analysis"),
      api("/recommendations"),
    ]);
    state.vms = r.sections?.compute?.vms || [];
    state.projectId = r.project_id || state.user?.gcp_project_id || "";
    state.findings = a.findings || [];
    state.recs = rec.recommendations || [];
  }

  function bind() {
    root.querySelectorAll("[data-go]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.error = "";
        state.view = btn.getAttribute("data-go");
        render();
      });
    });

    const switchAuth = root.querySelector("[data-switch-auth]");
    if (switchAuth) {
      switchAuth.addEventListener("click", () => {
        state.error = "";
        state.view = state.view === "login" ? "register" : "login";
        render();
      });
    }

    const authForm = root.querySelector("#auth-form");
    if (authForm) {
      authForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(authForm);
        state.form = {
          name: String(fd.get("name") || ""),
          email: String(fd.get("email") || ""),
          password: String(fd.get("password") || ""),
        };
        state.busy = true;
        state.busyMsg = state.view === "register" ? "Creating account…" : "Signing in…";
        state.error = "";
        render();
        try {
          const path = state.view === "register" ? "/auth/register" : "/auth/login";
          const body = {
            email: state.form.email,
            password: state.form.password,
            ...(state.view === "register" ? { name: state.form.name } : {}),
          };
          const r = await api(path, { method: "POST", body: JSON.stringify(body) });
          setToken(r.token);
          state.user = r.user;
          state.view = r.user?.gcp_project_id ? "dashboard" : "connect";
          if (state.view === "dashboard") await loadDashboardData();
          else {
            try {
              const c = await api("/clouds");
              state.clouds = c.clouds || [];
            } catch {
              /* ignore */
            }
          }
        } catch (err) {
          state.error = err.message;
        } finally {
          state.busy = false;
          state.busyMsg = "";
          render();
        }
      });
    }

    const listBtn = root.querySelector("#list-projects");
    if (listBtn) {
      listBtn.addEventListener("click", async () => {
        state.busy = true;
        state.busyMsg = "Listing GCP projects…";
        state.error = "";
        render();
        try {
          const r = await api("/projects");
          state.projects = r.projects || [];
          if (state.projects[0] && !state.projectId) state.projectId = state.projects[0].project_id;
        } catch (err) {
          state.error = err.message;
          state.projects = [];
        } finally {
          state.busy = false;
          state.busyMsg = "";
          render();
        }
      });
    }

    const projectSelect = root.querySelector("#project-select");
    if (projectSelect) {
      projectSelect.addEventListener("change", () => {
        state.projectId = projectSelect.value;
      });
    }

    const manual = root.querySelector("#manual-project");
    if (manual) {
      manual.addEventListener("input", () => {
        state.manualProject = manual.value;
      });
    }

    const connectBtn = root.querySelector("#connect-btn");
    if (connectBtn) {
      connectBtn.addEventListener("click", async () => {
        const id = (state.projectId || state.manualProject).trim();
        if (!id) {
          state.error = "Enter or select a GCP project id";
          render();
          return;
        }
        state.busy = true;
        state.busyMsg = "Discovering VMs & generating recommendations…";
        state.error = "";
        render();
        try {
          const r = await api("/connect", {
            method: "POST",
            body: JSON.stringify({ cloud: "gcp", project_id: id }),
          });
          state.user = r.user;
          state.projectId = id;
          await loadDashboardData();
          const p = r.pipeline || {};
          state.status = `${p.resource_count ?? state.vms.length} VMs · ${p.finding_count ?? state.findings.length} findings · ${p.recommendation_count ?? state.recs.length} recommendations`;
          state.view = "dashboard";
        } catch (err) {
          state.error = err.message;
        } finally {
          state.busy = false;
          state.busyMsg = "";
          render();
        }
      });
    }

    root.querySelectorAll("[data-section]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.section = btn.getAttribute("data-section");
        render();
      });
    });

    const refreshBtn = root.querySelector("#refresh-btn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", async () => {
        state.busy = true;
        state.busyMsg = "Refreshing live inventory…";
        state.error = "";
        render();
        try {
          const result = await api("/refresh", { method: "POST" });
          await loadDashboardData();
          state.status = `${result.resource_count} VMs · ${result.finding_count} findings · ${result.recommendation_count} recommendations`;
        } catch (err) {
          state.error = err.message;
          state.status = "";
        } finally {
          state.busy = false;
          state.busyMsg = "";
          render();
        }
      });
    }

    const logoutBtn = root.querySelector("#logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        try {
          await api("/auth/logout", { method: "POST" });
        } catch {
          /* ignore */
        }
        setToken("");
        state.user = null;
        state.view = "landing";
        state.error = "";
        state.status = "";
        render();
      });
    }
  }

  async function boot() {
    if (!getToken()) {
      render();
      return;
    }
    try {
      const r = await api("/auth/me");
      state.user = r.user;
      if (r.user?.gcp_project_id) {
        state.view = "dashboard";
        await loadDashboardData();
      } else {
        state.view = "connect";
        try {
          const c = await api("/clouds");
          state.clouds = c.clouds || [];
        } catch {
          /* ignore */
        }
      }
    } catch {
      setToken("");
      state.view = "landing";
    }
    render();
  }

  boot();
})();