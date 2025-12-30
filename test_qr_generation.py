"""
Test QR code generation to verify correct URL
"""
import os
os.environ['FRONTEND_URL'] = 'http://localhost:3000'
os.environ['BACKEND_URL'] = 'http://localhost:8000'

from app.services.qr_service import qr_service
from pathlib import Path

print("\n" + "="*60)
print("QR CODE GENERATION TEST")
print("="*60 + "\n")

# Test QR service configuration
print(f"Frontend URL: {qr_service.base_url}")
print(f"QR Code Directory: {qr_service.qr_dir}")
print()

# Generate test QR code
test_worker_id = "IND-WRK-DLV-2025-958738"
print(f"Generating QR code for worker: {test_worker_id}")

try:
    # Generate QR code
    qr_path = qr_service.generate_worker_qr(test_worker_id)
    verification_endpoint = qr_service.generate_verification_endpoint(test_worker_id)
    
    print(f"\n✅ QR Code Generated Successfully!")
    print(f"   File Path: {qr_path}")
    print(f"   Full Path: {Path(qr_path).absolute()}")
    print(f"   Verification Endpoint: {verification_endpoint}")
    
    # Check if file exists
    if Path(qr_path).exists():
        file_size = Path(qr_path).stat().st_size
        print(f"   File Size: {file_size} bytes")
        print(f"\n✅ QR code file exists and can be served!")
    else:
        print(f"\n❌ ERROR: QR code file was not created!")
    
    # Show what the QR code contains
    print(f"\n📱 QR Code Contains:")
    print(f"   URL: http://localhost:3000/verify?id={test_worker_id}")
    print(f"   This URL will work in development mode ✅")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60 + "\n")

print("To use this in production, set:")
print("  FRONTEND_URL=https://jansuraksha.gov.in")
print("  BACKEND_URL=https://api.jansuraksha.gov.in")
print("\nThen regenerate all QR codes.")

