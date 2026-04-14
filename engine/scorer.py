"""
ATO Shield v2 - Phase 1.5: ML Scoring Engine
Scores transactions using XGBoost + Isolation Forest fusion
"""
import joblib
import numpy as np
import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Scorer:
    """ML scoring engine for ATO Shield v2"""
    
    # Risk thresholds per master document
    THRESHOLD_HIGH = 0.70
    THRESHOLD_MEDIUM = 0.30
    
    # Fusion weights
    WEIGHT_XGB = 0.7
    WEIGHT_ISO = 0.3
    
    def __init__(self, model_dir: str = None):
        """Load trained models"""
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine", "models")
        
        # Load XGBoost
        xgb_path = os.path.join(model_dir, "xgboost.pkl")
        if os.path.exists(xgb_path):
            xgb_data = joblib.load(xgb_path)
            self.xgb_model = xgb_data['model']
            self.xgb_features = xgb_data['feature_names']
        else:
            raise FileNotFoundError(f"XGBoost model not found at {xgb_path}. Run pipeline first.")
        
        # Load Isolation Forest
        iso_path = os.path.join(model_dir, "isolation_forest.pkl")
        if os.path.exists(iso_path):
            self.iso_model = joblib.load(iso_path)
        else:
            raise FileNotFoundError(f"Isolation Forest model not found at {iso_path}. Run pipeline first.")
    
    def prepare_features(self, transaction: dict) -> pd.DataFrame:
        """Transform transaction dict into feature DataFrame"""
        df = pd.DataFrame([transaction])
        
        # Engineered features
        if 'step' in df.columns:
            df['TransactionHour'] = df['step'] % 24
        
        if 'amount' in df.columns and 'AvgCustomerAmount' in df.columns:
            df['AmountVsAverage'] = df['amount'] / (df['AvgCustomerAmount'] + 1e-8)
        
        if 'amount' in df.columns:
            # Use same threshold as training (95th percentile ~577,374)
            threshold = 577374.0
            df['IsLargeTransaction'] = (df['amount'] > threshold).astype(int)
        
        if 'TransactionHour' in df.columns:
            df['IsNightTransaction'] = ((df['TransactionHour'] >= 0) & (df['TransactionHour'] <= 5)).astype(int)
        
        if 'oldbalanceOrg' in df.columns and 'newbalanceOrig' in df.columns:
            df['BalanceChange'] = df['oldbalanceOrg'] - df['newbalanceOrig']
            df['IsBalanceDrained'] = (df['newbalanceOrig'] == 0).astype(int)
            df['BalanceError'] = abs(df['BalanceChange'] - df['amount'])
        
        if 'oldbalanceDest' in df.columns and 'newbalanceDest' in df.columns:
            df['DestBalanceChange'] = df['newbalanceDest'] - df['oldbalanceDest']
        
        # One-hot encode transaction type
        if 'type' in df.columns:
            for txn_type in ['CASH_OUT', 'PAYMENT', 'CASH_IN', 'TRANSFER', 'DEBIT']:
                df[f'type_{txn_type}'] = (df['type'] == txn_type).astype(int)
            df = df.drop(columns=['type'])
        
        # Drop ID columns
        df = df.drop(columns=[c for c in ['nameOrig', 'nameDest', 'step'] if c in df.columns], errors='ignore')
        
        # Ensure all required features are present
        for feature in self.xgb_features:
            if feature not in df.columns:
                df[feature] = 0
        
        # Select only the features the model expects
        df = df[self.xgb_features]
        
        return df
    
    def score_transaction(self, transaction: dict) -> dict:
        """Score a single transaction using fused models"""
        # Prepare features
        X = self.prepare_features(transaction)
        
        # XGBoost score (probability of fraud)
        xgb_proba = self.xgb_model.predict_proba(X)[0][1]
        
        # Isolation Forest score (convert anomaly score to 0-1 scale)
        iso_score_raw = self.iso_model.score_samples(X)[0]
        # Normalize: typical range is -0.6 to 0.6, invert so higher = more fraudulent
        iso_score = max(0, min(1, -iso_score_raw))
        
        # Score fusion
        final_score = (self.WEIGHT_XGB * xgb_proba) + (self.WEIGHT_ISO * iso_score)
        
        # Risk level
        if final_score >= self.THRESHOLD_HIGH:
            risk_level = "HIGH"
        elif final_score >= self.THRESHOLD_MEDIUM:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            'risk_score': float(final_score),
            'risk_level': risk_level,
            'xgb_score': float(xgb_proba),
            'iso_score': float(iso_score)
        }
    
    def detect_fraud_type(self, transaction: dict, score: float) -> str:
        """Determine fraud type based on transaction patterns"""
        # Check for ANO (anomaly) first - Isolation Forest outlier
        X = self.prepare_features(transaction)
        iso_pred = self.iso_model.predict(X)[0]
        
        if iso_pred == -1 and score >= self.THRESHOLD_HIGH:
            return "ANO"
        
        # Check for ATO (Account Takeover)
        # Pattern: New device + unusual hour + large amount
        is_night = transaction.get('IsNightTransaction', 0) == 1
        is_large = transaction.get('IsLargeTransaction', 0) == 1
        amount_vs_avg = transaction.get('AmountVsAverage', 1)
        
        if is_night and is_large and amount_vs_avg > 3:
            return "ATO"
        
        # Check for VEL (Velocity Fraud)
        # Pattern: Multiple rapid transactions (would need external context)
        # For now, check for uniform amounts
        if transaction.get('type_TRANSFER', 0) == 1 and is_night:
            return "VEL"
        
        # Check for AMT (Large Amount Anomaly)
        if is_large and amount_vs_avg > 10:
            return "AMT"
        
        # Check for NGT (Off-Hours Fraud)
        if is_night and transaction.get('amount', 0) > 50000:
            return "NGT"
        
        # Default to ANO for unknown patterns
        if score >= self.THRESHOLD_MEDIUM:
            return "ANO"
        
        return "ANO"


def create_scorer(model_dir: str = None) -> Scorer:
    """Factory function to create scorer"""
    return Scorer(model_dir)


# Singleton pattern for API usage
_scorer_instance = None

def get_scorer_singleton(model_dir: str = None) -> Scorer:
    """Get or create singleton scorer instance (thread-safe)"""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = Scorer(model_dir)
    return _scorer_instance


def reset_scorer_singleton():
    """Reset singleton (useful for testing or model reload)"""
    global _scorer_instance
    _scorer_instance = None


if __name__ == "__main__":
    print("=" * 80)
    print("ATO SHIELD V2 - PHASE 1.5: SCORER SERVICE TEST")
    print("=" * 80)
    
    # Create scorer
    scorer = create_scorer()
    
    # Test transaction
    test_transaction = {
        'step': 3,
        'type': 'CASH_OUT',
        'amount': 120000,
        'oldbalanceOrg': 150000,
        'newbalanceOrig': 30000,
        'oldbalanceDest': 0,
        'newbalanceDest': 120000,
        'AvgCustomerAmount': 8200,
    }
    
    # Score
    result = scorer.score_transaction(test_transaction)
    fraud_type = scorer.detect_fraud_type(test_transaction, result['risk_score'])
    
    print("\n🧪 Test Transaction:")
    print(f"   Amount: ₹{test_transaction['amount']:,.0f}")
    print(f"   Type: {test_transaction['type']}")
    print(f"   Hour: {test_transaction['step'] % 24}:00")
    print(f"   Customer Avg: ₹{test_transaction['AvgCustomerAmount']:,.0f}")
    
    print(f"\n📊 Scoring Result:")
    print(f"   XGBoost Score: {result['xgb_score']:.4f}")
    print(f"   Isolation Forest Score: {result['iso_score']:.4f}")
    print(f"   Final Score: {result['risk_score']:.4f}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Fraud Type: {fraud_type}")
    
    print("\n" + "=" * 80)
    print("✅ PHASE 1.5 COMPLETE - SCORER SERVICE")
    print("=" * 80)
