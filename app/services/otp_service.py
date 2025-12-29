"""
OTP service for email and SMS
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import OTPVerification
from app.auth import generate_otp
import os


class OTPService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "Jan Suraksha")
    
    def send_email_otp(self, email: str, otp: str, purpose: str) -> bool:
        """Send OTP via email"""
        print(f"\n[OTP-EMAIL] Sending OTP to {email}")
        print(f"[OTP-EMAIL] Purpose: {purpose}")
        print(f"[OTP-EMAIL] OTP Code: {otp}")
        try:
            subject = f"Your Jan Suraksha OTP - {otp}"
            
            # Create HTML email
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: #f9f9f9; padding: 30px; border-radius: 10px;">
                        <h2 style="color: #2563eb;">Jan Suraksha</h2>
                        <h3 style="color: #333;">Your OTP Code</h3>
                        <p style="color: #666; font-size: 16px;">
                            Your OTP for {purpose} is:
                        </p>
                        <div style="background-color: #2563eb; color: white; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; border-radius: 5px; margin: 20px 0;">
                            {otp}
                        </div>
                        <p style="color: #666; font-size: 14px;">
                            This OTP is valid for 10 minutes. Do not share this code with anyone.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        <p style="color: #999; font-size: 12px;">
                            This is an automated email from Jan Suraksha platform. Please do not reply to this email.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = email
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            print(f"[OTP-EMAIL] ✓ OTP sent successfully to {email}")
            return True
        except Exception as e:
            print(f"[OTP-EMAIL] ✗ Error sending email: {str(e)}")
            return False
    
    def send_sms_otp(self, mobile: str, otp: str, purpose: str) -> bool:
        """
        Send OTP via SMS
        In production, integrate with SMS gateway (Twilio, AWS SNS, etc.)
        For now, just log it
        """
        # TODO: Integrate with SMS gateway
        print(f"\n[OTP-SMS] Sending OTP to {mobile}")
        print(f"[OTP-SMS] Purpose: {purpose}")
        print(f"[OTP-SMS] OTP Code: {otp}")
        print(f"[OTP-SMS] ✓ OTP logged (SMS gateway not configured)")
        # In development, always return True
        return True
    
    def create_otp(self, db: Session, email: str = None, mobile: str = None, purpose: str = "verification") -> str:
        """Create and store OTP"""
        print(f"\n[OTP-SERVICE] Creating OTP")
        print(f"[OTP-SERVICE] Email: {email}, Mobile: {mobile}, Purpose: {purpose}")
        
        otp = generate_otp(6)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        print(f"[OTP-SERVICE] Generated OTP: {otp}")
        print(f"[OTP-SERVICE] Expires at: {expires_at}")
        
        # Store in database
        otp_record = OTPVerification(
            email=email,
            mobile=mobile,
            otp_code=otp,
            purpose=purpose,
            expires_at=expires_at
        )
        db.add(otp_record)
        db.commit()
        print(f"[OTP-SERVICE] OTP stored in database")
        
        # Send OTP
        if email:
            self.send_email_otp(email, otp, purpose)
        elif mobile:
            self.send_sms_otp(mobile, otp, purpose)
        
        return otp
    
    def verify_otp(self, db: Session, otp: str, email: str = None, mobile: str = None, purpose: str = "verification") -> bool:
        """Verify OTP"""
        print(f"\n[OTP-SERVICE] Verifying OTP")
        print(f"[OTP-SERVICE] OTP: {otp}, Email: {email}, Mobile: {mobile}, Purpose: {purpose}")
        
        # First, check all OTPs for this email/mobile to debug
        if email:
            all_otps = db.query(OTPVerification).filter(OTPVerification.email == email).all()
            print(f"[OTP-SERVICE] DEBUG: Found {len(all_otps)} total OTP(s) for email {email}")
            for idx, otp_rec in enumerate(all_otps):
                print(f"  [{idx+1}] Code: {otp_rec.otp_code}, Purpose: {otp_rec.purpose}, Verified: {otp_rec.is_verified}, Expires: {otp_rec.expires_at}, Current Time: {datetime.utcnow()}")
        elif mobile:
            all_otps = db.query(OTPVerification).filter(OTPVerification.mobile == mobile).all()
            print(f"[OTP-SERVICE] DEBUG: Found {len(all_otps)} total OTP(s) for mobile {mobile}")
            for idx, otp_rec in enumerate(all_otps):
                print(f"  [{idx+1}] Code: {otp_rec.otp_code}, Purpose: {otp_rec.purpose}, Verified: {otp_rec.is_verified}, Expires: {otp_rec.expires_at}")
        
        query = db.query(OTPVerification).filter(
            OTPVerification.otp_code == otp,
            OTPVerification.purpose == purpose,
            OTPVerification.is_verified == False,
            OTPVerification.expires_at > datetime.utcnow()
        )
        
        if email:
            query = query.filter(OTPVerification.email == email)
        elif mobile:
            query = query.filter(OTPVerification.mobile == mobile)
        
        otp_record = query.first()
        
        if otp_record:
            # Mark as verified
            otp_record.is_verified = True
            otp_record.verified_at = datetime.utcnow()
            db.commit()
            print(f"[OTP-SERVICE] ✓ OTP verified successfully")
            return True
        
        # Check if OTP exists but doesn't match all conditions
        otp_any = db.query(OTPVerification).filter(OTPVerification.otp_code == otp).first()
        if otp_any:
            print(f"[OTP-SERVICE] ✗ OTP found but conditions not met:")
            print(f"  - Purpose match: {otp_any.purpose == purpose} (expected: {purpose}, got: {otp_any.purpose})")
            print(f"  - Not verified: {not otp_any.is_verified}")
            print(f"  - Not expired: {otp_any.expires_at > datetime.utcnow()}")
            if email:
                print(f"  - Email match: {otp_any.email == email}")
            if mobile:
                print(f"  - Mobile match: {otp_any.mobile == mobile}")
            
            # Increment attempts
            otp_any.attempts += 1
            db.commit()
            print(f"[OTP-SERVICE] ✗ Invalid OTP (attempts: {otp_any.attempts})")
        else:
            print(f"[OTP-SERVICE] ✗ OTP not found in database at all")
        
        return False


otp_service = OTPService()

