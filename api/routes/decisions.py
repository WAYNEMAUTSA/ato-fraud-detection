"""
ATO Shield v2 - Decision Route
POST /api/v1/cases/{case_id}/decision - Analyst acts on a case
"""
import httpx
import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from datetime import datetime

from store.database import get_db
from store.models import Bank, Case, Analyst, Transaction
from store.queries import record_decision, get_open_cases, get_open_case_count
from api.middleware.auth import validate_api_key
from api.schemas.transaction import DecisionCreate, DecisionResponse

router = APIRouter()


def _get_bank_or_demo(db: Session, auth_header: str | None = None) -> Bank:
    """
    Try to validate API key from Authorization header.
    If DEMO_MODE is enabled and no valid key is found, return a demo bank.
    """
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"

    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header.split("Bearer ")[1]
        bank = db.query(Bank).filter(Bank.api_key == api_key).first()
        if bank:
            return bank

    # Demo mode fallback
    if demo_mode:
        demo_bank = db.query(Bank).first()
        if demo_bank:
            return demo_bank
        # Create a temporary demo bank if none exists
        demo_bank = Bank(
            bank_id=uuid4(),
            name="Demo Bank",
            api_key="demo_key",
            webhook_url=None
        )
        db.add(demo_bank)
        db.commit()
        db.refresh(demo_bank)
        return demo_bank

    raise HTTPException(status_code=401, detail="Invalid API key. DEMO_MODE is disabled.")


@router.post("/cases/{case_id}/decision", response_model=DecisionResponse)
async def create_decision(
    case_id: str,  # String for SQLite UUID compatibility
    decision_data: DecisionCreate,
    authorization: str | None = Header(default=None),
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
    # Use demo-mode bank if no valid API key
    bank = _get_bank_or_demo(db, authorization)

    # Convert IDs to strings for SQLite compatibility
    bank_id_str = str(bank.bank_id)

    # Validate case exists - in demo mode, don't filter by bank_id
    demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
    
    if demo_mode:
        case = db.query(Case).filter(
            Case.case_id == case_id,
            Case.status == 'OPEN'
        ).first()
    else:
        case = db.query(Case).filter(
            Case.case_id == case_id,
            Case.bank_id == bank_id_str,
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
        # Use demo analyst - convert bank_id to string for SQLite
        demo_analyst = db.query(Analyst).filter(
            Analyst.bank_id == bank_id_str
        ).first()

        if demo_analyst:
            analyst_id = str(demo_analyst.analyst_id)
        else:
            # Create temporary analyst record
            analyst_id = str(uuid4())

    try:
        # Record decision - convert case_id string to UUID
        from uuid import UUID as PyUUID
        decision = record_decision(
            db,
            case_id=PyUUID(case_id),
            analyst_id=PyUUID(analyst_id),
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

        # Broadcast stats update to all connected WebSocket clients
        try:
            import api.websocket as ws_manager
            open_cases_count = get_open_case_count(db, bank_id=None)
            total_transactions = db.query(Transaction).count()
            
            # Calculate threat level
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

            await ws_manager.manager.broadcast_stats_update({
                'open_cases': open_cases_count,
                'screened_count': total_transactions,
                'threat_level': threat_level,
                'threat_label': threat_label,
                'threat_color': threat_color
            })
        except Exception as e:
            print(f"⚠️ Failed to broadcast stats update: {e}")

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
