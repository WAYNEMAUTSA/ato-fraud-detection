"""
ATO Shield v2 - Phase 1.7: Full Pipeline Orchestrator
Single command to rebuild all ML models from scratch
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_pipeline():
    """Execute full ML training pipeline"""
    print("=" * 80)
    print(" 🛡  ATO SHIELD V2 - FULL ML PIPELINE")
    print("=" * 80)
    print()
    
    # Get paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "paysim dataset.csv")
    data_dir = os.path.join(base_dir, "data", "processed")
    model_dir = os.path.join(base_dir, "engine", "models")
    
    # Verify dataset exists
    if not os.path.exists(data_path):
        print("❌ ERROR: PaySim dataset not found!")
        print(f"   Expected at: {data_path}")
        sys.exit(1)
    
    print(f"📊 Dataset: {data_path}")
    print(f"📁 Processed data: {data_dir}")
    print(f"📁 Model output: {model_dir}")
    print()
    
    # Phase 1.2: Preprocessing
    print("=" * 80)
    print(" STEP 1/5: Preprocessing")
    print("=" * 80)
    from pipeline.preprocessing import run_preprocessing
    X_train, X_test, y_train, y_test, feature_names = run_preprocessing(data_path, data_dir)
    
    # Phase 1.3: XGBoost
    print("\n")
    print("=" * 80)
    print(" STEP 2/5: XGBoost Training")
    print("=" * 80)
    from pipeline.train_xgboost import run_xgboost_training
    xgb_model, xgb_metrics = run_xgboost_training(data_dir, model_dir)
    
    # Phase 1.4: Isolation Forest
    print("\n")
    print("=" * 80)
    print(" STEP 3/5: Isolation Forest Training")
    print("=" * 80)
    from pipeline.train_isolation_forest import run_isolation_forest_training
    iso_model, iso_metrics = run_isolation_forest_training(data_dir, model_dir)
    
    # Phase 1.5: Test Scorer
    print("\n")
    print("=" * 80)
    print(" STEP 4/5: Scorer Service Test")
    print("=" * 80)
    from engine.scorer import create_scorer
    
    scorer = create_scorer(model_dir)
    
    # Test with sample transaction
    test_txn = {
        'step': 3,
        'type': 'CASH_OUT',
        'amount': 120000,
        'oldbalanceOrg': 150000,
        'newbalanceOrig': 30000,
        'oldbalanceDest': 0,
        'newbalanceDest': 120000,
        'AvgCustomerAmount': 8200,
    }
    
    score_result = scorer.score_transaction(test_txn)
    fraud_type = scorer.detect_fraud_type(test_txn, score_result['risk_score'])
    
    print(f"\n🧪 Test Transaction Scored:")
    print(f"   Risk Score: {score_result['risk_score']:.4f}")
    print(f"   Risk Level: {score_result['risk_level']}")
    print(f"   Fraud Type: {fraud_type}")
    
    # Phase 1.6: Test SHAP Explainer
    print("\n")
    print("=" * 80)
    print(" STEP 5/5: SHAP Explainer Test")
    print("=" * 80)
    from engine.explainer import create_explainer
    
    explainer = create_explainer(os.path.join(model_dir, "xgboost.pkl"))
    explanations = explainer.explain_to_dict(test_txn)
    
    print(f"\n💡 Explanations Generated:")
    for reason in explanations['reasons']:
        print(f"   • {reason}")
    
    # Final Summary
    print("\n")
    print("=" * 80)
    print(" ✅ PIPELINE COMPLETE - MODEL SUMMARY")
    print("=" * 80)
    print()
    print("📊 XGBoost Performance:")
    print(f"   Precision:  {xgb_metrics['precision']:.3f}")
    print(f"   Recall:     {xgb_metrics['recall']:.3f}")
    print(f"   F1 Score:   {xgb_metrics['f1']:.3f}")
    print(f"   ROC-AUC:    {xgb_metrics['roc_auc']:.3f}")
    print()
    print("📊 Isolation Forest Performance:")
    print(f"   Precision:  {iso_metrics['precision']:.3f}")
    print(f"   Recall:     {iso_metrics['recall']:.3f}")
    print(f"   F1 Score:   {iso_metrics['f1']:.3f}")
    print(f"   ROC-AUC:    {iso_metrics['roc_auc']:.3f}")
    print()
    print("📦 Models Saved:")
    print(f"   • {os.path.join(model_dir, 'xgboost.pkl')}")
    print(f"   • {os.path.join(model_dir, 'isolation_forest.pkl')}")
    print()
    print("=" * 80)
    print(" 🚀 ATO Shield v2 ML Engine Ready!")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline()
