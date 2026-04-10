"""
ATO Shield v2 - Phase 4: PaySim Transaction Simulator
Samples real PaySim transactions and posts them to the API
"""
import pandas as pd
import requests
import time
import random
import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TransactionSimulator:
    """Simulates live bank transaction flow using PaySim data"""
    
    def __init__(self, data_path: str, api_url: str = "http://localhost:8000", api_key: str = "ask_live_demo_key_12345"):
        self.api_url = api_url
        self.api_key = api_key
        self.running = False
        
        print("📥 Loading PaySim dataset...")
        self.df = pd.read_csv(data_path)
        print(f"   ✅ Loaded {len(self.df):,} transactions")
        
        # Separate fraud and legitimate transactions
        self.fraud_txns = self.df[self.df['isFraud'] == 1]
        self.legit_txns = self.df[self.df['isFraud'] == 0]
        
        print(f"   📊 Fraud transactions: {len(self.fraud_txns):,}")
        print(f"   📊 Legitimate transactions: {len(self.legit_txns):,}")
    
    def sample_transaction(self, fraud_weight: float = 0.15) -> dict:
        """Sample a random transaction from PaySim data"""
        if random.random() < fraud_weight:
            # Sample fraud transaction
            txn = self.fraud_txns.sample(n=1).iloc[0]
        else:
            # Sample legitimate transaction
            txn = self.legit_txns.sample(n=1).iloc[0]
        
        # Generate unique transaction ID
        txn_id = f"TXN_SIM_{uuid4().hex[:8].upper()}"
        
        return {
            "transaction_id": txn_id,
            "step": int(txn['step']),
            "type": txn['type'],
            "amount": float(txn['amount']),
            "nameOrig": txn['nameOrig'],
            "oldbalanceOrg": float(txn['oldbalanceOrg']),
            "newbalanceOrig": float(txn['newbalanceOrig']),
            "nameDest": txn['nameDest'],
            "oldbalanceDest": float(txn['oldbalanceDest']),
            "newbalanceDest": float(txn['newbalanceDest']),
            "is_fraud": bool(txn['isFraud'])  # For our tracking only
        }
    
    def post_transaction(self, txn: dict) -> dict:
        """Post transaction to ATO Shield API"""
        # Remove internal tracking field
        api_payload = {k: v for k, v in txn.items() if k != 'is_fraud'}
        
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/transaction",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=api_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                result['actual_fraud'] = txn['is_fraud']
                return result
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
        
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to ATO Shield API"}
        except requests.exceptions.Timeout:
            return {"error": "Request timeout"}
    
    def run_simulation(self, count: int = 100, speed: float = 0.5, fraud_weight: float = 0.15):
        """Run continuous transaction simulation"""
        print("\n" + "=" * 80)
        print(" 🔄 ATO SHIELD V2 - TRANSACTION SIMULATOR")
        print("=" * 80)
        print(f"\n📊 Simulating {count} transactions...")
        print(f"⚡ Speed: {speed}s between transactions")
        print(f"🎯 Fraud rate: {fraud_weight*100:.0f}%")
        print(f"🔗 API: {self.api_url}")
        print("\n" + "-" * 80)
        
        self.running = True
        stats = {
            'total': 0,
            'low': 0,
            'medium': 0,
            'high': 0,
            'fraud_detected': 0,
            'fraud_missed': 0,
            'false_positives': 0
        }
        
        start_time = time.time()
        
        try:
            for i in range(count):
                if not self.running:
                    break
                
                # Sample and post transaction
                txn = self.sample_transaction(fraud_weight=fraud_weight)
                result = self.post_transaction(txn)
                
                # Update stats
                stats['total'] += 1
                
                if 'error' in result:
                    print(f"\n❌ Transaction {i+1}: {result['error']}")
                    continue
                
                risk_level = result.get('risk_level', 'UNKNOWN')
                stats[risk_level.lower()] = stats.get(risk_level.lower(), 0) + 1
                
                # Check detection accuracy
                actual_fraud = result.get('actual_fraud', False)
                if actual_fraud and risk_level in ['MEDIUM', 'HIGH']:
                    stats['fraud_detected'] += 1
                    emoji = "🎯"
                elif actual_fraud and risk_level == 'LOW':
                    stats['fraud_missed'] += 1
                    emoji = "❌"
                elif not actual_fraud and risk_level in ['MEDIUM', 'HIGH']:
                    stats['false_positives'] += 1
                    emoji = "⚠️"
                else:
                    emoji = "✅"
                
                # Print result
                case_id = result.get('case_id', '')
                fraud_type = result.get('fraud_type') or ''
                
                print(f"{emoji} [{i+1:3d}/{count}] {txn['type']:10s} Rs.{txn['amount']:>12,.2f} -> {risk_level:6s} {fraud_type:3s} Case: {str(case_id)[:8] if case_id else 'N/A':8s}")
                
                # Progress indicator every 10 transactions
                if (i + 1) % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    print(f"   └─ Rate: {rate:.1f} txn/s | HIGH: {stats['high']} | MEDIUM: {stats['medium']} | LOW: {stats['low']}")
                
                time.sleep(speed)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Simulation stopped by user")
        
        # Final statistics
        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print(" 📊 SIMULATION RESULTS")
        print("=" * 80)
        print(f"\n⏱️  Duration: {elapsed:.1f}s")
        print(f"📈 Rate: {stats['total']/elapsed:.1f} transactions/second")
        print(f"\n📋 Risk Distribution:")
        print(f"   LOW:     {stats['low']:3d} ({stats['low']/stats['total']*100:.1f}%)")
        print(f"   MEDIUM:  {stats['medium']:3d} ({stats['medium']/stats['total']*100:.1f}%)")
        print(f"   HIGH:    {stats['high']:3d} ({stats['high']/stats['total']*100:.1f}%)")
        print(f"\n🎯 Detection Performance:")
        total_fraud = stats['fraud_detected'] + stats['fraud_missed']
        if total_fraud > 0:
            detection_rate = stats['fraud_detected'] / total_fraud * 100
            print(f"   Fraud Detected: {stats['fraud_detected']}/{total_fraud} ({detection_rate:.1f}%)")
            print(f"   Fraud Missed:   {stats['fraud_missed']}/{total_fraud}")
        print(f"   False Positives: {stats['false_positives']}")
        print("\n" + "=" * 80)
    
    def stop(self):
        """Stop the simulation"""
        self.running = False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ATO Shield Transaction Simulator')
    parser.add_argument('--count', type=int, default=100, help='Number of transactions to simulate')
    parser.add_argument('--speed', type=float, default=0.5, help='Seconds between transactions')
    parser.add_argument('--fraud-rate', type=float, default=0.15, help='Fraud transaction rate (0-1)')
    parser.add_argument('--data-path', type=str, default=None, help='Path to PaySim CSV')
    
    args = parser.parse_args()
    
    # Find PaySim data
    if args.data_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args.data_path = os.path.join(base_dir, "paysim dataset.csv")
    
    if not os.path.exists(args.data_path):
        print(f"❌ PaySim dataset not found at: {args.data_path}")
        sys.exit(1)
    
    # Run simulation
    simulator = TransactionSimulator(
        data_path=args.data_path,
        api_url="http://localhost:8000",
        api_key="ask_live_demo_key_12345"
    )
    
    simulator.run_simulation(
        count=args.count,
        speed=args.speed,
        fraud_weight=args.fraud_rate
    )
