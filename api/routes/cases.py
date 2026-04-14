"""
ATO Shield v2 - Case Management Routes
GET /api/v1/cases - List open cases
GET /api/v1/cases/{case_id} - Full case detail
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta

from store.database import get_db
from store.models import Bank, Transaction, SHAPReason
from store.queries import get_open_cases, get_case_by_id, get_case_transaction
from api.middleware.auth import validate_api_key
from api.schemas.transaction import CaseSummary, CaseDetail

router = APIRouter()


def minutes_ago(created_at: datetime) -> int:
    """Calculate minutes between case creation and now"""
    if created_at is None:
        return 0
    try:
        now = datetime.now()
        delta = now - created_at
        return max(0, int(delta.total_seconds() / 60))
    except (TypeError, ValueError):
        return 0


@router.get("/cases", response_model=list[CaseSummary])
async def list_cases(
    bank: Bank = Depends(validate_api_key),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    Get open cases for this bank, ordered by risk score (highest first).
    Returns lightweight summaries for the alert queue.
    """
    cases = get_open_cases(db, bank.bank_id, limit)
    
    summaries = []
    for case in cases:
        # Get transaction payload for context
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == case.transaction_id
        ).first()
        
        txn_payload = transaction.payload if transaction else {}
        
        # Get first SHAP reason as one-line summary
        first_reason = db.query(SHAPReason).filter(
            SHAPReason.case_id == case.case_id
        ).order_by(SHAPReason.display_order).first()
        
        summaries.append(CaseSummary(
            case_id=case.case_id,
            transaction_id=case.transaction_id,
            risk_score=case.risk_score,
            risk_level=case.risk_level,
            fraud_type=case.fraud_type,
            status=case.status,
            created_at=case.created_at,
            customer_name=txn_payload.get('nameOrig'),
            amount=txn_payload.get('amount'),
            reason_summary=first_reason.reason_text if first_reason else None,
            minutes_ago=minutes_ago(case.created_at)
        ))
    
    return summaries


@router.get("/cases/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: str,
    bank: Bank = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """
    Get full case detail for investigation screen.
    Includes transaction, customer profile, SHAP reasons, and recent activity.
    """
    case_data = get_case_by_id(db, case_id, str(bank.bank_id))

    if not case_data:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = case_data['case']
    reasons = case_data['reasons']
    
    # Get transaction
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == case.transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    txn_payload = transaction.payload
    
    # Build customer profile (simplified from transaction data)
    customer_profile = {
        'name': txn_payload.get('nameOrig', 'Unknown'),
        'account_id': txn_payload.get('nameOrig', 'Unknown'),
        'avg_transaction': txn_payload.get('AvgCustomerAmount', txn_payload.get('amount', 0)),
        'city': 'Unknown',  # Would come from bank's customer data
    }
    
    # Get recent activity (last 5 transactions for this customer)
    # Note: SQLite JSON query - get all transactions and filter in Python
    recent_txns = db.query(Transaction).filter(
        Transaction.bank_id == bank.bank_id
    ).order_by(
        Transaction.received_at.desc()
    ).limit(50).all()  # Get recent transactions to filter

    recent_activity = []
    customer_name = txn_payload.get('nameOrig')
    # Filter in Python for SQLite compatibility
    for txn in recent_txns:
        if txn.payload.get('nameOrig') == customer_name and txn.transaction_id != txn_payload.get('transaction_id'):
            recent_activity.append({
                'amount': txn.payload.get('amount'),
                'type': txn.payload.get('type'),
                'time': str(txn.received_at),
                'destination': txn.payload.get('nameDest')
            })
        if len(recent_activity) >= 5:
            break
    
    return CaseDetail(
        case_id=case.case_id,
        transaction_id=case.transaction_id,
        risk_score=case.risk_score,
        risk_level=case.risk_level,
        fraud_type=case.fraud_type,
        status=case.status,
        created_at=case.created_at,
        minutes_ago=minutes_ago(case.created_at),
        transaction=txn_payload,
        customer=customer_profile,
        reasons=reasons,
        recent_activity=recent_activity[:5]
    )
