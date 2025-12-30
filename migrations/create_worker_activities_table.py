"""
Create worker_activities table and populate with dummy data
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Worker, WorkerActivity, WorkerCategory
from app.database import DATABASE_URL

# Sample data for realistic dummy activities
DELIVERY_PARTNERS = ["Flipkart", "Amazon", "Swiggy", "Zomato", "Delhivery", "BlueDart"]
PACKAGE_TYPES = ["Electronics", "Groceries", "Documents", "Clothing", "Medicines", "Books"]
BIHAR_CITIES = ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga", "Ara", "Begusarai", "Katihar"]
BIHAR_AREAS = [
    "Boring Road", "Patliputra", "Kankarbagh", "Rajendra Nagar", "Gandhi Maidan",
    "Ashok Nagar", "Bailey Road", "Fraser Road", "Exhibition Road", "Station Road"
]

TRANSACTION_TYPES = ["Cash Withdrawal", "Balance Inquiry", "Mini Statement", "Deposit", "Aadhaar Pay"]
BANK_NAMES = ["SBI", "PNB", "BOI", "HDFC", "ICICI", "Axis Bank", "Union Bank"]

def create_table(engine):
    """Create worker_activities table"""
    print("\n" + "="*60)
    print("Creating worker_activities table...")
    print("="*60 + "\n")
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS worker_activities (
        id INT AUTO_INCREMENT PRIMARY KEY,
        worker_id INT NOT NULL,
        activity_type VARCHAR(50) NOT NULL,
        activity_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        location VARCHAR(500),
        city VARCHAR(100),
        state VARCHAR(100),
        pincode VARCHAR(10),
        
        -- Delivery specific
        package_id VARCHAR(100),
        delivery_partner VARCHAR(100),
        package_type VARCHAR(100),
        recipient_name VARCHAR(255),
        recipient_contact VARCHAR(20),
        
        -- Transaction specific
        customer_name VARCHAR(255),
        customer_contact VARCHAR(20),
        transaction_type VARCHAR(50),
        transaction_amount FLOAT,
        bank_name VARCHAR(255),
        
        status VARCHAR(50) DEFAULT 'completed',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (worker_id) REFERENCES workers(id) ON DELETE CASCADE,
        INDEX idx_worker_id (worker_id),
        INDEX idx_activity_date (activity_date),
        INDEX idx_activity_type (activity_type)
    );
    """
    
    with engine.connect() as connection:
        connection.execute(text(create_table_sql))
        connection.commit()
    
    print("[OK] Table 'worker_activities' created successfully")

def generate_delivery_activities(worker_id, count=20):
    """Generate dummy delivery activities"""
    activities = []
    now = datetime.now()
    
    for i in range(count):
        # Random date within last 2 weeks
        days_ago = random.randint(0, 14)
        hours_ago = random.randint(0, 23)
        activity_date = now - timedelta(days=days_ago, hours=hours_ago)
        
        city = random.choice(BIHAR_CITIES)
        area = random.choice(BIHAR_AREAS)
        
        activity = WorkerActivity(
            worker_id=worker_id,
            activity_type="delivery",
            activity_date=activity_date,
            location=f"{area}, {city}, Bihar",
            city=city,
            state="Bihar",
            pincode=f"80000{random.randint(1, 9)}",
            package_id=f"PKG{random.randint(100000, 999999)}",
            delivery_partner=random.choice(DELIVERY_PARTNERS),
            package_type=random.choice(PACKAGE_TYPES),
            recipient_name=f"Customer {random.randint(1, 999)}",
            recipient_contact=f"9{random.randint(100000000, 999999999)}",
            status="completed",
            notes=f"Delivered successfully at {activity_date.strftime('%I:%M %p')}"
        )
        activities.append(activity)
    
    return activities

def generate_transaction_activities(worker_id, count=20):
    """Generate dummy transaction activities for AePS agents"""
    activities = []
    now = datetime.now()
    
    for i in range(count):
        # Random date within last 2 weeks
        days_ago = random.randint(0, 14)
        hours_ago = random.randint(0, 23)
        activity_date = now - timedelta(days=days_ago, hours=hours_ago)
        
        city = random.choice(BIHAR_CITIES)
        area = random.choice(BIHAR_AREAS)
        trans_type = random.choice(TRANSACTION_TYPES)
        
        # Amount only for cash transactions
        amount = None
        if trans_type in ["Cash Withdrawal", "Deposit", "Aadhaar Pay"]:
            amount = random.choice([500, 1000, 1500, 2000, 2500, 3000, 5000])
        
        activity = WorkerActivity(
            worker_id=worker_id,
            activity_type="transaction",
            activity_date=activity_date,
            location=f"{area}, {city}, Bihar",
            city=city,
            state="Bihar",
            pincode=f"80000{random.randint(1, 9)}",
            customer_name=f"Customer {random.randint(1, 999)}",
            customer_contact=f"9{random.randint(100000000, 999999999)}",
            transaction_type=trans_type,
            transaction_amount=amount,
            bank_name=random.choice(BANK_NAMES),
            status="completed",
            notes=f"Transaction completed at {activity_date.strftime('%I:%M %p')}"
        )
        activities.append(activity)
    
    return activities

def populate_dummy_data(db):
    """Add dummy activity data for verified workers"""
    print("\n" + "="*60)
    print("Populating dummy activity data...")
    print("="*60 + "\n")
    
    # Get all verified workers
    workers = db.query(Worker).all()
    
    if not workers:
        print("[WARNING] No workers found in database. Create workers first.")
        return
    
    total_added = 0
    
    for worker in workers:
        print(f"\nWorker ID: {worker.id}")
        print(f"  Category: {worker.category.value if worker.category else 'N/A'}")
        print(f"  Worker ID: {worker.worker_id or 'Not assigned'}")
        
        # Generate activities based on category
        if worker.category == WorkerCategory.DELIVERY_WORKER:
            activities = generate_delivery_activities(worker.id, count=20)
            print(f"  [OK] Generated {len(activities)} delivery activities")
        elif worker.category == WorkerCategory.AEPS_AGENT:
            activities = generate_transaction_activities(worker.id, count=20)
            print(f"  [OK] Generated {len(activities)} transaction activities")
        else:
            print(f"  [WARNING] Unknown category, skipping...")
            continue
        
        # Add to database
        for activity in activities:
            db.add(activity)
        
        total_added += len(activities)
    
    # Commit all activities
    db.commit()
    
    print("\n" + "="*60)
    print(f"[OK] Successfully added {total_added} activity records")
    print("="*60)

def main():
    print("\n" + "="*70)
    print("         WORKER ACTIVITIES TABLE CREATION & DATA POPULATION")
    print("="*70)
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Create table
        create_table(engine)
        
        # Step 2: Populate with dummy data
        populate_dummy_data(db)
        
        print("\n" + "="*70)
        print("[OK] MIGRATION COMPLETE!")
        print("="*70)
        print("\nYou can now:")
        print("  1. View activities on worker dashboard")
        print("  2. View activities on police dashboard under each worker")
        print("  3. Activities from last 2 weeks are displayed")
        print("\n")
        
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()

