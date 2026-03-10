# ─── Isolation Forest Anomaly Detection ──────────────────────────────
# This model finds unusual transactions without needing fraud labels.
# It learns what "normal" looks like and flags anything different.

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import joblib
import os

print("✅ Libraries imported successfully")

# ─── Load original unbalanced data ───────────────────────────────────────────
print("⏳ Loading data...")

X = pd.read_csv("data/processed/X_test.csv")
y = pd.read_csv("data/processed/y_test.csv").squeeze()

print(f"✅ Data loaded — {X.shape[0]:,} rows")
print(f"   Fraud: {y.sum():,} ({y.mean()*100:.1f}%)")
print(f"   Normal: {(y==0).sum():,}")

# ─── Train Isolation Forest ───────────────────────────────────────────────────
print("⏳ Training Isolation Forest... this may take a few minutes")

iso_forest = IsolationForest(
    n_estimators=100,       # number of trees
    contamination=0.035,    # we tell it ~3.5% of data is fraud
    random_state=42,
    n_jobs=-1               # use all CPU cores to go faster
)

iso_forest.fit(X)

print("✅ Isolation Forest trained successfully")

# ─── Evaluate Isolation Forest ───────────────────────────────────────────────
print("⏳ Evaluating model...")

# Isolation Forest returns -1 for anomalies and 1 for normal
# We convert to 1 for fraud and 0 for normal to match our labels
raw_predictions = iso_forest.predict(X)
y_pred = [1 if x == -1 else 0 for x in raw_predictions]

# Get anomaly scores (lower score = more anomalous)
scores = iso_forest.decision_function(X)
# Flip scores so higher = more suspicious
anomaly_scores = -scores

precision = precision_score(y, y_pred)
recall = recall_score(y, y_pred)
f1 = f1_score(y, y_pred)
roc_auc = roc_auc_score(y, anomaly_scores)

print(f"✅ Isolation Forest Evaluation Results:")
print(f"   Precision : {precision:.3f}")
print(f"   Recall    : {recall:.3f}")
print(f"   F1-Score  : {f1:.3f}")
print(f"   ROC-AUC   : {roc_auc:.3f}")

# ─── Save Isolation Forest model ─────────────────────────────────────────────
print("⏳ Saving model...")

joblib.dump(iso_forest, "src/models/saved/isolation_forest.pkl")

print("✅ Model saved to src/models/saved/isolation_forest.pkl")