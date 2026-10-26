read



# Cloud CostPilot

Intelligent, **read-only** cloud cost recommendations for Google Cloud.

**Discover → Analyze → Recommend** — Cloud CostPilot never starts, stops, resizes, or deletes your infrastructure.

---

## Problem statement

Cloud bills grow quietly: idle VMs, oversized machine types, and unused capacity. Engineers need a simple way to:

1. Connect a GCP project
2. See Compute Engine inventory
3. Get clear rightsizing / cost advice

…without granting a tool permission to change production.

Cloud CostPilot fills that gap with live discovery, rule-based analysis, and Gemini-backed recommendations.

---

## Features

- Register / log in (session token auth)
- Connect a Google Cloud project
- Live Compute VM discovery (read-only GCP APIs)
- Rule findings (underutilized, rightsizing signals, non-running)
- Gemini recommendations in a dashboard sidebar
- Refresh pipeline on demand / on a schedule
- Single-process demo: FastAPI serves the product UI at `/`

---

## Technology stack

|   |
| - |

Layer

|   |
| - |

Choice

|   |
| - |

API + UI host

|   |
| - |

FastAPI + static UI (`backend/app/static`)

|   |
| - |

Optional SPA

|   |
| - |

Vite + React (`frontend/`)

|   |
| - |

Discovery

|   |
| - |

GCP Compute + Resource Manager (ADC / runtime SA)

|   |
| - |

Analysis

|   |
| - |

Python rule engine (`analyzer/`)

|   |
| - |

Recommendations

|   |
| - |

Google Gemini (`google-generativeai`)

|   |
| - |

Storage

|   |
| - |

Local JSON (demo); BigQuery optional via Terraform

|   |
| - |

Containers

|   |
| - |

Docker + Docker Compose

|   |
| - |

IaC

|   |
| - |

Terraform (APIs, read-only service account)

|   |
| - |

CI

|   |
| - |

GitHub Actions (`.github/workflows/ci.yml`)

---

## Architecture (at a glance)
```text
Discovery (GCP) → Python Analysis (rules) → Gemini Recommendations → Dashboard
```

See **docs/ARCHITECTURE.md** for HLD / LLD diagrams.\
See **docs/E2E_DESIGN.md** for the full design walkthrough.

---

## Repository layout
```text
CloudOps/
├── backend/           # FastAPI app, static UI, tests
├── frontend/          # Optional Vite UI
├── terraform/         # GCP APIs + read-only runtime SA
├── docs/              # Architecture, deployment, API, E2E design
├── docker-compose.yml
├── .env.example       # Template only — never commit real secrets
└── .github/workflows/ci.yml
```

---

## Local setup

**Requirements:** Python 3.11 or 3.12, `gcloud` CLI, Gemini API key ([AI Studio](https://aistudio.google.com/apikey)).
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-gcp.txt
copy ..\.env.example .env          # Linux/macOS: cp ../.env.example .env
# Edit .env → set GEMINI_API_KEY=
gcloud auth application-default login
uvicorn app.main:app --reload --port 8000
```

- **App (use this):** [http://127.0.0.1:8000/](http://127.0.0.1:8000/) &#x20;
- **API docs only:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) &#x20;
- **Health:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Windows shortcut: `run-backend.bat` (after `backend/.env` exists).

### Docker
```bash
# PowerShell
$env:GEMINI_API_KEY="your-key"
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080) (Compose frontend) or [http://localhost:8000](http://localhost:8000) (API + static UI).

### Tests
```bash
cd backend
pytest -q
```

---

## GitHub & live demo

This repository is meant to be published on **GitHub** and deployed as a **live demo** (for reviewers / resume).

### Push to GitHub (first time)

1. Confirm `.env` and secrets are **not** staged (`.gitignore` excludes `.env`).
2. Create an empty GitHub repo (e.g. `Cloud-CostPilot`).
3. From this folder:
```bash
git init
git add .
git commit -m "Initial commit: Cloud CostPilot"
git branch -M main
git remote add origin https://github.com/<YOUR_USER>/Cloud-CostPilot.git
git push -u origin main
```

4. Add GitHub Actions secrets only if you extend CI to deploy (e.g. `GCP_SA_KEY`) — **never** put `GEMINI_API_KEY` in the README.

### Live URL (recommended: Cloud Run, scale-to-zero)

|   |
| - |

Goal

|   |
| - |

Approach

|   |
| - |

Public HTTPS link

|   |
| - |

Deploy backend image to **Cloud Run**

|   |
| - |

Control cost

|   |
| - |

`min-instances=0` (scales to zero when idle)

|   |
| - |

Stop when done

|   |
| - |

Delete the service, or leave idle (near-zero cost)

Full steps: **docs/DEPLOYMENT.md**.

After deploy, add your URL here for reviewers:
```text
Live demo: https://<YOUR-CLOUD-RUN-URL>
```

Screenshots: add under `docs/screenshots/` and link from this section when ready.

### Resume / portfolio tip

Lead with: *read-only FinOps assistant — Discovery → Analysis → Gemini → Dashboard*, plus links to this README, architecture doc, CI workflow, and the live Cloud Run URL.

---

## Security (summary)

- Recommendation-only — no cloud mutate APIs &#x20;
- Secrets via `.env` locally / Secret Manager in cloud — never committed &#x20;
- Runtime identity: viewer-style IAM (see Terraform) &#x20;
- Health check: `GET /health`

Details: **docs/DEPLOYMENT.md**.

---

## Documentation

|   |
| - |

Doc

|   |
| - |

Contents

|   |
| - |

ARCHITECTURE.md

|   |
| - |

HLD + LLD diagrams

|   |
| - |

DEPLOYMENT.md

|   |
| - |

Local, GitHub, Cloud Run, secrets, troubleshooting

|   |
| - |

API.md

|   |
| - |

HTTP endpoints

|   |
| - |

E2E_DESIGN.md

|   |
| - |

Full HLD/LLD design reference