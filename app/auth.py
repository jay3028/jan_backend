"""
Authentication utilities - JWT, password hashing, OTP
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
import secrets
import random
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    try:
        # Pre-hash long passwords with SHA256 to avoid bcrypt 72-byte limit
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"[AUTH] Password verification error: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt with SHA256 pre-hashing for long passwords"""
    try:
        # Pre-hash long passwords with SHA256 to avoid bcrypt 72-byte limit
        if len(password.encode('utf-8')) > 72:
            print(f"[AUTH] Password longer than 72 bytes, applying SHA256 pre-hash")
            password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"[AUTH] Password hashing error: {str(e)}")
        raise Exception(f"Failed to hash password: {str(e)}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.JWTError:
        raise ValueError("Invalid token")


def generate_otp(length: int = 6) -> str:
    """Generate random OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def generate_api_key() -> str:
    """Generate secure API key for companies"""
    return secrets.token_urlsafe(32)


def generate_worker_id(category: str, year: int, db_session=None) -> str:
    """
    Generate Universal Worker ID with guaranteed uniqueness
    Format: IND-WRK-{CATEGORY}-YYYY-XXXXXX
    
    XXXXXX is a 6-digit sequential number based on database count
    This ensures uniqueness and official-looking IDs
    
    Example: IND-WRK-DLV-2025-000001
    """
    from app.models import Worker
    
    category_codes = {
        "delivery_worker": "DLV",
        "aeps_agent": "AEP"
    }
    code = category_codes.get(category, "WRK")
    
    # If database session provided, get count for sequential numbering
    if db_session:
        # Count existing workers for this category and year
        prefix = f"IND-WRK-{code}-{year}-"
        existing_count = db_session.query(Worker).filter(
            Worker.worker_id.like(f"{prefix}%")
        ).count()
        
        # Generate next sequential number
        next_number = existing_count + 1
        sequential_suffix = f"{next_number:06d}"  # 6 digits, zero-padded
        
        worker_id = f"IND-WRK-{code}-{year}-{sequential_suffix}"
        
        # Double-check uniqueness (in case of concurrent requests)
        max_attempts = 10
        attempts = 0
        while db_session.query(Worker).filter(Worker.worker_id == worker_id).first() and attempts < max_attempts:
            next_number += 1
            sequential_suffix = f"{next_number:06d}"
            worker_id = f"IND-WRK-{code}-{year}-{sequential_suffix}"
            attempts += 1
        
        return worker_id
    else:
        # Fallback: use random if no db session (shouldn't happen in production)
        random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        return f"IND-WRK-{code}-{year}-{random_suffix}"

