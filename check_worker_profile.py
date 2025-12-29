"""
Quick script to check worker profile in database
Run: python check_worker_profile.py
"""
from app.database import SessionLocal
from app.models import Worker, User

def check_worker_profile():
    db = SessionLocal()
    try:
        # Get all users with worker role
        users = db.query(User).filter(User.role.in_(['worker', 'delivery_worker', 'aeps_agent'])).all()
        
        print("\n" + "="*80)
        print("WORKER PROFILES IN DATABASE")
        print("="*80)
        
        if not users:
            print("\n❌ No users with worker role found!")
            return
        
        for user in users:
            print(f"\n📋 User ID: {user.id}")
            print(f"   Name: {user.full_name}")
            print(f"   Email: {user.email}")
            print(f"   Mobile: {user.mobile}")
            print(f"   Role: {user.role.value}")
            
            # Check for worker profile
            worker = db.query(Worker).filter(Worker.user_id == user.id).first()
            
            if worker:
                print(f"\n   ✅ WORKER PROFILE EXISTS")
                print(f"   Worker Internal ID: {worker.id}")
                print(f"   Worker Official ID: {worker.worker_id or '⚠️ NOT GENERATED YET (Will be assigned after police verification)'}")
                print(f"   Category: {worker.category.value if worker.category else 'None'}")
                print(f"   Status: {worker.status.value if worker.status else 'None'}")
                print(f"   Verification: {worker.verification_status.value if worker.verification_status else 'None'}")
                print(f"   Onboarding Step: {worker.onboarding_step} / 6")
                
                # Determine what should be shown
                if worker.onboarding_step == 6:
                    print(f"   ✅ ONBOARDING: COMPLETED")
                elif worker.onboarding_step > 0:
                    print(f"   ⏳ ONBOARDING: IN PROGRESS (Step {worker.onboarding_step}/6)")
                else:
                    print(f"   ❌ ONBOARDING: NOT STARTED")
                
                print(f"\n   Address: {worker.address_current or 'N/A'}")
                print(f"   City: {worker.city or 'N/A'}")
                print(f"   State: {worker.state or 'N/A'}")
                print(f"   Selfie: {'✅ Uploaded' if worker.selfie_url else '❌ Not uploaded'}")
                print(f"   Aadhaar: {'✅ Provided' if worker.aadhaar_reference else '❌ Not provided'}")
                
                if worker.worker_id:
                    print(f"\n   🎉 OFFICIAL WORKER ID ISSUED: {worker.worker_id}")
                    print(f"   QR Code: {worker.qr_code_url or 'Not generated'}")
            else:
                print(f"\n   ❌ NO WORKER PROFILE (needs to complete onboarding)")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_worker_profile()

