"""
ATO Shield v2 - Pydantic Schemas for API Validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ---- Transaction Ingestion ----

class TransactionCreate(BaseModel):
    """Bank submits a transaction for scoring"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    step: int = Field(..., description="Time step (1-hour window)")
    type: str = Field(..., description="Transaction type: PAYMENT, TRANSFER, CASH_OUT, CASH_IN, DEBIT")
    amount: float = Field(..., gt=0, description="Transaction amount")
    nameOrig: str = Field(..., description="Originating customer ID")
    oldbalanceOrg: float = Field(..., ge=0, description="Balance before transaction")
    newbalanceOrig: float = Field(..., ge=0, description="Balance after transaction")
    nameDest: str = Field(..., description="Destination account ID")
    oldbalanceDest: float = Field(..., ge=0, description="Destination balance before")
    newbalanceDest: float = Field(..., ge=0, description="Destination balance after")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "transaction_id": "TXN_9821ABC",
                    "step": 3,
                    "type": "CASH_OUT",
                    "amount": 120000.00,
                    "nameOrig": "C1231006815",
                    "oldbalanceOrg": 150000.00,
                    "newbalanceOrig": 30000.00,
                    "nameDest": "M840083671",
                    "oldbalanceDest": 0.00,
                    "newbalanceDest": 120000.00
                }
            ]
        }
    }


class TransactionResponse(BaseModel):
    """API response after transaction scoring"""
    transaction_id: str
    risk_score: float
    risk_level: str  # HIGH, MEDIUM, LOW
    fraud_type: Optional[str] = None  # ATO, VEL, AMT, NGT, ANO
    case_id: Optional[UUID] = None  # Only present if MEDIUM or HIGH
    recommended_action: Optional[str] = None


# ---- Case Management ----

class CaseSummary(BaseModel):
    """Lightweight case info for alert queue"""
    case_id: UUID
    transaction_id: str
    risk_score: float
    risk_level: str
    fraud_type: Optional[str]
    status: str
    created_at: datetime
    
    # Customer context
    customer_name: Optional[str] = None
    amount: Optional[float] = None
    reason_summary: Optional[str] = None  # One-line summary
    minutes_ago: Optional[int] = None


class CaseDetail(BaseModel):
    """Full case investigation view"""
    case_id: UUID
    transaction_id: str
    risk_score: float
    risk_level: str
    fraud_type: Optional[str]
    status: str
    created_at: datetime
    minutes_ago: int
    
    # Transaction details
    transaction: dict
    
    # Customer profile
    customer: dict
    
    # SHAP explanations
    reasons: list[str]
    
    # Recent activity
    recent_activity: Optional[list[dict]] = None


# ---- Decisions ----

class DecisionCreate(BaseModel):
    """Analyst action on a case"""
    action: str = Field(..., description="BLOCK, FREEZE, ESCALATE, or CLEAR")
    analyst_id: Optional[str] = None  # Can be None for demo


class DecisionResponse(BaseModel):
    decision_id: UUID
    case_id: UUID
    action: str
    decided_at: datetime
    next_case_id: Optional[UUID] = None  # Auto-advance to next open case


# ---- WebSocket Alerts ----

class WSAlert(BaseModel):
    """Real-time alert pushed to dashboard"""
    type: str = "new_case"
    case_id: UUID
    risk_level: str
    fraud_type: Optional[str]
    customer_name: Optional[str]
    amount: Optional[float]
    minutes_ago: int
