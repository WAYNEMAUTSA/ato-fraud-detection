# Data Loading & Preprocessing ───────────────────────────────────
# This script loads the IEEE-CIS dataset, cleans it, creates new features,
# and balances the data ready for AI model training.

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
import joblib
import os

print("✅ Libraries imported successfully")

# ─── Load the dataset ────────────────────────────────────────────────────────
print("⏳ Loading dataset... this may take 30 seconds")

df = pd.read_csv("data/raw/train_transaction.csv")

print(f"✅ Dataset loaded — {df.shape[0]:,} rows and {df.shape[1]} columns")
print(f"   Fraud cases: {df['isFraud'].sum():,} ({df['isFraud'].mean()*100:.1f}%)")
print(f"   Normal cases: {(df['isFraud']==0).sum():,}")

# ─── Select key features for ATO fraud detection ─────────────────────────────
features = [
    'TransactionAmt',
    'ProductCD',
    'card1', 'card2', 'card3', 'card5',
    'addr1', 'addr2',
    'dist1',
    'P_emaildomain',
    'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
    'D1', 'D2', 'D3',
    'V1', 'V2', 'V3', 'V4', 'V5', 'V6',
    'DeviceType',
    'DeviceInfo'
]

# Keep only features that exist in the dataset
features = [f for f in features if f in df.columns]

# Create our working dataframe
X = df[features].copy()
y = df['isFraud'].copy()

print(f"✅ Selected {len(features)} features for training")
print(f"   Features: {features}")

# ─── Clean missing values ─────────────────────────────────────────────────────
print("⏳ Cleaning missing values...")

for col in X.columns:
    if X[col].dtype == 'object':
        # Text columns — fill with 'Unknown'
        X[col] = X[col].fillna('Unknown')
    else:
        # Number columns — fill with median
        X[col] = X[col].fillna(X[col].median())

print(f"✅ Missing values cleaned")
print(f"   Remaining missing values: {X.isnull().sum().sum()}")

# ─── Convert text columns to numbers ─────────────────────────────────────────
print("⏳ Encoding text columns...")

label_encoder = LabelEncoder()

for col in X.columns:
    if X[col].dtype == 'object':
        X[col] = label_encoder.fit_transform(X[col])
        print(f"   Encoded: {col}")

print("✅ All text columns converted to numbers")

# ─── Engineer new fraud-detection features ───────────────────────────────────
print("⏳ Creating new features...")

# What hour of day did the transaction happen?
# TransactionDT is seconds from a reference point — we convert to hours
X['TransactionHour'] = (df['TransactionDT'] / 3600 % 24).astype(int)

# How does this transaction amount compare to the average?
avg_amount = X['TransactionAmt'].mean()
X['AmountVsAverage'] = X['TransactionAmt'] / avg_amount

# Is this a large transaction? (1 = yes, 0 = no)
X['IsLargeTransaction'] = (X['TransactionAmt'] > 1000).astype(int)

# Is this transaction happening at night? (1 = yes, 0 = no)
X['IsNightTransaction'] = ((X['TransactionHour'] >= 0) & (X['TransactionHour'] <= 5)).astype(int)

print("✅ New features created:")
print(f"   TransactionHour — range: {X['TransactionHour'].min()} to {X['TransactionHour'].max()}")
print(f"   AmountVsAverage — mean: {X['AmountVsAverage'].mean():.2f}")
print(f"   IsLargeTransaction — {X['IsLargeTransaction'].sum():,} large transactions")
print(f"   IsNightTransaction — {X['IsNightTransaction'].sum():,} night transactions")

# ─── Balance the data with SMOTE ─────────────────────────────────────────────
print("⏳ Balancing data with SMOTE... this will take a few minutes")

smote = SMOTE(random_state=42)
X_balanced, y_balanced = smote.fit_resample(X, y)

print(f"✅ Data balanced successfully")
print(f"   Before — Fraud: {y.sum():,} | Normal: {(y==0).sum():,}")
print(f"   After  — Fraud: {y_balanced.sum():,} | Normal: {(y_balanced==0).sum():,}")

# ─── Save the processed data ─────────────────────────────────────────────────
print("⏳ Saving processed data...")

# Create processed folder if it doesn't exist
os.makedirs("data/processed", exist_ok=True)

# Save balanced data ready for model training
X_balanced.to_csv("data/processed/X_train.csv", index=False)
y_balanced.to_csv("data/processed/y_train.csv", index=False)

# Save original unbalanced data for testing
X.to_csv("data/processed/X_test.csv", index=False)
y.to_csv("data/processed/y_test.csv", index=False)

print("✅ Data saved successfully")
print(f"   data/processed/X_train.csv — {X_balanced.shape[0]:,} rows, {X_balanced.shape[1]} columns")
print(f"   data/processed/y_train.csv — labels for training")
print(f"   data/processed/X_test.csv  — original data for testing")
print(f"   data/processed/y_test.csv  — labels for testing")
print("\n🎉 Step 2 Complete — Data is ready for model training!")