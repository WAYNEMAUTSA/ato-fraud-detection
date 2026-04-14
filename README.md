# ATO Shield v2

**Fraud analyst workstation for financial institutions.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-orange.svg)](https://xgboost.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Banks submit transactions via REST API. An ML engine (XGBoost + Isolation Forest) silently scores each transaction for fraud risk. Flagged transactions become cases that fraud analysts review in a professional dark-themed dashboard — with plain-English explanations and one-click decisions. The technology is invisible. The decision is front and centre.

---

## What It Does

ATO Shield sits between a bank's core system and its fraud team. Every transaction is scored the moment it arrives. Low-risk transactions are logged and forgotten. Medium and high-risk transactions become cases — surfaced to analysts with a plain-English explanation of exactly why the model flagged it, the customer's profile, their recent history, and four possible actions: **BLOCK**, **FREEZE**, **ESCALATE**, or **CLEAR**.

Analysts never see a risk score, a model name, or a SHAP value. They see a story and a decision to make.

---

## Features

- **Silent ML Scoring** — XGBoost + Isolation Forest fusion scores every transaction in the background. 0.982 ROC-AUC. Analysts see none of it.
- **Plain-English Alerts** — SHAP explanations translated into human sentences. "Transfer is 14× larger than this customer's average" — not "AmountVsAverage: 0.847".
- **Real-Time Dashboard** — WebSocket push notifications for HIGH-risk cases. Live stats update every 5 seconds. No refresh needed.
- **Three-Screen Workstation** — Operations Centre (ambient monitoring), Alert Queue (prioritised inbox), Case Investigation (one case, one decision).
- **Five Fraud Types** — ATO (Account Takeover), VEL (Velocity), AMT (Large Amount), NGT (Off-Hours), ANO (Anomalous Pattern).
- **Analyst Profile** — Cases reviewed, accuracy rate, decision breakdown, average review time.
- **Multi-Bank Support** — Complete data isolation per institution. Each bank's analysts see only their own cases.
- **Transaction Simulator** — Generate realistic test traffic from the PaySim dataset at configurable speed and fraud rate.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Seed the Database

```bash
python store/seed.py
```

This creates the database schema, inserts a demo bank and analyst account, and populates sample cases so the dashboard is immediately useful.

### 3. Start the Server

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open the Dashboard

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:8000/dashboard |
| Alert Queue | http://localhost:8000/queue |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

### 5. Send a Test Transaction

```bash
curl -X POST http://localhost:8000/api/v1/transaction \
  -H "Authorization: Bearer ask_live_demo_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_test_001",
    "step": 3,
    "type": "CASH_OUT",
    "amount": 120000,
    "nameOrig": "C_TEST",
    "oldbalanceOrg": 150000,
    "newbalanceOrig": 30000,
    "nameDest": "M_TEST",
    "oldbalanceDest": 0,
    "newbalanceDest": 120000
  }'
```

---

## Demo Credentials

| Credential | Value |
|------------|-------|
| Analyst Email | `analyst@atoshield.demo` |
| Demo API Key | `ask_live_demo_key_12345` |

---

## How It Works

### The Flow

```
Bank's core banking system
        │
        │  POST /api/v1/transaction
        │  Authorization: Bearer {api_key}
        ▼
ATO Shield — Ingestion Layer
        │
        ├── Validates payload (Pydantic)
        ├── Stores raw transaction
        └── Passes to ML engine
        │
        ▼
ML Scoring Engine (silent, runs in background)
        │
        ├── XGBoost scores transaction (0.70 weight)
        ├── Isolation Forest scores transaction (0.30 weight)
        ├── Fuses scores: final = 0.7 × xgb + 0.3 × iso
        └── SHAP generates plain-English reason bullets
        │
        ├── LOW  (< 0.30)  → logged, never shown to analyst
        ├── MED  (≥ 0.30)  → added to alert queue
        └── HIGH (≥ 0.70)  → analyst notified immediately via WebSocket
        │
        ▼
Analyst reviews in dashboard
        │
        └── BLOCK / FREEZE / ESCALATE / CLEAR
                │
                ▼
        Decision sent back to bank via webhook
```

### Integration Model

ATO Shield v2 operates in **monitoring mode** — the bank sends transactions after they clear. If fraud is confirmed, the bank manually reverses. This keeps integration risk low: if ATO Shield has downtime, nothing breaks on the bank's side.

The API is designed so a future **intercept mode** (pre-authorisation) requires no architecture changes — only a configuration switch.

### Multi-Bank Isolation

Every transaction, case, analyst account, and database query is scoped to a `bank_id`. Two banks can run simultaneously with zero data crossover. An analyst at Bank A cannot see Bank B's cases.

---

## ML Engine

### Models

| Component | Detail |
|-----------|--------|
| Dataset | PaySim (6.3M synthetic mobile money transactions) |
| Supervised | XGBoost — 100 trees, depth 6 |
| Unsupervised | Isolation Forest — contamination 0.035 |
| Fusion | `0.7 × xgb_score + 0.3 × iso_score` |
| Balancing | SMOTE on training set only |
| Explainability | SHAP — per transaction, translated to plain English |

### Risk Thresholds

| Level | Score | Action |
|-------|-------|--------|
| HIGH | ≥ 0.70 | Case created, analyst notified via WebSocket immediately |
| MEDIUM | ≥ 0.30 | Case created, added to alert queue |
| LOW | < 0.30 | Logged only, never surfaced to analyst |

### Performance

| Model | Precision | Recall | F1 | ROC-AUC |
|-------|-----------|--------|----|---------|
| Isolation Forest alone | 0.060 | 0.060 | 0.060 | 0.627 |
| XGBoost alone | 0.960 | 0.909 | 0.934 | 0.982 |
| Hybrid 70/30 | 0.960 | 0.909 | 0.934 | 0.982 |

XGBoost carries the classification weight. Isolation Forest acts as a safety net for novel fraud patterns the supervised model hasn't encountered.

### Training the Models (Optional)

The system runs without trained models for UI and API testing. To enable full ML scoring:

```bash
# 1. Download PaySim dataset from Kaggle
#    https://www.kaggle.com/datasets/ealaxi/paysim1
#    Save as: paysim dataset.csv in the project root

# 2. Run the full training pipeline
python pipeline/run_all.py

# 3. Restart the server — models load automatically
uvicorn api.main:app --reload
```

The pipeline runs in sequence: preprocessing → SMOTE balancing → XGBoost training → Isolation Forest training → evaluation. Models save to `engine/models/`.

---

## The Five Fraud Types

| Code | Name | Trigger Scenario |
|------|------|-----------------|
| ATO | Account Takeover | New device + unusual hour + large amount |
| VEL | Velocity Fraud | Multiple rapid transactions, uniform amounts |
| AMT | Large Amount Anomaly | Abnormal size, no historical precedent |
| NGT | Off-Hours Fraud | High-value transaction outside customer's activity window |
| ANO | Anomalous Pattern | Isolation Forest outlier — doesn't fit any known pattern |

---

## Dashboard

### Screen 1 — Operations Centre (`/dashboard`)

The analyst's ambient view. Answers one question: *"Is anything on fire right now?"*

- **Threat Level Indicator** — ALL CLEAR / ELEVATED / CRITICAL, updates live via WebSocket
- **Stat Cards** — Open cases, screened today, protected value (₹ formatted)
- **Transaction Volume Chart** — Bar chart, legitimate vs flagged, 4-hour buckets
- **Recent Flags** — Last 3 open cases with risk badges, amounts, fraud types
- **Today's Breakdown** — Donut chart showing fraud type distribution

### Screen 2 — Alert Queue (`/queue`)

The analyst's inbox. Prioritised by risk score — HIGH cases always appear before MEDIUM.

- Filter by risk level: All / HIGH / MEDIUM
- Sort: Newest / Oldest
- Each row shows: customer name, amount, one-line reason summary, fraud type, time since flagged
- New cases slide in at the top live — no refresh needed
- Quick actions inline: BLOCK / FREEZE / ESCALATE / CLEAR

### Screen 3 — Case Investigation (`/case/{case_id}`)

One case. Full context. One decision.

- Alert header with risk level and fraud type
- Transaction details and customer profile side by side
- **"Why This Was Flagged"** — 3–4 plain-English bullets from SHAP (no numbers, no jargon)
- Last 5 transactions for behavioural context
- Decision panel: BLOCK (red) / FREEZE (amber) / ESCALATE (outlined) / CLEAR (ghost)
- After decision: confirmation toast → auto-advance to next open case

### Analyst Profile

Click your name in the top bar:

- Cases reviewed, accuracy rate, average review time
- Decision breakdown: blocked / frozen / escalated / cleared
- Recent activity with timestamps

---

## Transaction Simulator

Generate realistic test traffic without connecting a real bank system.

```bash
# 50 transactions, 0.3s between each, 20% fraud rate
python simulator/simulator.py --count 50 --speed 0.3 --fraud-rate 0.20

# Fast injection: 200 transactions
python simulator/simulator.py --count 200 --speed 0.1 --fraud-rate 0.25

# Windows batch shortcut
inject.bat 50 0.3 0.20
```

The simulator samples from the PaySim dataset, formats transactions as valid ATO Shield API payloads, and posts them to the ingestion endpoint. Watch the dashboard update live as transactions flow in.

---

## API Reference

### Authentication

All transaction endpoints require a Bearer token:

```
Authorization: Bearer ask_live_demo_key_12345
```

### Endpoints

#### Submit a Transaction
```
POST /api/v1/transaction
```
```json
Request:
{
  "transaction_id": "TXN_001",
  "step": 1,
  "type": "TRANSFER",
  "amount": 120000,
  "nameOrig": "C123456",
  "oldbalanceOrg": 150000,
  "newbalanceOrig": 30000,
  "nameDest": "M789012",
  "oldbalanceDest": 0,
  "newbalanceDest": 120000
}

Response:
{
  "transaction_id": "TXN_001",
  "risk_score": 0.87,
  "risk_level": "HIGH",
  "fraud_type": "ATO",
  "case_id": "case_uuid_here"
}
```

#### List Open Cases
```
GET /api/v1/cases
```
Returns all open cases for the authenticated bank, ordered HIGH → MEDIUM, most recent first.

#### Case Detail
```
GET /api/v1/cases/{case_id}
```
Returns full case including transaction payload, customer profile, and SHAP reason bullets.

#### Submit a Decision
```
POST /api/v1/cases/{case_id}/decision
```
```json
Request:
{ "action": "BLOCK" }

Actions: BLOCK | FREEZE | ESCALATE | CLEAR
```
Stores the decision, updates case status, and fires the bank's webhook if configured.

#### Health Check
```
GET /health
→ { "status": "ok" }
```

### WebSocket

```
WS /ws
```

Connect from the dashboard to receive real-time push alerts. The server broadcasts a JSON message whenever a HIGH or MEDIUM risk case is created. The dashboard uses this to update the threat indicator, alert counter, and queue — without any polling.

---

## Project Structure

```
ato-shield-v2/
│
├── api/                        # FastAPI backend
│   ├── main.py                 # App entry point, WebSocket manager
│   ├── routes/
│   │   ├── transactions.py     # POST /api/v1/transaction
│   │   ├── cases.py            # GET /api/v1/cases
│   │   └── decisions.py        # POST /api/v1/cases/{id}/decision
│   ├── schemas/                # Pydantic request/response models
│   └── middleware/
│       └── auth.py             # API key validation
│
├── engine/                     # ML scoring engine
│   ├── scorer.py               # score(transaction) → risk decision
│   ├── explainer.py            # SHAP → plain-English bullets
│   └── models/                 # Trained .pkl files
│       ├── xgboost.pkl
│       └── isolation_forest.pkl
│
├── pipeline/                   # ML training (run once)
│   ├── run_all.py              # Single command: full pipeline
│   ├── preprocessing.py
│   ├── train_xgboost.py
│   ├── train_isolation_forest.py
│   └── evaluate.py
│
├── dashboard/                  # Jinja2 server-rendered frontend
│   ├── routes.py               # Dashboard page routes
│   ├── templates/
│   │   ├── base.html           # Shared layout, nav, WebSocket client
│   │   ├── login.html
│   │   ├── operations_centre.html
│   │   ├── alert_queue.html
│   │   └── case_investigation.html
│   ├── partials/               # Reusable template fragments
│   └── static/
│       ├── styles.css
│       └── ws_client.js        # WebSocket listener
│
├── store/                      # Database layer
│   ├── database.py             # SQLAlchemy engine + session
│   ├── models.py               # ORM table definitions
│   ├── queries.py              # Reusable query functions
│   └── seed.py                 # Demo data setup
│
├── simulator/                  # Test transaction generator
│   └── simulator.py
│
├── tests/
│   ├── test_scorer.py
│   ├── test_explainer.py
│   ├── test_api.py
│   └── test_decisions.py
│
├── data/
│   ├── raw/                    # PaySim CSV (gitignored)
│   └── processed/              # X_train, X_test, y_train, y_test
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///ato_shield_dev.db` |
| `API_SECRET_KEY` | Secret key for session auth | (set in .env) |
| `BANK_API_KEY` | Demo bank API key | `ask_live_demo_key_12345` |
| `BANK_WEBHOOK_URL` | Where decisions are sent back | (optional) |
| `WS_SECRET` | WebSocket auth secret | (optional) |

---

## Running Tests

```bash
# Full test suite
pytest tests/

# Individual files
pytest tests/test_api.py -v
pytest tests/test_scorer.py -v
pytest tests/test_explainer.py -v
```

Tests cover the scorer (risk level assertions), explainer (plain-English output, no raw numbers), API authentication (401 on bad key), transaction ingestion (rows created in all tables), and decision recording (decision stored, webhook fired).

---

## Docker

```bash
# Build and start full stack
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop
docker-compose -f docker/docker-compose.yml down
```

Docker Compose starts the FastAPI application and PostgreSQL together. The database is initialised automatically on first run.

---

## Deployment

| Stage | Application | Database |
|-------|------------|----------|
| Development | Local uvicorn | SQLite |
| Demo / Pilot | Railway | Supabase free tier |
| Production | DigitalOcean App Platform | Supabase Pro / managed PostgreSQL |

Railway picks up `docker-compose.yml` directly. No deployment configuration changes needed when moving from local to demo.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `"ML engine not available"` | Run `python pipeline/run_all.py` to train models, or use demo mode which bypasses ML |
| `401 Unauthorized` | Check API key is `ask_live_demo_key_12345`, run `python store/seed.py` if not done |
| Database errors | Delete `*.db` files, restart server, run `python store/seed.py` |
| Models not loading | Confirm `engine/models/xgboost.pkl` and `isolation_forest.pkl` exist — train if missing |
| WebSocket not connecting | Confirm server is running on port 8000 and no firewall is blocking WS connections |
| Empty dashboard | Run the simulator for 30 seconds to generate cases: `python simulator/simulator.py --count 30` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.9+) |
| Dashboard | Jinja2 + HTML/CSS + Chart.js |
| Real-Time | WebSockets (FastAPI native) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy |
| ML — Supervised | XGBoost |
| ML — Unsupervised | Isolation Forest (scikit-learn) |
| Explainability | SHAP |
| Data | PaySim dataset |
| Containerisation | Docker + docker-compose |
| Deployment | Railway (demo) / DigitalOcean (prod) |

---

## License

This project is licensed under the MIT License.

---

**Built for analysts. Invisible technology. Clear decisions.**