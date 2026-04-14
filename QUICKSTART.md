# ATO Shield v2 - Quick Start Commands

## First Time Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Seed database
python store/seed.py

# Start server
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

## Access Points
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Test Commands

### Health Check
```bash
curl http://localhost:8000/health
```

### Submit Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transaction ^
  -H "Authorization: Bearer ask_live_demo_key_12345" ^
  -H "Content-Type: application/json" ^
  -d "{\"transaction_id\":\"txn_001\",\"step\":3,\"type\":\"CASH_OUT\",\"amount\":120000,\"oldbalanceOrg\":150000,\"newbalanceOrig\":30000,\"oldbalanceDest\":0,\"newbalanceDest\":120000,\"nameOrig\":\"Customer_A\",\"nameDest\":\"Merchant_B\"}"
```

### View Cases
```bash
curl -H "Authorization: Bearer ask_live_demo_key_12345" http://localhost:8000/api/v1/cases
```

## API Keys
- **Demo API Key**: `ask_live_demo_key_12345`
- **Demo Analyst Email**: `analyst@atoshield.demo`

## Common Tasks

### Start Transaction Simulator
```bash
# Continuous simulation (runs until stopped)
python simulator/simulator.py --speed 0.5 --fraud-rate 0.20

# Fast burst (200 transactions then stops)
python simulator/simulator.py --count 200 --speed 0.1 --fraud-rate 0.25

# Or use the batch file (Windows)
inject.bat 50 0.3 0.20
```

### Stop Simulation
```bash
# Press Ctrl+C in simulator terminal
# Or via API:
curl http://localhost:8000/simulate/stop
```

### Re-seed Database
```bash
python store/seed.py
```
(Safe to run multiple times - won't create duplicates)

### Check Logs
Server logs show in the terminal where you ran `uvicorn`

### Stop Server
Press `Ctrl+C` in the terminal

### View Database
Use DB Browser for SQLite: `ato_shield_dev.db`

## ML Model Training (Optional)
```bash
# 1. Get PaySim dataset from Kaggle: https://www.kaggle.com/datasets/ealaxi/paysim1
# 2. Place as "paysim dataset.csv" in project root

# 3. Train models
python pipeline/run_all.py

# 4. Restart server to load models
```

## Troubleshooting

### "ML engine not available"
- Models not trained yet
- Run `python pipeline/run_all.py`

### "401 Unauthorized"
- Check API key is correct: `ask_live_demo_key_12345`
- Run `python store/seed.py` to ensure database has records

### Database errors
- Delete `ato_shield_dev.db`
- Restart server (tables auto-create)
- Run `python store/seed.py`

## Full Documentation
- **Setup Guide**: `SETUP.md`
- **Main README**: `README.md` (architecture & features)
