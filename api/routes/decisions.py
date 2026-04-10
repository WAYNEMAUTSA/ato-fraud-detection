"""
ATO Shield v2 - Decision Route
POST /api/v1/cases/{case_id}/decision - Analyst acts on a case
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime

from store.database import get_db
from store.models import Bank, Case, Analyst
from store.queries import record_decision, get_open_cases
from api.middleware.auth import validate_api_key
from api.schemas.transaction import DecisionCreate, DecisionResponse

router = APIRouter()


@router.post("/cases/{case_id}/decision", response_model=DecisionResponse)
async def create_decision(
    case_id: UUID,
    decision_data: DecisionCreate,
    bank: Bank = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """
    Analyst makes a decision on a case.
    
    Actions: BLOCK, FREEZE, ESCALATE, CLEAR
    
    Side effects:
    1. Decision recorded in database
    2. Case marked as RESOLVED
    3. Webhook sent to bank's endpoint
    4. Returns next open case ID for auto-advance
    """
    # Validate case exists and belongs to this bank
    case = db.query(Case).filter(
        Case.case_id == case_id,
        Case.bank_id == bank.bank_id,
        Case.status == 'OPEN'
    ).first()
    
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found or already resolved"
        )
    
    # Validate action
    valid_actions = ['BLOCK', 'FREEZE', 'ESCALATE', 'CLEAR']
    if decision_data.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}"
        )
    
    # Get or create dummy analyst for demo
    analyst_id = decision_data.analyst_id
    if not analyst_id:
        # Use demo analyst
        demo_analyst = db.query(Analyst).filter(
            Analyst.bank_id == bank.bank_id
        ).first()
        
        if demo_analyst:
            analyst_id = str(demo_analyst.analyst_id)
        else:
            # Create temporary analyst record
            analyst_id = str(uuid4())
    
    try:
        # Record decision
        decision = record_decision(
            db,
            case_id=case_id,
            analyst_id=UUID(analyst_id),
            action=decision_data.action
        )
        
        # Send webhook to bank
        if bank.webhook_url:
            await send_bank_webhook(
                bank.webhook_url,
                {
                    'case_id': str(case_id),
                    'transaction_id': case.transaction_id,
                    'action': decision_data.action,
                    'bank_id': str(bank.bank_id),
                    'decided_at': str(datetime.now())
                }
            )
        
        # Get next open case for auto-advance
        next_cases = get_open_cases(db, bank.bank_id, limit=1)
        next_case_id = next_cases[0].case_id if next_cases else None
        
        return DecisionResponse(
            decision_id=decision.decision_id,
            case_id=case_id,
            action=decision_data.action,
            decided_at=decision.decided_at,
            next_case_id=next_case_id
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing decision: {str(e)}"
        )


async def send_bank_webhook(webhook_url: str, payload: dict):
    """Send decision notification to bank's webhook endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0
            )
            # Log success/failure but don't fail the request
            if response.status_code != 200:
                print(f"⚠️  Webhook failed: {response.status_code} - {response.text}")
    except Exception as e:
        # Webhook failure shouldn't block analyst workflow
        print(f"⚠️  Webhook error: {str(e)}")
