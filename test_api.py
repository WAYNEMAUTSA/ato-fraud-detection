"""
Test the transaction ingestion flow
"""
import requests
import json

url = "http://localhost:8000/api/v1/transaction"
headers = {
    "Authorization": "Bearer ask_live_demo_key_12345",
    "Content-Type": "application/json"
}

payload = {
    "transaction_id": "TXN_TEST_006",
    "step": 3,
    "type": "CASH_OUT",
    "amount": 120000,
    "nameOrig": "C1231006815",
    "oldbalanceOrg": 150000,
    "newbalanceOrig": 30000,
    "nameDest": "M840083671",
    "oldbalanceDest": 0,
    "newbalanceDest": 120000
}

print("🔄 Sending transaction to API...")
response = requests.post(url, headers=headers, json=payload)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
