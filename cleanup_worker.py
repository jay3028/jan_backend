"""
Cleanup script to fix any workers with base64 QR codes
Run this once to clean up existing records
"""
from app.database import SessionLocal
from app.models import Worker
from app.services.qr_service import qr_service

def cleanup_workers():
    db = SessionLocal()
    try:
        # Find all workers
        workers = db.query(Worker).all()
        
        for worker in workers:
            # Check if qr_code_url is base64 (starts with "data:")
            if worker.qr_code_url and worker.qr_code_url.startswith("data:"):
                print(f"Cleaning up worker {worker.id} - {worker.worker_id}")
                
                # Regenerate QR code as file
                if worker.worker_id:
                    worker.qr_code_url = qr_service.generate_worker_qr(worker.worker_id)
                    worker.verification_endpoint = qr_service.generate_verification_endpoint(worker.worker_id)
                    print(f"  New QR path: {worker.qr_code_url}")
                else:
                    # If no worker_id yet, clear the QR code
                    worker.qr_code_url = None
                    worker.verification_endpoint = None
                    print(f"  Cleared QR code (no worker_id yet)")
        
        db.commit()
        print(f"\nCleaned up {len(workers)} worker records")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_workers()

