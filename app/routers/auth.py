"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User, UserRole, PoliceOfficer
from app.schemas import (
    SignupRequest, LoginRequest, OTPRequest, OTPVerify,
    TokenResponse, RefreshTokenRequest, UserResponse
)
from app.auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token
)
from app.services.otp_service import otp_service
from app.dependencies import get_current_user, create_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/request-otp")
async def request_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Request OTP for email or mobile"""
    print(f"\n[AUTH] OTP Request - Email: {request.email}, Mobile: {request.mobile}, Purpose: {request.purpose}")
    try:
        # Check if user already exists
        if request.email:
            existing_user = db.query(User).filter(User.email == request.email).first()
            if existing_user and request.purpose == "signup":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        elif request.mobile:
            existing_user = db.query(User).filter(User.mobile == request.mobile).first()
            if existing_user and request.purpose == "signup":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mobile number already registered"
                )
        
        # Generate and send OTP
        otp = otp_service.create_otp(
            db=db,
            email=request.email,
            mobile=request.mobile,
            purpose=request.purpose
        )
        print(f"[AUTH] OTP Generated and Sent: {otp}")
        
        return {
            "success": True,
            "message": "OTP sent successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify-otp")
async def verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP"""
    print(f"\n[AUTH] OTP Verification - Email: {request.email}, Mobile: {request.mobile}, OTP: {request.otp}, Purpose: {request.purpose}")
    is_valid = otp_service.verify_otp(
        db=db,
        otp=request.otp,
        email=request.email,
        mobile=request.mobile,
        purpose=request.purpose
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # If this is email verification, mark user as verified
    if request.purpose == "email_verification" and request.email:
        user = db.query(User).filter(User.email == request.email).first()
        if user:
            user.email_verified = True
            user.is_verified = True
            db.commit()
            
            # Generate tokens
            access_token = create_access_token({"user_id": user.id, "role": user.role.value})
            refresh_token = create_refresh_token({"user_id": user.id})
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                user={
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role.value
                }
            )
    
    return {"success": True, "message": "OTP verified successfully"}


@router.post("/resend-otp")
async def resend_otp(request: dict, db: Session = Depends(get_db)):
    """Resend OTP"""
    email = request.get("email")
    mobile = request.get("mobile")
    purpose = request.get("purpose", "email_verification")
    
    otp_service.create_otp(
        db=db,
        email=email,
        mobile=mobile,
        purpose=purpose
    )
    
    return {"success": True, "message": "OTP resent successfully"}


@router.post("/signup")
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """User signup - Returns TokenResponse or verification required message"""
    print(f"\n[AUTH] Signup Request - Name: {request.full_name}, Role: {request.role}, Email: {request.email}, Mobile: {request.mobile}")
    # Validation
    if not request.email and not request.mobile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or mobile number required"
        )
    
    # Check if user exists
    if request.email:
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    if request.mobile:
        existing = db.query(User).filter(User.mobile == request.mobile).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile number already registered"
            )
    
    # For mobile signup, verify OTP
    if request.mobile and request.otp:
        is_valid = otp_service.verify_otp(
            db=db,
            otp=request.otp,
            mobile=request.mobile,
            purpose="signup"
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
    
    # Create user
    user = User(
        email=request.email,
        mobile=request.mobile,
        full_name=request.full_name,
        role=UserRole(request.role),
        password_hash=get_password_hash(request.password) if request.password else None,
        mobile_verified=bool(request.mobile and request.otp),
        email_verified=False,
        is_verified=bool(request.mobile and request.otp)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[AUTH] User Created - ID: {user.id}, Email: {user.email}, Role: {user.role.value}")
    
    # Automatically create police officer profile if role is police
    if user.role == UserRole.POLICE:
        police_officer = PoliceOfficer(
            user_id=user.id,
            officer_id=f"OFF-{datetime.now().year}-{user.id:05d}",
            station_code=f"PS{user.id:03d}",
            station_name="Central Police Station",  # Default, can be updated later
            district="District HQ",  # Default, can be updated later
            state="Bihar",  # Default, can be updated later
            rank="Inspector"  # Default rank
        )
        db.add(police_officer)
        db.commit()
        db.refresh(police_officer)
        print(f"[AUTH] ✅ Police Officer Profile Created - Officer ID: {police_officer.officer_id}, Rank: {police_officer.rank}")
    
    # Create audit log
    create_audit_log(
        user_id=user.id,
        action="user_signup",
        resource_type="user",
        resource_id=user.id,
        details={"role": request.role},
        db=db
    )
    print(f"[AUDIT] User signup logged for user_id: {user.id}")
    
    # For email signup, require email verification
    if request.email and not request.mobile:
        # Send verification email
        print(f"[AUTH] Email signup - sending verification OTP to {request.email}")
        otp_service.create_otp(db=db, email=request.email, purpose="email_verification")
        
        return {
            "requires_verification": True,
            "message": "Please check your email for verification code",
            "access_token": None,
            "refresh_token": None,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value
            }
        }
    
    # Generate tokens
    access_token = create_access_token({"user_id": user.id, "role": user.role.value})
    refresh_token = create_refresh_token({"user_id": user.id})
    print(f"[AUTH] Tokens generated - User will be logged in automatically")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "mobile": user.mobile,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """User login"""
    print(f"\n[AUTH] Login Request - Method: {request.login_method}, Email: {request.email}, Mobile: {request.mobile}")
    user = None
    
    # Email + Password
    if request.login_method == "email_password":
        if not request.email or not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password required"
            )
        
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
    
    # Mobile + Password
    elif request.login_method == "mobile_password":
        if not request.mobile or not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile and password required"
            )
        
        user = db.query(User).filter(User.mobile == request.mobile).first()
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid mobile or password"
            )
    
    # Mobile + OTP
    elif request.login_method == "mobile_otp":
        if not request.mobile or not request.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile and OTP required"
            )
        
        # Verify OTP
        is_valid = otp_service.verify_otp(
            db=db,
            otp=request.otp,
            mobile=request.mobile,
            purpose="login"
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
        
        user = db.query(User).filter(User.mobile == request.mobile).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    print(f"[AUTH] Login Successful - User ID: {user.id}, Email: {user.email}, Role: {user.role.value}")
    
    # Create audit log
    create_audit_log(
        user_id=user.id,
        action="user_login",
        resource_type="user",
        resource_id=user.id,
        details={"method": request.login_method},
        db=db
    )
    print(f"[AUDIT] User login logged for user_id: {user.id}")
    
    # Generate tokens
    access_token = create_access_token({"user_id": user.id, "role": user.role.value})
    refresh_token = create_refresh_token({"user_id": user.id})
    print(f"[AUTH] Tokens generated for user_id: {user.id}")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "mobile": user.mobile,
            "full_name": user.full_name,
            "role": user.role.value
        }
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token"""
    try:
        payload = decode_token(request.refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new tokens
        access_token = create_access_token({"user_id": user.id, "role": user.role.value})
        refresh_token = create_refresh_token({"user_id": user.id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "id": user.id,
                "email": user.email,
                "mobile": user.mobile,
                "full_name": user.full_name,
                "role": user.role.value
            }
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

