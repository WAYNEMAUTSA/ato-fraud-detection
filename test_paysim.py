"""Test with actual PaySim data"""
import pandas as pd
import requests
import json

# Load one transaction from PaySim
df = pd.read_csv("paysim dataset.csv")
txn = df.iloc[0]

payload = {
    "transaction_id": "TEST_001",
    "step": int(txn['step']),
    "type": txn['type'],
    "amount": float(txn['amount']),
    "nameOrig": txn['nameOrig'],
    "oldbalanceOrg": float(txn['oldbalanceOrg']),
    "newbalanceOrig": float(txn['newbalanceOrig']),
    "nameDest": txn['nameDest'],
    "oldbalanceDest": float(txn['oldbalanceDest']),
    "newbalanceDest": float(txn['newbalanceDest'])
}

print("🔄 Sending transaction:")
print(json.dumps(payload, indent=2))

response = requests.post(
    "http://localhost:8000/api/v1/transaction",
    headers={"Authorization": "Bearer ask_live_demo_key_12345"},
    json=payload
)

print(f"\n📊 Status: {response.status_code}")
print(f"📊 Response: {response.text}")
