# ─── XGBoost Fraud Detection Model ───────────────────────────────────
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import joblib
import os

print("✅ Libraries imported successfully")

# ─── Load processed data ─────────────────────────────────────────────────────
print("⏳ Loading processed data...")

X = pd.read_csv("data/processed/X_train.csv")
y = pd.read_csv("data/processed/y_train.csv").squeeze()

print(f"✅ Data loaded — {X.shape[0]:,} rows, {X.shape[1]} columns")

# ─── Split data into train and test sets ─────────────────────────────────────
print("⏳ Splitting data...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.2,      # 80% training, 20% testing
    random_state=42     # same split every time
)

print(f"✅ Data split complete")
print(f"   Training set: {X_train.shape[0]:,} rows")
print(f"   Testing set:  {X_test.shape[0]:,} rows")

# ─── Train XGBoost model ─────────────────────────────────────────────────────
print("⏳ Training XGBoost model... this may take a few minutes")

model = XGBClassifier(
    n_estimators=100,       # number of trees
    max_depth=6,            # how deep each tree goes
    learning_rate=0.1,      # how fast it learns
    random_state=42,
    eval_metric='logloss',
    verbosity=0
)

model.fit(X_train, y_train)

print("✅ XGBoost model trained successfully")

# ─── Evaluate the model ──────────────────────────────────────────────────────
print("⏳ Evaluating model...")

y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_pred_proba)

print(f"✅ Model Evaluation Results:")
print(f"   Precision : {precision:.3f}")
print(f"   Recall    : {recall:.3f}")
print(f"   F1-Score  : {f1:.3f}")
print(f"   ROC-AUC   : {roc_auc:.3f}")

# ─── Save the trained model ───────────────────────────────────────────────────
print("⏳ Saving model...")

os.makedirs("src/models/saved", exist_ok=True)

joblib.dump(model, "src/models/saved/xgboost_model.pkl")

print("✅ Model saved to src/models/saved/xgboost_model.pkl")
print("\n🎉 Step 3 Complete — XGBoost model trained and saved!")
