"""
ATO Shield v2 - SQLAlchemy ORM Models
"""
import os
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from store.database import Base

# Check if we're using SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ato_shield_dev.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite")


def UUIDColumn(**kwargs):
    """UUID column that works with both PostgreSQL and SQLite"""
    if IS_SQLITE:
        return Column(Text, **kwargs)  # SQLite stores UUID as string
    return Column(UUID(as_uuid=True), **kwargs)


class Bank(Base):
    __tablename__ = "banks"

    bank_id = UUIDColumn(primary_key=True)
    name = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False)
    webhook_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())


class Analyst(Base):
    __tablename__ = "analysts"

    analyst_id = UUIDColumn(primary_key=True)
    bank_id = UUIDColumn()
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(255), primary_key=True)
    bank_id = UUIDColumn()
    payload = Column(JSON, nullable=False)
    received_at = Column(DateTime, server_default=func.now())


class Case(Base):
    __tablename__ = "cases"

    case_id = UUIDColumn(primary_key=True)
    transaction_id = Column(String(255))
    bank_id = UUIDColumn()
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(10), nullable=False)  # HIGH / MEDIUM / LOW
    fraud_type = Column(String(10))  # ATO / VEL / AMT / NGT / ANO
    status = Column(String(20), default="OPEN")  # OPEN / RESOLVED
    created_at = Column(DateTime, server_default=func.now())


class SHAPReason(Base):
    __tablename__ = "shap_reasons"

    reason_id = UUIDColumn(primary_key=True)
    case_id = UUIDColumn()
    reason_text = Column(String(500), nullable=False)
    display_order = Column(Integer, nullable=False)


class Decision(Base):
    __tablename__ = "decisions"

    decision_id = UUIDColumn(primary_key=True)
    case_id = UUIDColumn()
    analyst_id = UUIDColumn()
    action = Column(String(50), nullable=False)  # BLOCK / FREEZE / ESCALATE / CLEAR
    decided_at = Column(DateTime, server_default=func.now())
