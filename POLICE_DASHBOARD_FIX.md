# 🚔 Police Dashboard Fix - Data Format Mismatch

## The Problem

Backend logs showed: `[POLICE] Found 1 workers pending verification`  
But frontend showed: **"0" for everything**

## Root Cause

**Data format mismatch between backend and frontend:**

### What Frontend Expected:
```javascript
{
  "verifications": [
    {
      "id": 1,
      "full_name": "Worker Name",
      "status": "pending" | "approved" | "rejected",  // ← Missing!
      ...
    }
  ]
}
```

### What Backend Returned (Before Fix):
```json
{
  "workers": [...],  // ← Wrong key! Should be "verifications"
  // No "status" field in each record
}
```

## The Fix

### Changed in `app/routers/police.py`:

1. **Fixed Response Key** (Line 254):
   ```python
   # Before:
   return {"workers": result, "total": len(result)}
   
   # After:
   return {"verifications": result, "total": len(result)}
   ```

2. **Added Status Field** (Lines 218-246):
   ```python
   # Map worker verification_status to frontend status
   if worker.verification_status == VerificationStatus.VERIFIED:
       status = "approved"
   elif worker.verification_status == VerificationStatus.REJECTED:
       status = "rejected"
   else:
       status = "pending"
   
   result.append({
       ...
       "status": status  # ← Frontend can now filter by this!
   })
   ```

3. **Return All Verifications** (Line 211-213):
   ```python
   # Before: Only pending
   workers = db.query(Worker).filter(
       Worker.status == WorkerStatus.PENDING_VERIFICATION,
       Worker.verification_status == VerificationStatus.PENDING
   ).all()
   
   # After: All workers who completed onboarding
   workers = db.query(Worker).filter(
       Worker.onboarding_step == 6  # Completed onboarding
   ).all()
   ```

## Why This Works

### Frontend Code (page.js Lines 114-116):
```javascript
const pendingCount = verifications.filter(v => v.status === 'pending').length;
const approvedCount = verifications.filter(v => v.status === 'approved').length;
const rejectedCount = verifications.filter(v => v.status === 'rejected').length;
```

Now the frontend can:
- ✅ Access data via `verificationsData.verifications`
- ✅ Filter by `status` field for metrics
- ✅ Show correct counts in dashboard cards

## Expected Result

After restart, the police dashboard should show:
- **PENDING**: 1 (or actual count)
- **APPROVED**: 0 (or actual count)
- **REJECTED**: 0 (or actual count)
- **INCIDENTS**: 0 (or actual count)

And the "PENDING VERIFICATIONS" section should list the worker details!

## Testing

1. **Restart backend:**
   ```bash
   cd jansuraksha_backend
   uvicorn app.main:app --reload
   ```

2. **Refresh police dashboard:**
   - Go to `http://localhost:3000/dashboard/police`
   - You should now see the worker in the pending list!

3. **Check console:**
   - Backend: `[POLICE] Found X workers for verification queue`
   - Frontend: Should show data in the cards and list

## Files Modified

- ✅ `jansuraksha_backend/app/routers/police.py`
  - Line 203-254: `get_verification_queue` endpoint
  - Changed response format to match frontend expectations
  - Added status mapping for frontend filtering

## Related Files

- `jansuraksha_frontend/src/app/dashboard/police/page.js`
  - Lines 30-34: Data fetching
  - Lines 114-116: Status filtering
  - No changes needed!

