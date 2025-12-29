"""
Database initialization script
Creates tables and optional test data
"""
from app.database import engine, Base, SessionLocal
from app.models import User, UserRole
from app.auth import get_password_hash
import sys


def init_database():
    """Initialize database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")


def create_admin_user():
    """Create default admin user"""
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@jansuraksha.gov.in").first()
        
        if not admin:
            admin = User(
                email="admin@jansuraksha.gov.in",
                full_name="System Administrator",
                role=UserRole.ADMIN,
                password_hash=get_password_hash("admin123"),
                is_active=True,
                is_verified=True,
                email_verified=True
            )
            db.add(admin)
            db.commit()
            print("✓ Admin user created:")
            print("  Email: admin@jansuraksha.gov.in")
            print("  Password: admin123")
            print("  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
        else:
            print("✓ Admin user already exists")
    
    except Exception as e:
        print(f"✗ Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()


def main():
    print("=" * 50)
    print("Jan Suraksha Database Initialization")
    print("=" * 50)
    
    init_database()
    
    if "--with-admin" in sys.argv or "-a" in sys.argv:
        create_admin_user()
    
    print("=" * 50)
    print("Database initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()

