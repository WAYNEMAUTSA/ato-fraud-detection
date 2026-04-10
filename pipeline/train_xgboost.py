"""
ATO Shield v2 - Phase 1.3: XGBoost Training
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import classification_report, roc_auc_score, precision_score, recall_score, f1_score
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_processed_data(data_dir: str):
    """Load preprocessed data"""
    print("📥 Loading processed data...")
    X_train = joblib.load(os.path.join(data_dir, "X_train.pkl"))
    X_test = joblib.load(os.path.join(data_dir, "X_test.pkl"))
    y_train = joblib.load(os.path.join(data_dir, "y_train.pkl"))
    y_test = joblib.load(os.path.join(data_dir, "y_test.pkl"))
    feature_names = joblib.load(os.path.join(data_dir, "feature_names.pkl"))
    
    print(f"   Train: {len(X_train):,} samples")
    print(f"   Test:  {len(X_test):,} samples")
    print(f"   Features: {len(feature_names)}")
    
    return X_train, X_test, y_train, y_test, feature_names


def train_xgboost(X_train, X_test, y_train, y_test, feature_names):
    """Train XGBoost model per master document spec"""
    print("\n🚀 Training XGBoost model...")
    print("   Parameters: 100 trees, depth 6")
    
    # Calculate scale_pos_weight for imbalanced data
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_weight = neg_count / pos_count if pos_count > 0 else 1
    
    print(f"   Scale pos weight: {scale_weight:.2f}")
    
    # XGBoost classifier
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=scale_weight,
        random_state=42,
        eval_metric='logloss',
        use_label_encoder=False
    )
    
    # Train
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=True
    )
    
    return model


def evaluate_model(model, X_test, y_test, feature_names):
    """Evaluate model performance"""
    print("\n📊 Evaluating model...")
    
    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)
    
    print("\n" + "=" * 60)
    print("XGBOOST MODEL PERFORMANCE")
    print("=" * 60)
    print(f"   Precision:  {precision:.3f}")
    print(f"   Recall:     {recall:.3f}")
    print(f"   F1 Score:   {f1:.3f}")
    print(f"   ROC-AUC:    {roc_auc:.3f}")
    print("=" * 60)
    
    print("\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))
    
    # Feature importance
    print("\n🔝 Top 10 Feature Importance:")
    importance = model.feature_importances_
    feat_imp = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    for i, row in feat_imp.head(10).iterrows():
        print(f"   {row['feature']:<30} {row['importance']:.4f}")
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc
    }


def save_model(model, feature_names, model_dir: str = None):
    """Save trained model"""
    if model_dir is None:
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine", "models")
    
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "xgboost.pkl")
    
    print(f"\n💾 Saving model to {model_path}...")
    joblib.dump({
        'model': model,
        'feature_names': feature_names
    }, model_path)
    
    print(f"   ✅ Model saved successfully")


def run_xgboost_training(data_dir: str = None, model_dir: str = None):
    """Run complete XGBoost training pipeline"""
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
    
    # Load data
    X_train, X_test, y_train, y_test, feature_names = load_processed_data(data_dir)
    
    # Train model
    model = train_xgboost(X_train, X_test, y_train, y_test, feature_names)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test, feature_names)
    
    # Save
    save_model(model, feature_names, model_dir)
    
    print("\n" + "=" * 80)
    print("✅ PHASE 1.3 COMPLETE - XGBOOST TRAINING")
    print("=" * 80)
    
    return model, metrics


if __name__ == "__main__":
    run_xgboost_training()
