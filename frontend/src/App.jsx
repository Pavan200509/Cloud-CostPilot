import { useCallback, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";

function Landing({ onLogin, onRegister }) {
  return (
    <div className="shell landing">
      <nav className="topnav">
        <div className="brand-mark">
          <img src="/costpilot-icon.png" alt="" width="36" height="36" />
          <span>Cloud CostPilot</span>
        </div>
        <div className="nav-actions">
          <button type="button" className="ghost" onClick={onLogin}>
            Log in
          </button>
          <button type="button" className="primary" onClick={onRegister}>
            Get started
          </button>
        </div>
      </nav>
      <section className="hero-plane">
        <div className="hero-copy">
          <h1 className="brand-hero">Cloud CostPilot</h1>
          <p className="hero-line">See what your cloud is costing you — before you change a thing.</p>
          <p className="hero-sub">
            Connect Google Cloud, discover Compute VMs automatically, and get Gemini-backed rightsizing advice.
            Cloud CostPilot never mutates your infrastructure.
          </p>
          <div className="cta-row">
            <button type="button" className="primary large" onClick={onRegister}>
              Create account
            </button>
            <button type="button" className="ghost large" onClick={onLogin}>
              I already have an account
            </button>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true" />
      </section>
    </div>
  );
}

function AuthForm({ mode, onSubmit, onSwitch, busy, error }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const isRegister = mode === "register";

  return (
    <div className="shell auth">
      <div className="auth-panel">
        <div className="brand-mark center">
          <img src="/costpilot-icon.png" alt="" width="40" height="40" />
          <span>Cloud CostPilot</span>
        </div>
        <h2>{isRegister ? "Create your account" : "Welcome back"}</h2>
        <p className="muted">Recommendation-only cloud cost guidance.</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit({ email, password, name });
          }}
        >
          {isRegister && (
            <label>
              Name
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Alex" />
            </label>
          )}
          <label>
            Email
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
            />
          </label>
          <label>
            Password
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
            />
          </label>
          {error && <p className="err">{error}</p>}
          <button type="submit" className="primary wide" disabled={busy}>
            {busy ? "Please wait…" : isRegister ? "Register" : "Log in"}
          </button>
        </form>
        <button type="button" className="linkish" onClick={onSwitch}>
          {isRegister ? "Already registered? Log in" : "Need an account? Register"}
        </button>
      </div>
    </div>
  );
}

function ConnectCloud({ user, onConnected, busy, error, setError }) {
  const [clouds, setClouds] = useState([]);
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState(user?.gcp_project_id || "");
  const [manual, setManual] = useState("");
  const [loadingProjects, setLoadingProjects] = useState(false);

  useEffect(() => {
    api.clouds().then((r) => setClouds(r.clouds || [])).catch(() => {});
  }, []);

  async function loadProjects() {
    setLoadingProjects(true);
    setError("");
    try {
      const r = await api.projects();
      setProjects(r.projects || []);
      if (r.projects?.[0] && !projectId) setProjectId(r.projects[0].project_id);
    } catch (e) {
      setError(e.message);
      setProjects([]);
    } finally {
      setLoadingProjects(false);
    }
  }

  async function connect() {
    const id = (projectId || manual).trim();
    if (!id) {
      setError("Enter or select a GCP project id");
      return;
    }
    await onConnected(id);
  }

  return (
    <div className="shell connect">
      <div className="connect-panel">
        <div className="brand-mark">
          <img src="/costpilot-icon.png" alt="" width="32" height="32" />
          <span>Cloud CostPilot</span>
        </div>
        <h2>Connect your cloud</h2>
        <p className="muted">
          Hi {user?.name || "there"}. Pick Google Cloud, then enter the project Cloud CostPilot should analyze.
          Discovery and Gemini recommendations run automatically — no Execute button.
        </p>
        <div className="cloud-grid">
          {clouds.map((c) => (
            <div key={c.id} className={`cloud-tile ${c.enabled ? "on" : "off"}`}>
              <strong>{c.name}</strong>
              <span>{c.enabled ? "Available" : "Coming soon"}</span>
            </div>
          ))}
        </div>
        <div className="connect-row">
          <button type="button" className="ghost" onClick={loadProjects} disabled={loadingProjects || busy}>
            {loadingProjects ? "Listing…" : "List my GCP projects"}
          </button>
          <span className="hint">Uses ADC locally, or the Cloud Run service account in prod.</span>
        </div>
        {projects.length > 0 && (
          <label>
            Project
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)} disabled={busy}>
              {projects.map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.name} ({p.project_id})
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Or type project id
          <input
            value={manual}
            onChange={(e) => setManual(e.target.value)}
            placeholder="my-gcp-project"
            disabled={busy}
          />
        </label>
        {error && <p className="err">{error}</p>}
        <button type="button" className="primary wide" onClick={connect} disabled={busy}>
          {busy ? "Discovering & analyzing…" : "Connect & analyze"}
        </button>
      </div>
    </div>
  );
}

function Dashboard({ user, onLogout, onReconnect }) {
  const [section, setSection] = useState("vms");
  const [vms, setVms] = useState([]);
  const [findings, setFindings] = useState([]);
  const [recs, setRecs] = useState([]);
  const [projectId, setProjectId] = useState(user?.gcp_project_id || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const load = useCallback(async () => {
    const [r, a, rec] = await Promise.all([api.resources(), api.analysis(), api.recommendations()]);
    setVms(r.sections?.compute?.vms || []);
    setProjectId(r.project_id || user?.gcp_project_id || "");
    setFindings(a.findings || []);
    setRecs(rec.recommendations || []);
  }, [user]);

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [load]);

  async function refresh() {
    setBusy(true);
    setError("");
    setStatus("Refreshing live inventory…");
    try {
      const result = await api.refresh();
      await load();
      setStatus(
        `${result.resource_count} VMs · ${result.finding_count} findings · ${result.recommendation_count} recommendations`
      );
    } catch (e) {
      setError(e.message);
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell dash">
      <aside className="sidebar">
        <div className="brand-mark">
          <img src="/costpilot-icon.png" alt="" width="28" height="28" />
          <span>Cloud CostPilot</span>
        </div>
        <p className="project-chip">{projectId || "No project"}</p>
        <nav className="side-nav">
          <div className="nav-group">Compute</div>
          <button type="button" className={section === "vms" ? "active" : ""} onClick={() => setSection("vms")}>
            VMs
          </button>
          <button type="button" className={section === "findings" ? "active" : ""} onClick={() => setSection("findings")}>
            Findings
          </button>
        </nav>
        <div className="side-foot">
          <button type="button" className="ghost small" onClick={onReconnect}>
            Change project
          </button>
          <button type="button" className="ghost small" onClick={onLogout}>
            Log out
          </button>
        </div>
      </aside>

      <main className="dash-main">
        <header className="dash-head">
          <div>
            <h2>{section === "vms" ? "Compute · VMs" : "Findings"}</h2>
            <p className="muted">Read-only · auto-analyzed with Gemini</p>
          </div>
          <button type="button" className="primary" onClick={refresh} disabled={busy}>
            {busy ? "Working…" : "Refresh"}
          </button>
        </header>
        {status && <p className="ok">{status}</p>}
        {error && <p className="err">{error}</p>}

        {section === "vms" && (
          <div className="table-wrap">
            {vms.length === 0 ? (
              <p className="empty">No VMs yet. Connect a project or hit Refresh.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Zone</th>
                    <th>vCPU</th>
                    <th>Mem GB</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {vms.map((r) => (
                    <tr key={r.resource_id}>
                      <td>{r.name}</td>
                      <td className="mono">{r.machine_type}</td>
                      <td>{r.zone}</td>
                      <td>{r.cpu_cores ?? "—"}</td>
                      <td>{r.memory_gb ?? "—"}</td>
                      <td>
                        <span className="pill">{r.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {section === "findings" && (
          <ul className="find-list">
            {findings.length === 0 ? (
              <li className="empty">No findings yet.</li>
            ) : (
              findings.map((f, i) => (
                <li key={`${f.resource_id}-${f.finding_type}-${i}`}>
                  <span className={`sev ${f.severity}`}>{f.severity}</span>
                  <div>
                    <strong>{f.finding_type}</strong>
                    <p>{f.summary}</p>
                  </div>
                </li>
              ))
            )}
          </ul>
        )}
      </main>

      <aside className="rec-rail">
        <h3>Recommendations</h3>
        <p className="muted small">Gemini · advisory only</p>
        <ul className="rec-list">
          {recs.length === 0 ? (
            <li className="empty">Recommendations appear after connect/refresh.</li>
          ) : (
            recs.map((r, i) => (
              <li key={`${r.resource_id}-${i}`}>
                <strong>{r.resource_name}</strong>
                <span className="provider">{r.provider}</span>
                <p>{r.recommendation}</p>
              </li>
            ))
          )}
        </ul>
      </aside>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("landing");
  const [user, setUser] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) return;
    api
      .me()
      .then((r) => {
        setUser(r.user);
        setView(r.user?.gcp_project_id ? "dashboard" : "connect");
      })
      .catch(() => setToken(""));
  }, []);

  async function handleAuth({ email, password, name }, mode) {
    setBusy(true);
    setError("");
    try {
      const fn = mode === "register" ? api.register : api.login;
      const r = await fn({ email, password, name });
      setToken(r.token);
      setUser(r.user);
      setView(r.user?.gcp_project_id ? "dashboard" : "connect");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleConnect(projectId) {
    setBusy(true);
    setError("");
    try {
      const r = await api.connect({ cloud: "gcp", project_id: projectId });
      setUser(r.user);
      setView("dashboard");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    try {
      await api.logout();
    } catch {
      /* ignore */
    }
    setToken("");
    setUser(null);
    setView("landing");
  }

  if (view === "landing") {
    return (
      <Landing
        onLogin={() => {
          setError("");
          setView("login");
        }}
        onRegister={() => {
          setError("");
          setView("register");
        }}
      />
    );
  }

  if (view === "login" || view === "register") {
    return (
      <AuthForm
        mode={view}
        busy={busy}
        error={error}
        onSubmit={(body) => handleAuth(body, view)}
        onSwitch={() => {
          setError("");
          setView(view === "login" ? "register" : "login");
        }}
      />
    );
  }

  if (view === "connect") {
    return (
      <ConnectCloud
        user={user}
        busy={busy}
        error={error}
        setError={setError}
        onConnected={handleConnect}
      />
    );
  }

  return (
    <Dashboard
      user={user}
      onLogout={logout}
      onReconnect={() => {
        setError("");
        setView("connect");
      }}
    />
  );
}
