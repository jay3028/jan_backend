# Police Dashboard API Endpoints

## Authentication
All endpoints require police officer authentication via Bearer token.

---

## 1. Get Police Officer Profile
**GET** `/api/police/me`

**Response:**
```json
{
  "officer": {
    "id": 1,
    "officer_id": "OFF-2025-001",
    "name": "Officer Name",
    "email": "officer@police.gov.in",
    "station_code": "PS001",
    "station_name": "City Police Station",
    "district": "District Name",
    "state": "State Name",
    "rank": "Inspector"
  },
  "statistics": {
    "total_verifications": 50,
    "verified": 45,
    "rejected": 3,
    "pending": 2
  },
  "recent_verifications": [...]
}
```

---

## 2. Get Verification Queue (Pending Workers)
**GET** `/api/police/verification-queue`

**Description:** Get all workers waiting for police verification

**Response:**
```json
{
  "workers": [
    {
      "id": 1,  // Use this ID to fetch details
      "worker_id": "Pending Assignment",  // Not assigned yet
      "full_name": "Kunal Kumar",
      "mobile": "7870304944",
      "email": "kunal@example.com",
      "category": "delivery_worker",
      "city": "Barauni",
      "state": "Bihar",
      "address": "Railway Colony",
      "submitted_at": "2025-12-30T01:30:00Z",
      "onboarding_step": 6,
      "has_selfie": true,
      "has_aadhaar": true
    }
  ],
  "total": 1
}
```

---

## 3. Get Worker Details for Review
**GET** `/api/police/workers/by-id/{internal_id}`

**Parameters:**
- `internal_id`: Worker's internal database ID (from verification queue)

**Response:**
```json
{
  "id": 1,
  "worker_id": "Not Assigned",
  "user": {
    "full_name": "Kunal Kumar",
    "email": "kunal@example.com",
    "mobile": "7870304944"
  },
  "category": "delivery_worker",
  "address": "Railway Colony",
  "city": "Barauni",
  "state": "Bihar",
  "pincode": "851101",
  "aadhaar_reference": "XXXX-XXXX-1234",
  "selfie_url": "uploads/selfies/worker_1_abc123.jpg",
  "status": "pending_verification",
  "verification_status": "pending",
  "onboarding_step": 6,
  "onboarding_data": { ... },
  "submitted_at": "2025-12-30T01:30:00Z",
  "verifications": [],
  "complaints": []
}
```

---

## 4. Perform Face Verification
**POST** `/api/police/verify-face`

**Request Body:**
```json
{
  "worker_id": 1,  // Internal ID
  "live_face_image_url": "data:image/jpeg;base64,..."
}
```

**Response:**
```json
{
  "match_score": 0.95,  // 95% match
  "is_match": true,
  "liveness_detected": true,
  "confidence": 0.95
}
```

---

## 5. Verify/Reject Worker (Final Decision)
**POST** `/api/police/verify`

**Request Body:**
```json
{
  "worker_id": 1,  // Internal ID
  "status": "verified",  // or "rejected"
  "remarks": "All documents verified successfully",
  "external_verification_ref": "CIJS-2025-001",  // Optional
  "external_system": "CIJS",  // Optional: "CIJS" or "CCTNS"
  "certificate_url": "http://...",  // Optional
  "certificate_number": "CERT-2025-001"  // Optional
}
```

**Response (if VERIFIED):**
```json
{
  "success": true,
  "verification_id": 5,
  "message": "Worker verified",
  "worker_status": "active",
  "worker_id": "IND-WRK-DLV-2025-000001",  // ✅ NOW GENERATED!
  "qr_code_url": "uploads/qrcodes/IND-WRK-DLV-2025-000001.png",
  "verification_endpoint": "https://jansuraksha.gov.in/api/verify/worker/IND-WRK-DLV-2025-000001"
}
```

**Response (if REJECTED):**
```json
{
  "success": true,
  "verification_id": 5,
  "message": "Worker rejected",
  "worker_status": "blocked"
}
```

---

## 6. Search Workers
**GET** `/api/police/workers/search?q={search_term}`

**Parameters:**
- `q`: Search query (worker ID, name, or mobile)

**Response:**
```json
{
  "workers": [
    {
      "id": 1,
      "worker_id": "IND-WRK-DLV-2025-000001",
      "full_name": "Kunal Kumar",
      "mobile": "7870304944",
      "category": "delivery_worker",
      "status": "active",
      "verification_status": "verified",
      "risk_score": 0.0
    }
  ]
}
```

---

## Complete Police Verification Flow

```
1. Police logs in
   └─> GET /api/auth/me (verify role = "police")

2. Load dashboard
   └─> GET /api/police/me (get officer stats)
   └─> GET /api/police/verification-queue (get pending workers)

3. Click on a worker to review
   └─> GET /api/police/workers/by-id/{id} (get full details)

4. Review documents, selfie, address, etc.

5. (Optional) Check CIJS/CCTNS database externally

6. Perform face verification
   └─> POST /api/police/verify-face
       {
         "worker_id": 1,
         "live_face_image_url": "captured_photo_base64"
       }

7. Make final decision
   └─> POST /api/police/verify
       {
         "worker_id": 1,
         "status": "verified",
         "remarks": "All checks passed",
         "external_verification_ref": "CIJS-REF-123"
       }

8. ✅ System Automatically:
   - Generates Worker ID: IND-WRK-DLV-2025-000001
   - Generates QR Code
   - Updates worker status to "active"
   - Stores verification in police officer's profile
   - Worker can now see their ID and QR code!
```

---

## Status Values

### Worker Status
- `pending_verification` - Submitted, awaiting police
- `active` - Verified and active
- `blocked` - Rejected by police
- `suspended` - Temporarily suspended
- `inactive` - Inactive

### Verification Status
- `pending` - Not verified yet
- `verified` - Police approved
- `rejected` - Police rejected
- `expired` - Verification expired

---

## CIJS/CCTNS Integration Notes

The system stores external verification references but does **NOT** directly connect to CIJS/CCTNS databases. Police officers should:

1. Check CIJS/CCTNS externally
2. Enter the reference number in the verification form
3. System stores it for audit trail

This is by design for security and compliance reasons.

---

## Testing the Flow

### Test with cURL:

```bash
# 1. Get verification queue
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/police/verification-queue

# 2. Get worker details
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/police/workers/by-id/1

# 3. Verify worker
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"worker_id": 1, "status": "verified", "remarks": "Approved"}' \
  http://localhost:8000/api/police/verify
```

