"""
ATO Shield v2 - Phase 1.1: PaySim Dataset Exploration
"""
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 80)
print("ATO SHIELD V2 - PHASE 1.1: PAYSIM DATASET EXPLORATION")
print("=" * 80)

# Load dataset
print("\n📥 Loading PaySim dataset...")
df = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paysim dataset.csv"))

print(f"\n✅ Dataset loaded successfully!")
print(f"   Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

print("\n" + "=" * 80)
print("COLUMN OVERVIEW")
print("=" * 80)
for col in df.columns:
    dtype = str(df[col].dtype)
    non_null = df[col].count()
    null_pct = (df[col].isnull().sum() / len(df)) * 100
    print(f"   {col:<20} {dtype:<12} {non_null:>10,} values  {null_pct:.1f}% null")

print("\n" + "=" * 80)
print("FIRST 5 ROWS")
print("=" * 80)
print(df.head())

print("\n" + "=" * 80)
print("TARGET VARIABLE DISTRIBUTION (isFraud)")
print("=" * 80)
fraud_counts = df['isFraud'].value_counts()
total = len(df)
fraud_count = fraud_counts.get(1, 0)
legit_count = fraud_counts.get(0, 0)
fraud_rate = (fraud_count / total) * 100

print(f"   Legitimate (0): {legit_count:>10,} ({100-fraud_rate:.2f}%)")
print(f"   Fraud (1):      {fraud_count:>10,} ({fraud_rate:.2f}%)")
print(f"   Total:          {total:>10,}")

print("\n" + "=" * 80)
print("TRANSACTION TYPE DISTRIBUTION")
print("=" * 80)
type_counts = df['type'].value_counts()
for txn_type, count in type_counts.items():
    pct = (count / total) * 100
    print(f"   {txn_type:<15} {count:>10,} ({pct:.2f}%)")

print("\n" + "=" * 80)
print("FRAUD BY TRANSACTION TYPE")
print("=" * 80)
fraud_by_type = df[df['isFraud'] == 1]['type'].value_counts()
for txn_type, count in fraud_by_type.items():
    total_of_type = (df['type'] == txn_type).sum()
    fraud_rate_type = (count / total_of_type) * 100 if total_of_type > 0 else 0
    print(f"   {txn_type:<15} {count:>8,} fraud / {total_of_type:>10,} total ({fraud_rate_type:.2f}% fraud rate)")

print("\n" + "=" * 80)
print("NUMERIC COLUMNS - STATISTICAL SUMMARY")
print("=" * 80)
print(df.describe().to_string())

print("\n" + "=" * 80)
print("KEY INSIGHTS")
print("=" * 80)
print(f"   1. Dataset contains {df.shape[0]:,} mobile money transactions")
print(f"   2. Fraud rate: {fraud_rate:.2f}% ({fraud_count:,} fraudulent transactions)")
print(f"   3. Most common transaction types: {', '.join(type_counts.head(3).index.tolist())}")
print(f"   4. Features available: {', '.join(df.columns.tolist())}")
print(f"   5. Class imbalance: {'Severe' if fraud_rate < 1 else 'Moderate'} - SMOTE will be needed")

print("\n" + "=" * 80)
print("✅ PHASE 1.1 COMPLETE")
print("=" * 80)
