# ATO Shield v2

**Fraud analyst workstation for financial institutions.**

Banks connect via API. Every transaction is silently scored by the ML engine. Only flagged transactions surface to analysts — presented as plain-English alerts with full context and clear actions.

---

## Quick Start

```bash
# Start the full stack (PostgreSQL + ATO Shield)
docker-compose up -d

# Run the ML pipeline (train models)
python pipeline/run_all.py

# Start the API + Dashboard
uvicorn api.main:app --reload

# Open the dashboard
# http://localhost:8000/dashboard
```

---

## What is ATO Shield?

ATO Shield is a **fraud analyst workstation** — not a developer tool. Banks integrate via API, and fraud analysts review flagged cases in a professional dashboard.

- **Silent scoring** — Every transaction scored in background
- **Plain-English alerts** — No raw SHAP values, no model names
- **Fast decisions** — BLOCK / FREEZE / ESCALATE / CLEAR in one click
- **Multi-bank** — Complete data isolation per institution
- **Real-time** — WebSocket push notifications for HIGH risk cases

---

## Architecture

```
Bank → POST /api/v1/transaction → ATO Shield API
                                    │
                                    ├── Validates + stores transaction
                                    ├── ML engine scores (XGBoost + Isolation Forest)
                                    ├── Creates case if MEDIUM/HIGH
                                    └── Pushes alert via WebSocket (HIGH)
                                    │
                                    ▼
                          Analyst reviews in dashboard
```

---

## Folder Structure

```
ato-shield-v2/
├── api/                 # FastAPI backend
├── engine/              # ML scoring engine
├── pipeline/            # ML training scripts
├── dashboard/           # Jinja2 frontend
├── store/               # Database layer
├── simulator/           # Dev transaction generator
├── tests/               # pytest suite
├── docker/              # Containerisation
└── data/                # PaySim dataset
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.11+) |
| Dashboard | Jinja2 + HTML/CSS |
| Database | PostgreSQL |
| ML | XGBoost + Isolation Forest + SHAP |
| Real-time | WebSockets |
| Containerisation | Docker + docker-compose |

---

## Deployment

| Stage | App | Database |
|-------|-----|----------|
| Development | Local Docker | PostgreSQL (Docker) |
| Demo | Railway | Supabase |
| Production | DigitalOcean | Managed PostgreSQL |

---

## Documentation

- `ato_shield_v2_master.md` — Master reference document (all decisions)
- `ato_shield_v2_frontend.md` — Frontend design specification

---

**Built for analysts. Invisible technology. Clear decisions.**
