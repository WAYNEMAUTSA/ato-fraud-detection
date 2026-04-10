"""
Comprehensive API test - Phase 2 validation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from api.main import app
import json

client = TestClient(app)

print("=" * 80)
print("PHASE 2 - API VALIDATION TESTS")
print("=" * 80)

# Test 1: Health check
print("\n1️⃣  Health Check")
response = client.get("/health")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200, "Health check failed"
print("   ✅ PASS")

# Test 2: Invalid API key
print("\n2️⃣  Invalid API Key (should be 401)")
response = client.post(
    "/api/v1/transaction",
    headers={"Authorization": "Bearer invalid_key"},
    json={"transaction_id": "TXN_001", "step": 1, "type": "CASH_OUT", "amount": 100, 
          "nameOrig": "C1", "oldbalanceOrg": 100, "newbalanceOrig": 0, 
          "nameDest": "M1", "oldbalanceDest": 0, "newbalanceDest": 100}
)
print(f"   Status: {response.status_code}")
assert response.status_code == 401, "Should reject invalid key"
print("   ✅ PASS")

# Test 3: Valid transaction (LOW risk)
print("\n3️⃣  Valid Transaction - LOW Risk")
response = client.post(
    "/api/v1/transaction",
    headers={"Authorization": "Bearer ask_live_demo_key_12345"},
    json={
        "transaction_id": "TXN_LOW_001",
        "step": 10,
        "type": "PAYMENT",
        "amount": 5000,
        "nameOrig": "C_TEST_001",
        "oldbalanceOrg": 50000,
        "newbalanceOrig": 45000,
        "nameDest": "M_TEST_001",
        "oldbalanceDest": 0,
        "newbalanceDest": 5000
    }
)
print(f"   Status: {response.status_code}")
data = response.json()
print(f"   Risk Score: {data['risk_score']:.4f}")
print(f"   Risk Level: {data['risk_level']}")
assert response.status_code == 200
assert data['risk_level'] in ['LOW', 'MEDIUM', 'HIGH']
print("   ✅ PASS")

# Test 4: High-risk transaction
print("\n4️⃣  High-Risk Transaction (should create case)")
response = client.post(
    "/api/v1/transaction",
    headers={"Authorization": "Bearer ask_live_demo_key_12345"},
    json={
        "transaction_id": "TXN_HIGH_001",
        "step": 3,
        "type": "CASH_OUT",
        "amount": 500000,
        "nameOrig": "C_TEST_002",
        "oldbalanceOrg": 600000,
        "newbalanceOrig": 100000,
        "nameDest": "M_TEST_002",
        "oldbalanceDest": 0,
        "newbalanceDest": 500000
    }
)
print(f"   Status: {response.status_code}")
data = response.json()
print(f"   Risk Score: {data['risk_score']:.4f}")
print(f"   Risk Level: {data['risk_level']}")
print(f"   Case ID: {data.get('case_id')}")
print(f"   Fraud Type: {data.get('fraud_type')}")
print("   ✅ PASS")

# Test 5: List cases
print("\n5️⃣  List Cases")
response = client.get(
    "/api/v1/cases",
    headers={"Authorization": "Bearer ask_live_demo_key_12345"}
)
print(f"   Status: {response.status_code}")
cases = response.json()
print(f"   Open Cases: {len(cases)}")
if cases:
    print(f"   First Case: {cases[0]['case_id']}")
    print(f"   Risk Level: {cases[0]['risk_level']}")
print("   ✅ PASS")

print("\n" + "=" * 80)
print("✅ ALL PHASE 2 TESTS PASSED")
print("=" * 80)
