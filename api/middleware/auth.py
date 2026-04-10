"""
ATO Shield v2 - API Key Authentication Middleware
Validates bank API keys on inbound requests
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from store.database import get_db
from store.models import Bank

security = HTTPBearer()


async def validate_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Bank:
    """
    Validate API key from Bearer token.
    Returns the Bank object if valid, raises 401 if not.
    """
    api_key = credentials.credentials
    
    bank = db.query(Bank).filter(Bank.api_key == api_key).first()
    
    if not bank:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return bank


async def validate_api_key_simple(
    request: Request,
    db: Session = Depends(get_db)
) -> Bank:
    """
    Alternative: Extract API key from Authorization header directly.
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )
    
    api_key = auth_header.split("Bearer ")[1]
    
    bank = db.query(Bank).filter(Bank.api_key == api_key).first()
    
    if not bank:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return bank
