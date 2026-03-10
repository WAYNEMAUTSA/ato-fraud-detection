# ─── Step 5: Risk Score Fusion ───────────────────────────────────────────────
# Combines XGBoost (70%) + Isolation Forest (30%) into one final risk score
# and labels each transaction as LOW / MEDIUM / HIGH risk

import pandas as pd
import numpy as np
import joblib

print("✅ Libraries imported successfully")

# ─── Load both saved models ───────────────────────────────────────────────────
print("⏳ Loading models...")

xgb_model = joblib.load("src/models/saved/xgboost_model.pkl")
iso_model = joblib.load("src/models/saved/isolation_forest.pkl")

print("✅ Both models loaded successfully")

# ─── Load test data ───────────────────────────────────────────────────────────
print("⏳ Loading test data...")

X = pd.read_csv("data/processed/X_test.csv")
y = pd.read_csv("data/processed/y_test.csv").squeeze()

print(f"✅ Data loaded — {X.shape[0]:,} rows")

# ─── Generate scores from both models ────────────────────────────────────────
print("⏳ Generating risk scores...")

# XGBoost probability score (0 to 1)
xgb_scores = xgb_model.predict_proba(X)[:, 1]

# Isolation Forest anomaly score (flipped so higher = more suspicious)
iso_raw = iso_model.decision_function(X)
iso_scores = ((-iso_raw) - (-iso_raw).min()) / ((-iso_raw).max() - (-iso_raw).min())

# ─── Combine scores 70% XGBoost + 30% Isolation Forest ───────────────────────
final_scores = (0.7 * xgb_scores) + (0.3 * iso_scores)

# ─── Label each transaction ───────────────────────────────────────────────────
def label_risk(score):
    if score >= 0.70:
        return "HIGH"
    elif score >= 0.30:
        return "MEDIUM"
    else:
        return "LOW"

risk_labels = [label_risk(s) for s in final_scores]

print(f"✅ Risk scores generated")
print(f"   HIGH risk:   {risk_labels.count('HIGH'):,}")
print(f"   MEDIUM risk: {risk_labels.count('MEDIUM'):,}")
print(f"   LOW risk:    {risk_labels.count('LOW'):,}")

# ─── Save results to a file ───────────────────────────────────────────────────
print("⏳ Saving results...")

results = pd.DataFrame({
    'xgb_score': xgb_scores,
    'iso_score': iso_scores,
    'final_score': final_scores,
    'risk_label': risk_labels,
    'actual_fraud': y.values
})

results.to_csv("data/processed/risk_scores.csv", index=False)

# ─── Quick accuracy check ─────────────────────────────────────────────────────
high_risk = results[results['risk_label'] == 'HIGH']
fraud_caught = high_risk['actual_fraud'].sum()
total_fraud = y.sum()

print(f"✅ Results saved to data/processed/risk_scores.csv")
print(f"   Total fraud cases: {total_fraud:,}")
print(f"   Fraud caught in HIGH risk: {fraud_caught:,} ({fraud_caught/total_fraud*100:.1f}%)")
print(f"\n🎉 Step 5 Complete — Risk scoring system working!")