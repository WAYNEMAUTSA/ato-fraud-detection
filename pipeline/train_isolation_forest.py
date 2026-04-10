"""
ATO Shield v2 - Phase 1.4: Isolation Forest Training
"""
import numpy as np
from sklearn.ensemble import IsolationForest
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


def train_isolation_forest(X_train, X_test, y_train, y_test, contamination=0.035):
    """Train Isolation Forest per master document spec"""
    print("\n🌲 Training Isolation Forest...")
    print(f"   Contamination: {contamination}")
    
    # Isolation Forest
    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    
    # Train
    model.fit(X_train)
    
    return model


def evaluate_model(model, X_test, y_test):
    """Evaluate Isolation Forest performance"""
    print("\n📊 Evaluating model...")
    
    # Predictions (-1 for anomalies, 1 for normal)
    y_pred_raw = model.predict(X_test)
    
    # Convert to binary (1 for fraud, 0 for legitimate)
    y_pred = (y_pred_raw == -1).astype(int)
    
    # Anomaly scores (lower = more anomalous)
    scores = model.score_samples(X_test)
    # Convert to fraud probability (higher = more fraudulent)
    y_proba = -scores
    
    # Metrics
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)
    
    print("\n" + "=" * 60)
    print("ISOLATION FOREST PERFORMANCE")
    print("=" * 60)
    print(f"   Precision:  {precision:.3f}")
    print(f"   Recall:     {recall:.3f}")
    print(f"   F1 Score:   {f1:.3f}")
    print(f"   ROC-AUC:    {roc_auc:.3f}")
    print("=" * 60)
    
    print("\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc
    }


def save_model(model, model_dir: str = None):
    """Save trained model"""
    if model_dir is None:
        model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine", "models")
    
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "isolation_forest.pkl")
    
    print(f"\n💾 Saving model to {model_path}...")
    joblib.dump(model, model_path)
    
    print(f"   ✅ Model saved successfully")


def run_isolation_forest_training(data_dir: str = None, model_dir: str = None):
    """Run complete Isolation Forest training pipeline"""
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed")
    
    # Load data
    X_train, X_test, y_train, y_test, feature_names = load_processed_data(data_dir)
    
    # Train model
    model = train_isolation_forest(X_train, X_test, y_train, y_test)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save
    save_model(model, model_dir)
    
    print("\n" + "=" * 80)
    print("✅ PHASE 1.4 COMPLETE - ISOLATION FOREST TRAINING")
    print("=" * 80)
    
    return model, metrics


if __name__ == "__main__":
    run_isolation_forest_training()
