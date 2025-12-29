-- Fix database after QR code workflow change
-- QR codes should ONLY be generated after police verification, not during onboarding
-- Run this SQL command in your MySQL database

-- Option 1: Clear ALL QR codes (will be regenerated when police verifies)
-- This is the safest option as QR codes should only exist for VERIFIED workers
UPDATE workers SET qr_code_url = NULL, verification_endpoint = NULL;

-- Option 2: Delete the incomplete worker record to start fresh
-- DELETE FROM workers WHERE user_id = 3;  -- Replace 3 with your actual user_id

-- Option 3: Clear QR codes only for pending/unverified workers
UPDATE workers 
SET qr_code_url = NULL, verification_endpoint = NULL 
WHERE verification_status != 'verified' OR status != 'active';

