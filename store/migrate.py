"""
ATO Shield v2 - Database Migration Script
Run this to create/update database tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from store.database import engine, Base
from store.models import Bank, Analyst, Transaction, Case, SHAPReason, Decision

def run_migration():
    """Create all tables in database"""
    print("🔄 Running database migration...")
    print("📊 Creating tables...")
    
    # This creates all tables defined in models.py
    Base.metadata.create_all(bind=engine)
    
    print("✅ Migration complete!")
    print("📋 Tables created/verified:")
    print("   - banks")
    print("   - analysts") 
    print("   - transactions")
    print("   - cases")
    print("   - shap_reasons")
    print("   - decisions")


if __name__ == "__main__":
    run_migration()
