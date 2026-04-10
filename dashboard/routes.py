"""
ATO Shield v2 - Dashboard Routes
Handles rendering of all three dashboard screens with real data
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from store.database import get_db
from store.queries import get_open_cases, get_open_case_count
from store.models import Transaction, SHAPReason

router = APIRouter()
templates = Jinja2Templates(directory="dashboard/templates")


def minutes_ago(created_at) -> int:
    """Calculate minutes between creation and now"""
    from datetime import datetime
    if not created_at:
        return 0
    now = datetime.now()
    delta = now - created_at
    return max(0, int(delta.total_seconds() / 60))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Screen 1: Operations Centre"""
    # Get open cases count
    open_cases_count = get_open_case_count(db, bank_id=None)  # Will be scoped properly with auth
    
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
    
    # Get recent cases for display
    cases = get_open_cases(db, bank_id=None, limit=3)
    recent_cases = []
    for case in cases:
        txn = db.query(Transaction).filter(
            Transaction.transaction_id == case.transaction_id
        ).first()
        recent_cases.append({
            'case_id': str(case.case_id),
            'risk_level': case.risk_level,
            'amount': txn.payload.get('amount', 0) if txn else 0,
            'minutes_ago': minutes_ago(case.created_at),
            'fraud_type': case.fraud_type or 'ANO'
        })
    
    # Volume chart data (mock for now - will be real in Phase 4)
    volume_labels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
    volume_legit = [120, 80, 350, 520, 480, 290]
    volume_flagged = [2, 1, 5, 8, 6, 4]
    
    # Fraud type breakdown
    fraud_type_labels = ['ATO', 'VEL', 'AMT', 'NGT', 'ANO']
    fraud_type_data = [3, 2, 1, 2, 1]
    
    return templates.TemplateResponse("operations_centre.html", {
        "request": request,
        "active_page": "dashboard",
        "threat_level": threat_level,
        "threat_label": threat_label,
        "threat_color": threat_color,
        "open_cases": open_cases_count,
        "screened_count": 1850,
        "protected_value": "42,31,500",
        "recent_cases": recent_cases,
        "volume_labels": volume_labels,
        "volume_legit": volume_legit,
        "volume_flagged": volume_flagged,
        "fraud_type_labels": fraud_type_labels,
        "fraud_type_data": fraud_type_data
    })


@router.get("/queue", response_class=HTMLResponse)
async def alert_queue(request: Request, db: Session = Depends(get_db)):
    """Screen 2: Alert Queue"""
    cases = get_open_cases(db, bank_id=None, limit=50)
    
    case_list = []
    for case in cases:
        txn = db.query(Transaction).filter(
            Transaction.transaction_id == case.transaction_id
        ).first()
        
        # Get first SHAP reason
        reason = db.query(SHAPReason).filter(
            SHAPReason.case_id == case.case_id
        ).order_by(SHAPReason.display_order).first()
        
        case_list.append({
            'case_id': str(case.case_id),
            'risk_level': case.risk_level,
            'fraud_type': case.fraud_type,
            'customer_name': txn.payload.get('nameOrig', 'Unknown') if txn else 'Unknown',
            'amount': txn.payload.get('amount', 0) if txn else 0,
            'reason_summary': reason.reason_text if reason else 'Flagged for review',
            'minutes_ago': minutes_ago(case.created_at)
        })
    
    return templates.TemplateResponse("alert_queue.html", {
        "request": request,
        "active_page": "queue",
        "cases": case_list,
        "open_case_count": len(case_list)
    })


@router.get("/case/{case_id}", response_class=HTMLResponse)
async def case_investigation(request: Request, case_id: str, db: Session = Depends(get_db)):
    """Screen 3: Case Investigation"""
    from store.models import Case
    
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if not case:
        return HTMLResponse("Case not found", status_code=404)
    
    # Get transaction
    txn = db.query(Transaction).filter(
        Transaction.transaction_id == case.transaction_id
    ).first()
    
    # Get SHAP reasons
    reasons = db.query(SHAPReason).filter(
        SHAPReason.case_id == case_id
    ).order_by(SHAPReason.display_order).all()
    
    # Build customer profile
    customer_profile = {
        'name': txn.payload.get('nameOrig', 'Unknown') if txn else 'Unknown',
        'account_id': txn.payload.get('nameOrig', 'Unknown') if txn else 'Unknown',
        'avg_transaction': txn.payload.get('AvgCustomerAmount', txn.payload.get('amount', 0)) if txn else 0,
        'city': 'Unknown'
    }
    
    return templates.TemplateResponse("case_investigation.html", {
        "request": request,
        "active_page": "cases",
        "case_id": case_id,
        "case": {
            'case_id': str(case.case_id),
            'transaction_id': case.transaction_id,
            'risk_level': case.risk_level,
            'fraud_type': case.fraud_type,
            'status': case.status,
            'minutes_ago': minutes_ago(case.created_at),
            'transaction': txn.payload if txn else {},
            'customer': customer_profile,
            'reasons': [r.reason_text for r in reasons],
            'recent_activity': []  # Would be populated from transaction history
        }
    })
