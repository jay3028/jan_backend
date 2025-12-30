"""
Quick test to verify QR code setup
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Worker, VerificationStatus
from app.database import DATABASE_URL

print("\n" + "="*60)
print("QR CODE VERIFICATION TEST")
print("="*60 + "\n")

# Create database session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Find verified workers
    workers = db.query(Worker).filter(
        Worker.verification_status == VerificationStatus.VERIFIED,
        Worker.worker_id.isnot(None)
    ).all()
    
    for worker in workers:
        print(f"Worker ID: {worker.worker_id}")
        print(f"  Database qr_code_url: {worker.qr_code_url}")
        print(f"  Verification endpoint: {worker.verification_endpoint}")
        
        if worker.qr_code_url:
            # Check if file exists
            file_path = Path(__file__).parent / worker.qr_code_url
            if file_path.exists():
                print(f"  [OK] QR Code file EXISTS at: {file_path}")
                print(f"  [OK] File size: {file_path.stat().st_size} bytes")
                print(f"  [OK] Access URL: http://localhost:8000/{worker.qr_code_url}")
            else:
                print(f"  [ERROR] QR Code file NOT FOUND at: {file_path}")
        else:
            print(f"  [ERROR] qr_code_url is NULL in database")
        
        print()
    
    if not workers:
        print("No verified workers found in database")
    
finally:
    db.close()

print("="*60)
print("TEST COMPLETE")
print("="*60)

