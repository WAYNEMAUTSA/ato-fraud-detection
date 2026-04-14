# ATO Shield v2 - Setup Guide

This guide will walk you through setting up the ATO Shield v2 fraud detection system from scratch.

## Prerequisites

- Python 3.9+
- pip or conda
- (Optional) Docker and Docker Compose for containerized deployment

## Quick Start (Development)

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/Mac

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file has been created with development defaults. Review and adjust if needed:

```bash
# View current configuration
cat .env  # Linux/Mac
type .env  # Windows
```

**Key settings:**
- `DATABASE_URL`: Database connection string (default: SQLite for development)
- `API_SECRET_KEY`: Secret key for API authentication
- `BANK_API_KEY`: Demo API key for testing

### 3. Seed the Database

Create initial Bank and Analyst records:

```bash
python store/seed.py
```

This will create:
- **Demo Bank**: API key `ask_live_demo_key_12345`
- **Demo Analyst**: Email `analyst@atoshield.demo`

### 4. Start the Application

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- **API**: http://localhost:8000
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs

### 5. Verify Health Check

```bash
curl http://localhost:8000/health
```

Expected response (without ML models):
```json
{
  "status": "degraded",
  "ml_engine": "not_available",
  "database": "connected"
}
```

---

## Enabling ML Model Training (Optional but Recommended)

The system can run without ML models for testing the UI and API, but to enable fraud scoring, you need to train the models.

### Step 1: Obtain the PaySim Dataset

The ML models require the **PaySim Synthetic Mobile Money Dataset**.

**Where to get it:**
1. Go to: https://www.kaggle.com/datasets/ealaxi/paysim1
2. Sign up/login to Kaggle
3. Download the dataset
4. Place the CSV file in the project root as `paysim dataset.csv`

**Alternative (if you have Kaggle CLI):**
```bash
kaggle datasets download -d ealaxi/paysim1
unzip paysim1.zip -d data/
mv data/PS_20174392719_1491204439457_log.csv "paysim dataset.csv"
```

### Step 2: Train ML Models

Run the complete ML pipeline:

```bash
python pipeline/run_all.py
```

This will:
1. Load and preprocess the PaySim dataset
2. Train the XGBoost classifier
3. Train the Isolation Forest anomaly detector
4. Save models to `engine/models/`
5. Generate training reports

**Expected output files:**
- `engine/models/xgboost.pkl` - XGBoost fraud classifier
- `engine/models/isolation_forest.pkl` - Isolation Forest anomaly detector

### Step 3: Restart the Application

After training, restart the server to load the ML models:

```bash
# Stop the running server (Ctrl+C)
# Then restart:
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Check the health endpoint again:

```bash
curl http://localhost:8000/health
```

Expected response (with ML models):
```json
{
  "status": "ok",
  "ml_engine": "loaded",
  "database": "connected"
}
```

---

## Testing the System

### Test API Authentication

```bash
# Valid API key (should return 200)
curl -X GET http://localhost:8000/api/v1/test \
  -H "Authorization: Bearer ask_live_demo_key_12345"

# Invalid key (should return 401)
curl -X GET http://localhost:8000/api/v1/test \
  -H "Authorization: Bearer invalid_key"
```

### Submit a Test Transaction

```bash
curl -X POST http://localhost:8000/api/v1/transaction \
  -H "Authorization: Bearer ask_live_demo_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "txn_test_001",
    "step": 3,
    "type": "CASH_OUT",
    "amount": 120000,
    "oldbalanceOrg": 150000,
    "newbalanceOrig": 30000,
    "oldbalanceDest": 0,
    "newbalanceDest": 120000,
    "nameOrig": "Customer_A",
    "nameDest": "Merchant_B"
  }'
```

Expected response (with ML models):
```json
{
  "transaction_id": "txn_test_001",
  "risk_score": 0.75,
  "risk_level": "HIGH",
  "fraud_type": "ATO",
  "case_id": "case_uuid_here",
  "recommended_action": "BLOCK or FREEZE recommended"
}
```

### Run the Transaction Simulator

If you have the PaySim dataset, you can run the simulator to generate realistic test traffic:

```bash
# Run simulator (sends 100 transactions)
python simulator/simulator.py --count 100

# Run with real dataset sampling
python simulator/simulator.py --dataset "paysim dataset.csv" --count 50
```

### Access the Dashboard

1. Open http://localhost:8000/dashboard
2. View the **Operations Centre** with real-time metrics
3. Click on flagged cases to investigate
4. Make decisions: **ESCALATE**, **CLEAR**, or **FREEZE**

---

## Troubleshooting

### Issue: "ML engine not available" in health check

**Cause:** Model files are missing or corrupted.

**Solution:**
```bash
# Check if models exist
ls engine/models/*.pkl

# If missing, train models first
python pipeline/run_all.py

# Restart the server
```

### Issue: "401 Unauthorized" on API calls

**Cause:** Invalid or missing API key.

**Solution:**
```bash
# Verify database is seeded
python store/seed.py

# Use the correct API key: ask_live_demo_key_12345
```

### Issue: "Database not found" or table errors

**Cause:** SQLite database file is missing or corrupted.

**Solution:**
```bash
# Delete existing database (if corrupted)
rm ato_shield_dev.db  # Linux/Mac
del ato_shield_dev.db  # Windows

# Restart the server (tables will be created automatically)
uvicorn api.main:app --reload

# Re-seed the database
python store/seed.py
```

### Issue: SHAP explainer errors

**Cause:** XGBoost model is missing or incompatible.

**Solution:** Retrain models with the pipeline script.

---

## Production Deployment

For production use:

1. **Use PostgreSQL instead of SQLite:**
   ```bash
   # Update .env
   DATABASE_URL=postgresql://user:password@localhost:5432/ato_shield
   
   # Install PostgreSQL driver
   pip install psycopg2-binary
   ```

2. **Generate secure API keys:**
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

3. **Use environment-specific secrets:**
   - Never commit `.env` to version control
   - Use AWS Secrets Manager, Azure Key Vault, or similar

4. **Set up proper logging:**
   - Configure log rotation
   - Send logs to centralized monitoring

5. **Enable HTTPS:**
   - Use a reverse proxy (nginx, Apache)
   - Configure SSL certificates

6. **Use Docker for deployment:**
   ```bash
   docker-compose up -d
   ```

---

## Next Steps

- Review the [README.md](README.md) for architecture overview and dashboard features
- Explore the API documentation at http://localhost:8000/docs
- Run the transaction simulator to test live updates: `python simulator/simulator.py --speed 0.5`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs in the console
3. Inspect the database using SQLite browser or pgAdmin
4. Test individual components with the provided test scripts

---

**System Status Checklist:**

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured
- [ ] Database seeded (`python store/seed.py`)
- [ ] Server running (`uvicorn api.main:app --reload`)
- [ ] Health check returns `"status": "ok"` or `"degraded"`
- [ ] (Optional) ML models trained (`python pipeline/run_all.py`)
- [ ] Dashboard accessible at `/dashboard`
- [ ] Test transaction submission works
