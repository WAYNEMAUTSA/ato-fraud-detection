"""
ATO Shield v2 - Reusable Database Query Functions
"""
from uuid import UUID
from sqlalchemy.orm import Session
from store.models import Case, SHAPReason, Decision, Transaction, Analyst, Bank


def get_open_cases(db: Session, bank_id: UUID, limit: int = 50):
    """Get open cases for a bank, ordered by risk score (highest first)"""
    return (
        db.query(Case)
        .filter(Case.bank_id == bank_id, Case.status == "OPEN")
        .order_by(Case.risk_score.desc(), Case.created_at.asc())
        .limit(limit)
        .all()
    )


def get_case_by_id(db: Session, case_id: UUID, bank_id: UUID):
    """Get full case details including SHAP reasons"""
    case = (
        db.query(Case)
        .filter(Case.case_id == case_id, Case.bank_id == bank_id)
        .first()
    )
    
    if not case:
        return None
    
    reasons = (
        db.query(SHAPReason)
        .filter(SHAPReason.case_id == case_id)
        .order_by(SHAPReason.display_order)
        .all()
    )
    
    return {
        "case": case,
        "reasons": [r.reason_text for r in reasons]
    }


def get_case_transaction(db: Session, case_id: UUID, bank_id: UUID):
    """Get transaction data for a case"""
    from sqlalchemy import select
    
    case = db.query(Case).filter(Case.case_id == case_id, Case.bank_id == bank_id).first()
    if not case:
        return None
    
    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == case.transaction_id
    ).first()
    
    return transaction


def record_decision(db: Session, case_id: UUID, analyst_id: UUID, action: str):
    """Record analyst decision"""
    decision = Decision(
        case_id=case_id,
        analyst_id=analyst_id,
        action=action
    )
    db.add(decision)
    
    # Mark case as resolved
    case = db.query(Case).filter(Case.case_id == case_id).first()
    if case:
        case.status = "RESOLVED"
    
    db.commit()
    return decision


def get_analyst_by_email(db: Session, email: str):
    """Get analyst by email"""
    return db.query(Analyst).filter(Analyst.email == email).first()


def get_bank_by_api_key(db: Session, api_key: str):
    """Get bank by API key"""
    return db.query(Bank).filter(Bank.api_key == api_key).first()


def get_open_case_count(db: Session, bank_id: UUID):
    """Get count of open cases for a bank"""
    return (
        db.query(Case)
        .filter(Case.bank_id == bank_id, Case.status == "OPEN")
        .count()
    )
