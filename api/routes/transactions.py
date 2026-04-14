"""
ATO Shield v2 - Transaction Ingestion Route
POST /api/v1/transaction - Bank submits transaction for scoring
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta
import asyncio
import threading

from store.database import get_db
from store.models import Transaction, Case, SHAPReason, Bank
from store.queries import get_bank_by_api_key, get_open_case_count
from api.middleware.auth import validate_api_key
from api.schemas.transaction import TransactionCreate, TransactionResponse
from engine.scorer import get_scorer_singleton
from engine.explainer import get_explainer_singleton
from api.websocket import manager

router = APIRouter()


async def broadcast_dashboard_stats(db: Session):
    """Broadcast current dashboard stats via WebSocket after transaction"""
    try:
        # Get real transaction count
        total_transactions = db.query(Transaction).count()
        open_cases_count = get_open_case_count(db, bank_id=None)

        # Determine threat level
        if open_cases_count == 0:
            threat_level = "all-clear"
            threat_label = "ALL CLEAR"
            threat_color = "#27AE60"
        elif open_cases_count <= 3:
            threat_level = "elevated"
            threat_label = "ELEVATED"
            threat_color = "#F0A500"
        else:
            threat_level = "critical"
            threat_label = "CRITICAL"
            threat_color = "#E84040"

        # Calculate protected value
        resolved_cases = db.query(Case).filter(Case.status == "RESOLVED").all()
        protected_amount = 0
        for case in resolved_cases:
            txn = db.query(Transaction).filter(
                Transaction.transaction_id == case.transaction_id
            ).first()
            if txn:
                protected_amount += txn.payload.get('amount', 0)

        if protected_amount >= 100000:
            protected_value = f"{protected_amount / 100000:.2f}L"
        elif protected_amount >= 1000:
            protected_value = f"{protected_amount / 1000:.2f}K"
        else:
            protected_value = str(protected_amount)

        # Volume chart data
        now = datetime.now()
        time_buckets = []
        for i in range(5, -1, -1):
            bucket_time = now - timedelta(hours=i*4)
            time_buckets.append(bucket_time.strftime('%H:00'))

        volume_legit = []
        volume_flagged = []
        for i in range(6):
            bucket_start = now - timedelta(hours=(6-i)*4)
            bucket_end = bucket_start + timedelta(hours=4)

            legit_count = db.query(Transaction).filter(
                Transaction.received_at >= bucket_start,
                Transaction.received_at < bucket_end
            ).count()

            flagged_count = db.query(Case).filter(
                Case.created_at >= bucket_start,
                Case.created_at < bucket_end
            ).count()

            volume_legit.append(max(0, legit_count - flagged_count))
            volume_flagged.append(flagged_count)

        # Fraud type breakdown
        all_cases = db.query(Case).filter(Case.status == "OPEN").all()
        fraud_type_counts = {'ATO': 0, 'VEL': 0, 'AMT': 0, 'NGT': 0, 'ANO': 0}
        for case in all_cases:
            fraud_type = case.fraud_type or 'ANO'
            if fraud_type in fraud_type_counts:
                fraud_type_counts[fraud_type] += 1

        stats = {
            'open_cases': open_cases_count,
            'screened_count': total_transactions,
            'protected_value': protected_value,
            'threat_level': threat_level,
            'threat_label': threat_label,
            'threat_color': threat_color,
            'volume_labels': time_buckets,
            'volume_legit': volume_legit,
            'volume_flagged': volume_flagged,
            'fraud_type_data': [fraud_type_counts[ft] for ft in ['ATO', 'VEL', 'AMT', 'NGT', 'ANO']]
        }

        # Broadcast via WebSocket (non-blocking)
        await manager.broadcast_stats_update(stats)
    except Exception as e:
        print(f"⚠️ Failed to broadcast stats: {e}")



@router.post("/transaction", response_model=TransactionResponse)
async def ingest_transaction(
    txn: TransactionCreate,
    bank: Bank = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """
    Bank submits a transaction for fraud scoring.
    
    The transaction is:
    1. Validated (Pydantic schema)
    2. Stored in database
    3. Scored by ML engine (XGBoost + Isolation Forest)
    4. If MEDIUM/HIGH: case created, SHAP reasons generated
    5. If HIGH: WebSocket alert sent to connected analysts
    
    Returns: risk_score, risk_level, fraud_type, case_id (if flagged)
    """
    try:
        # Initialize ML engine (singleton - loaded once per application lifecycle)
        scorer = get_scorer_singleton()
        explainer = get_explainer_singleton()
        
        # Step 1: Store raw transaction
        transaction = Transaction(
            transaction_id=txn.transaction_id,
            bank_id=str(bank.bank_id),  # Convert to string for SQLite
            payload=txn.model_dump()
        )
        db.add(transaction)
        db.commit()
        
        # Step 2: Calculate additional features for scoring
        # Get customer's historical average (simplified for now)
        avg_customer_amount = txn.amount  # Fallback to current amount
        txn_dict = txn.model_dump()
        txn_dict['AvgCustomerAmount'] = avg_customer_amount
        
        # Step 3: Score transaction
        score_result = scorer.score_transaction(txn_dict)
        fraud_type = scorer.detect_fraud_type(txn_dict, score_result['risk_score'])
        
        # Step 4: If MEDIUM or HIGH, create case
        case_id = None
        recommended_action = None
        
        if score_result['risk_level'] in ['MEDIUM', 'HIGH']:
            # Create case
            case = Case(
                case_id=str(uuid4()),  # Convert to string for SQLite
                transaction_id=txn.transaction_id,
                bank_id=str(bank.bank_id),  # Convert to string for SQLite
                risk_score=score_result['risk_score'],
                risk_level=score_result['risk_level'],
                fraud_type=fraud_type,
                status='OPEN'
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            
            case_id = case.case_id
            
            # Generate SHAP explanations
            shap_explanations = explainer.explain_to_dict(txn_dict)
            
            # Store reasons
            for i, reason_text in enumerate(shap_explanations['reasons']):
                reason = SHAPReason(
                    reason_id=str(uuid4()),  # Convert to string for SQLite
                    case_id=case.case_id,
                    reason_text=reason_text,
                    display_order=i + 1
                )
                db.add(reason)
            
            db.commit()
            
            # Recommended action based on risk level
            if score_result['risk_level'] == 'HIGH':
                recommended_action = "BLOCK or FREEZE recommended"
            else:
                recommended_action = "REVIEW recommended"
            
            # Step 5: Send WebSocket alert for HIGH risk
            if score_result['risk_level'] == 'HIGH':
                alert = {
                    'type': 'new_case',
                    'case_id': str(case.case_id),
                    'risk_level': 'HIGH',
                    'fraud_type': fraud_type,
                    'customer_name': txn.nameOrig,
                    'amount': txn.amount,
                    'minutes_ago': 0
                }
                
                # Broadcast to all connected analysts
                await manager.broadcast_alert(alert)
        
        else:
            # LOW risk - no case, just log
            recommended_action = "No action required"

        # Broadcast updated dashboard stats (non-blocking background task)
        asyncio.create_task(broadcast_dashboard_stats(db))

        return TransactionResponse(
            transaction_id=txn.transaction_id,
            risk_score=score_result['risk_score'],
            risk_level=score_result['risk_level'],
            fraud_type=fraud_type if score_result['risk_level'] in ['MEDIUM', 'HIGH'] else None,
            case_id=case_id,
            recommended_action=recommended_action
        )
    
    except Exception as e:
        import traceback
        print(f"\n[ERROR] in transaction endpoint:")
        print(traceback.format_exc())
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing transaction: {str(e)}"
        )
