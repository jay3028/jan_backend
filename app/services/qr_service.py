"""
QR Code generation service
"""
import qrcode
from pathlib import Path
from typing import Optional


class QRCodeService:
    def __init__(self, base_url: str = "https://jansuraksha.gov.in"):
        self.base_url = base_url
        # Create QR codes directory
        self.qr_dir = Path("uploads/qrcodes")
        self.qr_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_worker_qr(self, worker_id: str) -> str:
        """
        Generate QR code for worker verification
        Saves to file and returns file path
        """
        # Create verification URL
        verification_url = f"{self.base_url}/verify?id={worker_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to file
        filename = f"{worker_id}.png"
        filepath = self.qr_dir / filename
        img.save(filepath)
        
        # Return relative path for database storage
        return str(filepath).replace("\\", "/")
    
    def generate_verification_endpoint(self, worker_id: str) -> str:
        """Generate public verification endpoint URL"""
        return f"{self.base_url}/api/verify/worker/{worker_id}"


qr_service = QRCodeService()

