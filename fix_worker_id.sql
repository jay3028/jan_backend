-- Fix workers who have Worker IDs but are still pending verification
-- This shouldn't happen in production, but fixes test data

-- Clear Worker ID and QR Code for pending workers
UPDATE workers 
SET worker_id = NULL,
    qr_code_url = NULL,
    verification_endpoint = NULL
WHERE verification_status = 'pending' 
  AND worker_id IS NOT NULL;

-- Verify the fix
SELECT 
    w.id,
    w.worker_id,
    w.status,
    w.verification_status,
    w.onboarding_step,
    u.full_name,
    u.mobile
FROM workers w
JOIN users u ON w.user_id = u.id
WHERE w.verification_status = 'pending';

