"""
Debug transaction route
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

print("🔄 Testing transaction endpoint...")
response = client.post(
    "/api/v1/transaction",
    headers={"Authorization": "Bearer ask_live_demo_key_12345"},
    json={
        "transaction_id": "TXN_DEBUG_001",
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
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 500:
    print("\n❌ Error occurred!")
    import traceback
    if hasattr(response, 'detail'):
        print(f"Detail: {response.detail}")
