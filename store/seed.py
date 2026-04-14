"""
ATO Shield v2 - Database Seeder for Development
Creates demo bank, analyst, and test transactions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from store.database import SessionLocal, engine, Base
from store.models import Bank, Analyst, Transaction, Case, SHAPReason
from uuid import uuid4

def seed_database():
    """Insert demo data for development (idempotent - safe to run multiple times)"""
    print("🔄 Seeding database...")

    db = SessionLocal()

    try:
        # Check if demo bank already exists
        existing_bank = db.query(Bank).filter(Bank.api_key == "ask_live_demo_key_12345").first()
        
        if existing_bank:
            print(f"ℹ️  Demo Bank already exists: {existing_bank.name}")
            demo_bank = existing_bank
        else:
            # Create demo bank
            demo_bank = Bank(
                bank_id=str(uuid4()),  # Convert to string for SQLite
                name="HDFC Bank Demo",
                api_key="ask_live_demo_key_12345",
                webhook_url="https://webhook.site/demo"
            )
            db.add(demo_bank)
            db.commit()
            db.refresh(demo_bank)
            print(f"✅ Demo Bank created: {demo_bank.name}")

        print(f"   API Key: {demo_bank.api_key}")
        print(f"   Bank ID: {demo_bank.bank_id}")

        # Check if demo analyst already exists
        existing_analyst = db.query(Analyst).filter(Analyst.email == "analyst@atoshield.demo").first()
        
        if existing_analyst:
            print(f"ℹ️  Demo Analyst already exists: {existing_analyst.name}")
        else:
            # Create demo analyst
            demo_analyst = Analyst(
                analyst_id=str(uuid4()),
                bank_id=demo_bank.bank_id,
                name="Demo Analyst",
                email="analyst@atoshield.demo",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILp92S.0i"
            )
            db.add(demo_analyst)
            db.commit()
            print(f"✅ Demo Analyst created: {demo_analyst.name}")

        print(f"   Email: analyst@atoshield.demo")

        print("\n" + "=" * 60)
        print("✅ DATABASE SEEDED SUCCESSFULLY")
        print("=" * 60)
        print("\n💡 To test the API, use:")
        print(f"   curl -X POST http://localhost:8000/api/v1/transaction \\")
        print(f"     -H 'Authorization: Bearer {demo_bank.api_key}' \\")
        print(f"     -H 'Content-Type: application/json' \\")
        print(f"     -d '{{\"test\": \"data\"}}'")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
