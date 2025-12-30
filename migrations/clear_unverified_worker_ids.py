"""
Database migration: Clear worker_ids for unverified workers

This script removes worker_id from any worker records that haven't been
verified by police yet. Worker IDs should only be assigned after police
verification is approved.

Run this script once to clean up any existing bad data.
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Worker, VerificationStatus
from app.database import DATABASE_URL

def clear_unverified_worker_ids():
    """Clear worker_id for all unverified workers"""
    print("\n" + "="*60)
    print("MIGRATION: Clear Worker IDs for Unverified Workers")
    print("="*60 + "\n")
    
    # Create database session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Find all workers with worker_id but not verified
        workers = db.query(Worker).filter(
            Worker.worker_id.isnot(None),
            Worker.verification_status != VerificationStatus.VERIFIED
        ).all()
        
        print(f"Found {len(workers)} workers with premature worker_ids")
        print("-" * 60)
        
        if len(workers) == 0:
            print("✓ No workers found with premature worker_ids")
            print("✓ Database is clean!")
            return
        
        # Clear worker_id for each unverified worker
        cleared_count = 0
        for worker in workers:
            print(f"\nWorker Internal ID: {worker.id}")
            print(f"  - Worker ID (being cleared): {worker.worker_id}")
            print(f"  - Category: {worker.category.value if worker.category else 'N/A'}")
            print(f"  - Verification Status: {worker.verification_status.value if worker.verification_status else 'N/A'}")
            print(f"  - Onboarding Step: {worker.onboarding_step}/6")
            
            # Clear the worker_id
            worker.worker_id = None
            cleared_count += 1
        
        # Commit changes
        db.commit()
        
        print("\n" + "="*60)
        print(f"✓ Successfully cleared {cleared_count} worker IDs")
        print("="*60)
        print("\nThese worker IDs will be regenerated when police approve verification.")
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will clear worker_ids for unverified workers!")
    print("This is a one-time cleanup migration.\n")
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        clear_unverified_worker_ids()
    else:
        print("\n✗ Migration cancelled")

