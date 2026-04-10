"""
ATO Shield v2 - Phase 1.2: Preprocessing Pipeline
Transforms raw PaySim data into ML-ready features
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_data(data_path: str) -> pd.DataFrame:
    """Load PaySim dataset"""
    print("📥 Loading PaySim dataset...")
    df = pd.read_csv(data_path)
    print(f"   Loaded {len(df):,} transactions")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create engineered features per master document spec"""
    print("\n🔧 Engineering features...")
    
    # Extract hour from step (step represents 1-hour windows in PaySim)
    df['TransactionHour'] = df['step'] % 24
    
    # Calculate customer average transaction amount
    customer_avg = df.groupby('nameOrig')['amount'].mean()
    df['AvgCustomerAmount'] = df['nameOrig'].map(customer_avg)
    
    # Amount vs Average ratio
    df['AmountVsAverage'] = df['amount'] / (df['AvgCustomerAmount'] + 1e-8)
    
    # Is Large Transaction (above 95th percentile)
    threshold = df['amount'].quantile(0.95)
    df['IsLargeTransaction'] = (df['amount'] > threshold).astype(int)
    
    # Is Night Transaction (0-5 AM)
    df['IsNightTransaction'] = ((df['TransactionHour'] >= 0) & (df['TransactionHour'] <= 5)).astype(int)
    
    # Balance features
    df['BalanceChange'] = df['oldbalanceOrg'] - df['newbalanceOrig']
    df['IsBalanceDrained'] = (df['newbalanceOrig'] == 0).astype(int)
    
    # Error in balance (should equal amount for legitimate transactions)
    df['BalanceError'] = abs(df['BalanceChange'] - df['amount'])
    
    # Destination balance features
    df['DestBalanceChange'] = df['newbalanceDest'] - df['oldbalanceDest']
    
    print(f"   ✅ Created 10 engineered features")
    return df


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical features"""
    print("\n🔤 Encoding categoricals...")
    
    # One-hot encode transaction type
    df = pd.get_dummies(df, columns=['type'], prefix='type')
    
    # Drop customer IDs (not useful for ML - use balance features instead)
    cols_to_drop = ['nameOrig', 'nameDest']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    print(f"   ✅ Encoded transaction types, dropped ID columns")
    return df


def prepare_features(df: pd.DataFrame):
    """Split into X and y"""
    print("\n📊 Splitting features...")
    
    # Target
    y = df['isFraud']
    
    # Features (drop target and unused columns)
    cols_to_drop = ['isFraud', 'isFlaggedFraud', 'step']
    X = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    print(f"   Features: {X.shape[1]}")
    print(f"   Samples: {X.shape[0]:,}")
    print(f"   Fraud rate: {y.mean()*100:.2f}%")
    
    return X, y


def split_and_balance(X: pd.DataFrame, y: pd.Series):
    """Train/test split with SMOTE on training set only"""
    print("\n⚖️  Splitting and balancing...")
    
    # Split first (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Train: {len(X_train):,} samples (fraud rate: {y_train.mean()*100:.2f}%)")
    print(f"   Test:  {len(X_test):,} samples (fraud rate: {y_test.mean()*100:.2f}%)")
    
    # Apply SMOTE to training set only
    print("\n   Applying SMOTE to training set...")
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
    
    print(f"   After SMOTE:")
    print(f"   Train: {len(X_train_balanced):,} samples (fraud rate: {y_train_balanced.mean()*100:.1f}%)")
    
    # Save feature names
    feature_names = X.columns.tolist()
    
    return X_train_balanced, X_test, y_train_balanced, y_test, feature_names


def run_preprocessing(data_path: str, output_dir: str = None):
    """Run full preprocessing pipeline"""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df = load_data(data_path)
    
    # Feature engineering
    df = engineer_features(df)
    
    # Encode categoricals
    df = encode_features(df)
    
    # Prepare features
    X, y = prepare_features(df)
    
    # Split and balance
    X_train, X_test, y_train, y_test, feature_names = split_and_balance(X, y)
    
    # Save processed data
    print(f"\n💾 Saving processed data to {output_dir}...")
    joblib.dump(X_train, os.path.join(output_dir, "X_train.pkl"))
    joblib.dump(X_test, os.path.join(output_dir, "X_test.pkl"))
    joblib.dump(y_train, os.path.join(output_dir, "y_train.pkl"))
    joblib.dump(y_test, os.path.join(output_dir, "y_test.pkl"))
    joblib.dump(feature_names, os.path.join(output_dir, "feature_names.pkl"))
    
    print("\n" + "=" * 80)
    print("✅ PHASE 1.2 COMPLETE - PREPROCESSING PIPELINE")
    print("=" * 80)
    print(f"\nFeature count: {len(feature_names)}")
    print(f"Features: {feature_names}")
    print(f"\nTraining set: {len(X_train):,} samples")
    print(f"Test set:     {len(X_test):,} samples")
    print(f"\nFiles saved:")
    print(f"   - X_train.pkl")
    print(f"   - X_test.pkl")
    print(f"   - y_train.pkl")
    print(f"   - y_test.pkl")
    print(f"   - feature_names.pkl")
    
    return X_train, X_test, y_train, y_test, feature_names


if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paysim dataset.csv")
    run_preprocessing(data_path)
