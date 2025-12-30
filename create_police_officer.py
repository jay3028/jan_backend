"""
Create police officer profile for testing
Run: python create_police_officer.py
"""
from app.database import SessionLocal
from app.models import PoliceOfficer, User

def create_police_officer():
    db = SessionLocal()
    try:
        # Find police users without officer profile
        police_users = db.query(User).filter(User.role == 'police').all()
        
        if not police_users:
            print("❌ No users with police role found!")
            print("Please create a police user first by registering at /auth/signup")
            return
        
        print("\n" + "="*80)
        print("POLICE USERS FOUND")
        print("="*80)
        
        for user in police_users:
            print(f"\n📋 User ID: {user.id}")
            print(f"   Name: {user.full_name}")
            print(f"   Email: {user.email}")
            print(f"   Mobile: {user.mobile}")
            
            # Check if officer profile exists
            existing = db.query(PoliceOfficer).filter(
                PoliceOfficer.user_id == user.id
            ).first()
            
            if existing:
                print(f"   ✅ Officer profile already exists!")
                print(f"   Officer ID: {existing.officer_id}")
                print(f"   Station: {existing.station_name}")
            else:
                print(f"   ⚠️  NO OFFICER PROFILE - Creating now...")
                
                # Create officer profile
                officer = PoliceOfficer(
                    user_id=user.id,
                    officer_id=f"OFF-2025-{user.id:03d}",
                    station_code=f"PS{user.id:03d}",
                    station_name="Central Police Station",
                    district="District HQ",
                    state="Bihar",
                    rank="Inspector"
                )
                
                db.add(officer)
                db.commit()
                db.refresh(officer)
                
                print(f"   ✅ OFFICER PROFILE CREATED!")
                print(f"   Officer ID: {officer.officer_id}")
                print(f"   Station: {officer.station_name}")
                print(f"   Rank: {officer.rank}")
        
        print("\n" + "="*80)
        print("✅ All police users have officer profiles now!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_police_officer()

