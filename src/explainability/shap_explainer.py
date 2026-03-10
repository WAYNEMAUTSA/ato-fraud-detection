# ─── Step 6: SHAP Explainability ─────────────────────────────────────────────
# SHAP explains WHY the model flagged a transaction as suspicious.
# It shows which features contributed most to the fraud score.

import pandas as pd
import numpy as np
import shap
import joblib
import warnings
warnings.filterwarnings('ignore')

print("✅ Libraries imported successfully")

# ─── Load model and data ──────────────────────────────────────────────────────
print("⏳ Loading model and data...")

xgb_model = joblib.load("src/models/saved/xgboost_model.pkl")

X = pd.read_csv("data/processed/X_test.csv")
y = pd.read_csv("data/processed/y_test.csv").squeeze()

# Use a small sample for speed — SHAP is slow on large datasets
X_sample = X.head(500)

print(f"✅ Model and data loaded")
print(f"   Explaining {len(X_sample)} transactions")

# ─── Generate SHAP values ─────────────────────────────────────────────────────
print("⏳ Generating SHAP values... this may take a minute")

explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_sample)

print("✅ SHAP values generated successfully")

# ─── Show top features overall ───────────────────────────────────────────────
print("\n📊 Top 10 Most Important Features for Fraud Detection:")
print("─" * 50)

feature_importance = pd.DataFrame({
    'feature': X_sample.columns,
    'importance': np.abs(shap_values).mean(axis=0)
}).sort_values('importance', ascending=False)

for i, row in feature_importance.head(10).iterrows():
    bar = "█" * int(row['importance'] * 100)
    print(f"   {row['feature']:<25} {row['importance']:.4f}  {bar}")

    # ─── Explain one specific flagged transaction ─────────────────────────────────
print("\n🔍 Explaining a single HIGH RISK transaction:")
print("─" * 50)

# Pick the transaction with highest fraud probability
xgb_probs = xgb_model.predict_proba(X_sample)[:, 1]
highest_risk_idx = np.argmax(xgb_probs)
transaction = X_sample.iloc[highest_risk_idx]

print(f"   Transaction index: {highest_risk_idx}")
print(f"   XGBoost fraud score: {xgb_probs[highest_risk_idx]:.3f}")
print(f"\n   Why was this flagged?")

# Get SHAP values for this transaction
single_shap = shap_values[highest_risk_idx]
single_explanation = pd.DataFrame({
    'feature': X_sample.columns,
    'value': transaction.values,
    'shap_impact': single_shap
}).sort_values('shap_impact', ascending=False)

for _, row in single_explanation.head(5).iterrows():
    direction = "↑ increases" if row['shap_impact'] > 0 else "↓ decreases"
    print(f"   {row['feature']:<25} = {row['value']:<10.2f} {direction} fraud risk by {abs(row['shap_impact']):.3f}")

print("\n🎉 Step 6 Complete — SHAP explainability working!")