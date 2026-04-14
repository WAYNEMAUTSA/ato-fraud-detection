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
    if created_at is None:
        return 0
    try:
        now = datetime.now()
        delta = now - created_at
        return max(0, int(delta.total_seconds() / 60))
    except (TypeError, ValueError):
        return 0


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Screen 1: Operations Centre"""
    from store.models import Case

    # Get real transaction count
    total_transactions = db.query(Transaction).count()
    screened_count = total_transactions

    # Get open cases count
    open_cases_count = get_open_case_count(db, bank_id=None)

    # Determine threat level based on open cases
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

    # Calculate protected value (sum of amounts in resolved/blocked cases)
    resolved_cases = db.query(Case).filter(Case.status == "RESOLVED").all()
    protected_amount = 0
    for case in resolved_cases:
        txn = db.query(Transaction).filter(
            Transaction.transaction_id == case.transaction_id
        ).first()
        if txn:
            protected_amount += txn.payload.get('amount', 0)

    # Format protected value
    if protected_amount >= 100000:
        protected_value = f"{protected_amount / 100000:.2f}L"
    elif protected_amount >= 1000:
        protected_value = f"{protected_amount / 1000:.2f}K"
    else:
        protected_value = str(protected_amount)

    # Get recent cases for display (last 3 open cases)
    cases = get_open_cases(db, bank_id=None, limit=3)
    recent_cases = []
    for case in cases:
        txn = db.query(Transaction).filter(
            Transaction.transaction_id == case.transaction_id
        ).first()
        recent_cases.append({
            'case_id': str(case.case_id),
            'risk_level': case.risk_level or 'LOW',
            'amount': txn.payload.get('amount', 0) if txn else 0,
            'minutes_ago': minutes_ago(case.created_at),
            'fraud_type': case.fraud_type or 'ANO'
        })

    # Volume chart data - real data from transactions grouped by time
    from datetime import datetime, timedelta
    now = datetime.now()
    time_buckets = []
    for i in range(5, -1, -1):
        bucket_time = now - timedelta(hours=i*4)
        time_buckets.append(bucket_time.strftime('%H:00'))

    # Count transactions in each time bucket
    volume_legit = []
    volume_flagged = []
    for i, bucket_start in enumerate([(now - timedelta(hours=(6-i)*4)) for i in range(6)]):
        bucket_end = bucket_start + timedelta(hours=4)

        # Count legitimate transactions (LOW risk - no case created)
        legit_count = db.query(Transaction).filter(
            Transaction.received_at >= bucket_start,
            Transaction.received_at < bucket_end
        ).count()

        # Count flagged transactions (have associated cases)
        flagged_count = db.query(Case).filter(
            Case.created_at >= bucket_start,
            Case.created_at < bucket_end
        ).count()

        # Adjust legit count to exclude flagged
        volume_legit.append(max(0, legit_count - flagged_count))
        volume_flagged.append(flagged_count)

    # Fraud type breakdown - real data from open cases
    all_cases = get_open_cases(db, bank_id=None, limit=1000)
    fraud_type_counts = {'ATO': 0, 'VEL': 0, 'AMT': 0, 'NGT': 0, 'ANO': 0}
    for case in all_cases:
        fraud_type = case.fraud_type or 'ANO'
        if fraud_type in fraud_type_counts:
            fraud_type_counts[fraud_type] += 1

    fraud_type_labels = ['ATO', 'VEL', 'AMT', 'NGT', 'ANO']
    fraud_type_data = [fraud_type_counts[ft] for ft in fraud_type_labels]

    return templates.TemplateResponse("operations_centre.html", {
        "request": request,
        "active_page": "dashboard",
        "threat_level": threat_level,
        "threat_label": threat_label,
        "threat_color": threat_color,
        "open_cases": open_cases_count,
        "screened_count": screened_count,
        "protected_value": protected_value,
        "recent_cases": recent_cases,
        "volume_labels": time_buckets,
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
            'risk_level': case.risk_level or 'LOW',
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

    # Format case_id for display
    case_id_str = str(case.case_id)
    case_id_short = case_id_str[:8].upper() if len(case_id_str) >= 8 else case_id_str.upper()

    return templates.TemplateResponse("case_investigation.html", {
        "request": request,
        "active_page": "cases",
        "case_id": case_id,
        "case": {
            'case_id': str(case.case_id),
            'transaction_id': case.transaction_id,
            'risk_level': case.risk_level or 'LOW',
            'fraud_type': case.fraud_type,
            'status': case.status,
            'minutes_ago': minutes_ago(case.created_at),
            'transaction': txn.payload if txn else {},
            'customer': customer_profile,
            'reasons': [r.reason_text for r in reasons],
            'recent_activity': [],  # Would be populated from transaction history
            'case_id_short': case_id_short
        }
    })
