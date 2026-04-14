"""
ATO Shield v2 - Dashboard Stats Route
GET /api/v1/dashboard/stats - Get current dashboard statistics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from store.database import get_db
from store.models import Transaction, Case, SHAPReason, Decision
from store.queries import get_open_cases, get_open_case_count

router = APIRouter()


@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get current dashboard statistics for real-time updates"""
    
    # Get real transaction count
    total_transactions = db.query(Transaction).count()
    
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
    
    # Volume chart data
    now = datetime.now()
    time_buckets = []
    for i in range(5, -1, -1):
        bucket_time = now - timedelta(hours=i*4)
        time_buckets.append(bucket_time.strftime('%H:00'))
    
    # Count transactions in each time bucket
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
    all_cases = get_open_cases(db, bank_id=None, limit=1000)
    fraud_type_counts = {'ATO': 0, 'VEL': 0, 'AMT': 0, 'NGT': 0, 'ANO': 0}
    for case in all_cases:
        fraud_type = case.fraud_type or 'ANO'
        if fraud_type in fraud_type_counts:
            fraud_type_counts[fraud_type] += 1
    
    # ---- Analyst Profile Stats (demo analyst) ----
    DEMO_ANALYST_ID = "demo"

    # Count decisions by the demo analyst
    analyst_decisions = db.query(Decision).filter(
        Decision.analyst_id == DEMO_ANALYST_ID
    ).all()

    analyst_cases_reviewed = len(analyst_decisions)
    analyst_blocked = sum(1 for d in analyst_decisions if d.action == "BLOCK")
    analyst_frozen = sum(1 for d in analyst_decisions if d.action == "FREEZE")
    analyst_escalated = sum(1 for d in analyst_decisions if d.action == "ESCALATE")
    analyst_cleared = sum(1 for d in analyst_decisions if d.action == "CLEAR")

    # Calculate accuracy rate: (blocked + cleared correct) / total
    # For now, assume BLOCK and CLEAR decisions are "correct" actions
    correct_decisions = analyst_blocked + analyst_cleared
    analyst_accuracy = round((correct_decisions / analyst_cases_reviewed * 100), 1) if analyst_cases_reviewed > 0 else 0.0

    # Average review time (stubbed - would need case.created_at vs decision.decided_at diff)
    analyst_avg_time = 3.5  # minutes (stub value)

    # Last 5 decisions with action, case_id, timestamp
    recent_decisions = db.query(Decision).filter(
        Decision.analyst_id == DEMO_ANALYST_ID
    ).order_by(Decision.decided_at.desc()).limit(5).all()

    analyst_recent_activity = [
        {
            "action": d.action,
            "case_id": str(d.case_id),
            "timestamp": d.decided_at.isoformat() if d.decided_at else None
        }
        for d in recent_decisions
    ]

    return {
        'open_cases': open_cases_count,
        'screened_count': total_transactions,
        'protected_value': protected_value,
        'threat_level': threat_level,
        'threat_label': threat_label,
        'threat_color': threat_color,
        'volume_labels': time_buckets,
        'volume_legit': volume_legit,
        'volume_flagged': volume_flagged,
        'fraud_type_data': [fraud_type_counts[ft] for ft in ['ATO', 'VEL', 'AMT', 'NGT', 'ANO']],
        # Analyst profile stats
        'analyst_cases_reviewed': analyst_cases_reviewed,
        'analyst_blocked': analyst_blocked,
        'analyst_frozen': analyst_frozen,
        'analyst_escalated': analyst_escalated,
        'analyst_cleared': analyst_cleared,
        'analyst_accuracy': analyst_accuracy,
        'analyst_avg_time': analyst_avg_time,
        'analyst_recent_activity': analyst_recent_activity
    }
