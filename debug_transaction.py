"""Debug transaction endpoint"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from api.main import app
import traceback

client = TestClient(app)

print("🔄 Testing transaction endpoint with PaySim data...")

payload = {
    "transaction_id": "TEST_DEBUG_001",
    "step": 1,
    "type": "PAYMENT",
    "amount": 9839.64,
    "nameOrig": "C1231006815",
    "oldbalanceOrg": 170136.0,
    "newbalanceOrig": 160296.36,
    "nameDest": "M1979787155",
    "oldbalanceDest": 0.0,
    "newbalanceDest": 0.0
}

try:
    response = client.post(
        "/api/v1/transaction",
        headers={"Authorization": "Bearer ask_live_demo_key_12345"},
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 500:
        print("\n❌ Server error - checking exception details...")
        # Try again with raise_on_error to see the actual exception
        try:
            with client:
                response = client.post(
                    "/api/v1/transaction",
                    headers={"Authorization": "Bearer ask_live_demo_key_12345"},
                    json=payload,
                    follow_redirects=True
                )
        except Exception as e:
            print(f"\nException: {type(e).__name__}")
            print(f"Message: {str(e)}")
            traceback.print_exc()

except Exception as e:
    print(f"\n❌ Exception occurred:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    traceback.print_exc()
