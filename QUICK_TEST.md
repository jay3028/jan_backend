# Quick Test - Police Dashboard

## Check if worker exists in database

Run this command:
```bash
cd jansuraksha_backend
python check_worker_profile.py
```

This will show if any workers have completed onboarding.

---

## Test API Endpoints Directly

### 1. Get Statistics (for dashboard cards)
```bash
curl -H "Authorization: Bearer YOUR_POLICE_TOKEN" \
  http://localhost:8000/api/police/stats
```

**Expected Response:**
```json
{
  "pending": 1,  // Should be > 0 if worker completed onboarding
  "approved": 0,
  "rejected": 0,
  "incidents": 0
}
```

### 2. Get Pending Verifications
```bash
curl -H "Authorization: Bearer YOUR_POLICE_TOKEN" \
  http://localhost:8000/api/police/verifications/pending
```

**Expected Response:**
```json
{
  "workers": [
    {
      "id": 1,
      "full_name": "Kunal Kumar",
      "mobile": "7870304944",
      "category": "delivery_worker",
      "city": "Barauni",
      "state": "Bihar",
      ...
    }
  ],
  "total": 1
}
```

### 3. Get Incidents
```bash
curl -H "Authorization: Bearer YOUR_POLICE_TOKEN" \
  http://localhost:8000/api/police/incidents
```

---

## Frontend Endpoint URLs (Now Working)

| Frontend Calls | Backend Endpoint | Status |
|----------------|------------------|--------|
| `/api/police/stats` | ✅ Added | Working |
| `/api/police/verifications/pending` | ✅ Added | Working |
| `/api/police/incidents` | ✅ Added | Working |
| `/api/police/verification-queue` | ✅ Exists | Working |

---

## Troubleshooting

### If dashboard shows 0 for everything:

**Reason 1: No workers in database**
- Check: Run `python check_worker_profile.py`
- Fix: Have a worker complete the onboarding process

**Reason 2: Worker onboarding incomplete**
- Check: Worker must complete step 6 (all 6 steps)
- Fix: Complete onboarding form

**Reason 3: Worker not in pending status**
- Check: Worker status must be `pending_verification`
- Fix: Run SQL:
  ```sql
  UPDATE workers 
  SET status = 'pending_verification', 
      verification_status = 'pending',
      onboarding_step = 6
  WHERE user_id = YOUR_USER_ID;
  ```

**Reason 4: Frontend authentication issue**
- Check: Police officer logged in with correct role
- Fix: Logout and login again

---

## SQL Queries to Check Database

```sql
-- Check if any workers exist
SELECT COUNT(*) FROM workers;

-- Check workers by status
SELECT status, verification_status, COUNT(*) 
FROM workers 
GROUP BY status, verification_status;

-- Check specific worker
SELECT w.id, w.worker_id, w.status, w.verification_status, w.onboarding_step,
       u.full_name, u.mobile, u.email
FROM workers w
JOIN users u ON w.user_id = u.id
WHERE u.mobile = '7870304944';

-- Check all pending workers
SELECT w.id, w.status, w.verification_status, w.onboarding_step,
       u.full_name, u.mobile
FROM workers w
JOIN users u ON w.user_id = u.id
WHERE w.status = 'pending_verification'
  AND w.verification_status = 'pending';
```

