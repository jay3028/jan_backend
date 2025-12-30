# Database Migrations

This directory contains database migration scripts for the JanSuraksha system.

## Available Migrations

### 1. `clear_unverified_worker_ids.py`

**Purpose:** Removes worker IDs from workers who haven't been verified by police yet.

**Background:** Worker IDs should only be assigned AFTER police verification is approved. This migration cleans up any existing data where worker IDs were prematurely assigned.

**When to run:** 
- Run this once after deploying the fix for worker ID assignment
- Safe to run multiple times (idempotent)
- No data loss - worker IDs will be regenerated when police approve verification

**How to run:**

```bash
cd jansuraksha_backend
python migrations/clear_unverified_worker_ids.py
```

**What it does:**
1. Finds all workers with a worker_id but verification_status != VERIFIED
2. Clears the worker_id field for these workers
3. Displays summary of changes made

**After running:**
- Unverified workers will show "Pending Verification" instead of a worker ID
- When police approve a worker, a new unique worker ID will be generated
- QR codes and verification endpoints will be created at that time

---

### 2. `regenerate_qr_codes.py`

**Purpose:** Generates QR codes for all verified workers who don't have one yet.

**Background:** QR codes are generated automatically when police approve a worker. However, if workers were verified before QR code generation was implemented, or if there was an issue during generation, this script will regenerate them.

**When to run:** 
- After deploying QR code generation feature
- If you notice verified workers missing QR codes
- Safe to run multiple times (skips workers who already have QR codes)
- No data loss or duplication

**How to run:**

```bash
cd jansuraksha_backend
python migrations/regenerate_qr_codes.py
```

**What it does:**
1. Finds all verified workers with worker_id but no qr_code_url
2. Generates QR code and verification endpoint for each
3. Saves QR code image to uploads/qr_codes/ directory
4. Updates database with QR code path

**After running:**
- Verified workers will see their QR code in the dashboard
- Citizens can scan QR codes for instant verification
- Police officers can view QR codes in worker details

---

## Migration Guidelines

1. Always backup the database before running migrations
2. Test migrations in development/staging environment first
3. Read the migration script to understand what it does
4. Check the output carefully after running

## Need Help?

Contact the development team if you encounter any issues with migrations.

