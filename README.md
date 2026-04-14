# ATO Shield v2

**Fraud analyst workstation for financial institutions.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Banks submit transactions via REST API. An ML engine (XGBoost + Isolation Forest) silently scores each transaction for fraud risk. Flagged transactions become cases that fraud analysts review in a professional dashboard with plain-English explanations and one-click decisions.

---

## Features

- **Silent ML Scoring** — Every transaction scored in background (XGBoost + Isolation Forest fusion)
- **Plain-English Alerts** — SHAP-powered explanations, no raw model outputs
- **Real-Time Dashboard** — WebSocket push notifications for HIGH-risk cases, live stats updates every 5 seconds
- **Analyst Profile** — Track your performance metrics (cases reviewed, accuracy rate, decision breakdown)
- **Multi-Bank Support** — Complete data isolation per institution
- **Fast Decisions** — BLOCK / FREEZE / ESCALATE / CLEAR in one click
- **Transaction Simulator** — Generate realistic test traffic from PaySim dataset

---

## Quick Start

### 1. Installation

```bash
# Clone and install dependencies
pip install -r requirements.txt

# Seed database with demo data
python store/seed.py
```

### 2. Start the Server

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access the System

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:8000/dashboard |
| **API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |

### 4. Test with a Transaction

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

## Architecture

```
Bank → POST /api/v1/transaction → ATO Shield API
                                    │
                                    ├── Validate + store transaction
                                    ├── ML engine scores (XGBoost + Isolation Forest)
                                    ├── Create case if MEDIUM/HIGH risk
                                    └── Push alert via WebSocket (HIGH risk)
                                    │
                                    ▼
                          Analyst reviews in dashboard
```

### Project Structure

```
ato-fraud-detection/
├── api/                 # FastAPI backend (routes, middleware, schemas)
├── engine/              # ML scoring engine (scorer, SHAP explainer)
├── pipeline/            # ML training pipeline
├── dashboard/           # Jinja2 frontend templates & static assets
├── store/               # Database layer (SQLAlchemy models, queries)
├── simulator/           # Transaction simulator for testing
├── tests/               # pytest test suite
├── docker/              # Docker & docker-compose configuration
└── data/                # Dataset & processed data artifacts
```

---

## ML Model Training (Optional)

The system works without ML models for testing UI/API, but to enable fraud scoring:

1. **Get PaySim Dataset** — Download from [Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1)
2. **Place CSV** — Save as `paysim dataset.csv` in project root
3. **Train Models** — Run `python pipeline/run_all.py`
4. **Restart Server** — Models load automatically on startup

---

## Running Tests

```bash
# Run the pytest suite
pytest tests/

# Or run individual test files
pytest tests/test_api.py -v
```

## Inject Transactions (Terminal)

```bash
# Quick inject: 50 transactions, 0.3s speed, 20% fraud rate
inject.bat 50 0.3 0.20

# Or use the Python command directly:
python simulator/simulator.py --count 50 --speed 0.3 --fraud-rate 0.20

# Fast injection: 200 transactions, 0.1s speed, 25% fraud rate
python simulator/simulator.py --count 200 --speed 0.1 --fraud-rate 0.25
```

Watch the dashboard auto-refresh every 3 seconds as transactions flow in.

---

## Demo Credentials

| Credential | Value |
|------------|-------|
| **Demo API Key** | `ask_live_demo_key_12345` |
| **Analyst Email** | `analyst@atoshield.demo` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **API** | FastAPI (Python 3.9+) |
| **Dashboard** | Jinja2 + HTML/CSS/JS + Chart.js |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **ML Engine** | XGBoost + Isolation Forest + SHAP |
| **Real-Time** | WebSockets |
| **Containerisation** | Docker + docker-compose |

---

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///ato_shield_dev.db` |
| `API_SECRET_KEY` | Secret key for authentication | (demo key provided) |
| `BANK_API_KEY` | Bank API key for testing | `ask_live_demo_key_12345` |
| `BANK_WEBHOOK_URL` | Webhook URL for bank notifications | (optional) |
| `WS_SECRET` | WebSocket secret for real-time alerts | (optional) |

---

## Deployment

| Stage | Application | Database |
|-------|------------|----------|
| **Development** | Local uvicorn | SQLite |
| **Demo** | Railway / Render | Supabase |
| **Production** | DigitalOcean / AWS | Managed PostgreSQL |

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d
```

---

## API Endpoints

### Transaction Ingestion
```
POST /api/v1/transaction
Headers: Authorization: Bearer <api_key>
Response: { risk_score, risk_level, fraud_type, case_id? }
```

### Case Management
```
GET  /api/v1/cases              # List open cases
GET  /api/v1/cases/{case_id}    # Case detail with SHAP reasons
POST /api/v1/cases/{case_id}/decision  # Record BLOCK/FREEZE/ESCALATE/CLEAR
```

### Dashboard Routes
```
GET /dashboard          # Operations Centre (metrics & charts)
GET /queue              # Alert Queue (filterable case list)
GET /case/{case_id}     # Case Investigation (details & decision)
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **"ML engine not available"** | Run `python pipeline/run_all.py` to train models |
| **"401 Unauthorized"** | Verify API key: `ask_live_demo_key_12345`, run `python store/seed.py` |
| **Database errors** | Delete `*.db` files, restart server, run `python store/seed.py` |
| **Models not loading** | Ensure `engine/models/*.pkl` exist (train if missing) |

---

## Dashboard Features

### Operations Centre (`/dashboard`)
Real-time fraud detection monitoring with live WebSocket updates:

- **Threat Level Indicator** — Dynamic status (ALL CLEAR / ELEVATED / CRITICAL) based on open cases
- **Stat Cards** — Open cases, screened transactions, protected value (INR formatted)
- **Transaction Volume Chart** — Bar chart showing legitimate vs flagged transactions (4-hour buckets)
- **Recent Flags** — Last 3 open cases with risk badges, amounts, and fraud types
- **Today's Breakdown** — Donut chart showing fraud type distribution (ATO/VEL/AMT/NGT/ANO)

### Alert Queue (`/queue`)
Filterable list of open cases requiring analyst decisions:

- Filter by risk level (All / HIGH / MEDIUM)
- Sort by newest/oldest
- Quick actions: BLOCK / FREEZE / ESCALATE / CLEAR
- Auto-advances to next case after decision

### Case Investigation (`/case/{case_id}`)
Detailed case analysis with ML explanations:

- Transaction details and customer profile
- SHAP-powered reason codes ("Why This Was Flagged")
- Recent customer activity history
- One-click decision panel

### Analyst Profile
Click your name in the top bar to view your performance:

- Cases reviewed, accuracy rate, average review time
- Decision breakdown (blocked/frozen/escalated/cleared)
- Recent activity history with timestamps

---

## Documentation

- **[SETUP.md](SETUP.md)** — Complete setup guide with ML training instructions
- **[QUICKSTART.md](QUICKSTART.md)** — Quick reference commands

---

## License

This project is licensed under the MIT License.

---

**Built for analysts. Invisible technology. Clear decisions.**
