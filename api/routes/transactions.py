"""
ATO Shield v2 - Transaction Ingestion Route
POST /api/v1/transaction - Bank submits transaction for scoring
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from store.database import get_db
from store.models import Transaction, Case, SHAPReason, Bank
from store.queries import get_bank_by_api_key
from api.middleware.auth import validate_api_key
from api.schemas.transaction import TransactionCreate, TransactionResponse
from engine.scorer import create_scorer
from engine.explainer import create_explainer
from api.websocket import manager

router = APIRouter()


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
        # Initialize ML engine
        scorer = create_scorer()
        explainer = create_explainer()
        
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
