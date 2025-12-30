"""
Database migration: Regenerate QR codes for verified workers

This script generates QR codes for all verified workers who don't have one yet.
This is useful after implementing QR code generation or if QR codes were not
generated during the verification process.

Run this script to ensure all verified workers have QR codes.
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Worker, VerificationStatus, WorkerStatus
from app.database import SQLALCHEMY_DATABASE_URL
from app.services.qr_service import qr_service

def regenerate_qr_codes():
    """Generate QR codes for all verified workers without them"""
    print("\n" + "="*60)
    print("MIGRATION: Regenerate QR Codes for Verified Workers")
    print("="*60 + "\n")
    
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Find all verified workers without QR codes
        workers = db.query(Worker).filter(
            Worker.verification_status == VerificationStatus.VERIFIED,
            Worker.worker_id.isnot(None),
            Worker.qr_code_url.is_(None)
        ).all()
        
        print(f"Found {len(workers)} verified workers without QR codes")
        print("-" * 60)
        
        if len(workers) == 0:
            print("✓ All verified workers already have QR codes!")
            print("✓ No action needed.")
            return
        
        # Generate QR code for each verified worker
        generated_count = 0
        for worker in workers:
            print(f"\nWorker Internal ID: {worker.id}")
            print(f"  - Worker ID: {worker.worker_id}")
            print(f"  - Category: {worker.category.value if worker.category else 'N/A'}")
            print(f"  - Status: {worker.status.value if worker.status else 'N/A'}")
            
            # Generate QR Code
            try:
                worker.qr_code_url = qr_service.generate_worker_qr(worker.worker_id)
                worker.verification_endpoint = qr_service.generate_verification_endpoint(worker.worker_id)
                print(f"  ✓ QR Code Generated: {worker.qr_code_url}")
                print(f"  ✓ Verification Endpoint: {worker.verification_endpoint}")
                generated_count += 1
            except Exception as e:
                print(f"  ✗ ERROR generating QR code: {str(e)}")
        
        # Commit changes
        db.commit()
        
        print("\n" + "="*60)
        print(f"✓ Successfully generated {generated_count} QR codes")
        print("="*60)
        print("\nQR codes are now available for all verified workers.")
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  This will generate QR codes for verified workers who don't have them yet.")
    print("This is safe to run and will not affect existing QR codes.\n")
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        regenerate_qr_codes()
    else:
        print("\n✗ Migration cancelled")

