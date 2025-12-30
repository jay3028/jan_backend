"""
Fix QR code URL in database for workers who have QR code files but no database entry
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Worker, VerificationStatus
from app.database import DATABASE_URL
from pathlib import Path

def fix_qr_code_urls():
    """Fix QR code URLs for verified workers"""
    print("\n" + "="*60)
    print("FIX: Update QR Code URLs in Database")
    print("="*60 + "\n")
    
    # Create database session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Find all verified workers with worker_id
        workers = db.query(Worker).filter(
            Worker.verification_status == VerificationStatus.VERIFIED,
            Worker.worker_id.isnot(None)
        ).all()
        
        print(f"Found {len(workers)} verified workers")
        print("-" * 60)
        
        updated_count = 0
        for worker in workers:
            print(f"\nWorker ID: {worker.worker_id}")
            print(f"  Internal ID: {worker.id}")
            print(f"  Current qr_code_url: {worker.qr_code_url}")
            print(f"  Current verification_endpoint: {worker.verification_endpoint}")
            
            # Check if QR code file exists
            qr_file_path = f"uploads/qrcodes/{worker.worker_id}.png"
            full_path = Path(__file__).parent.parent / qr_file_path
            
            if full_path.exists():
                print(f"  ✓ QR Code file exists: {qr_file_path}")
                
                # Update database fields
                worker.qr_code_url = qr_file_path
                worker.verification_endpoint = f"https://jansuraksha.gov.in/verify?id={worker.worker_id}"
                
                print(f"  ✓ Updated qr_code_url to: {worker.qr_code_url}")
                print(f"  ✓ Updated verification_endpoint to: {worker.verification_endpoint}")
                updated_count += 1
            else:
                print(f"  ✗ QR Code file NOT found at: {qr_file_path}")
        
        # Commit changes
        if updated_count > 0:
            db.commit()
            print("\n" + "="*60)
            print(f"✓ Successfully updated {updated_count} worker records")
            print("="*60)
            print("\nQR codes should now be visible in the dashboard!")
        else:
            print("\n" + "="*60)
            print("No updates needed - all records are correct")
            print("="*60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        db.rollback()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    fix_qr_code_urls()

