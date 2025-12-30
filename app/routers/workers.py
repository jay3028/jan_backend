"""
Worker onboarding and management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import base64
import os
import uuid
from pathlib import Path
from app.database import get_db
from app.models import Worker, WorkerCategory, WorkerStatus, VerificationStatus, User, WorkerActivity
from app.schemas import (
    WorkerOnboardingStep1, WorkerOnboardingStep2, WorkerOnboardingStep3,
    WorkerOnboardingStep4, WorkerOnboardingStep5, WorkerOnboardingStep6,
    WorkerOnboardComplete, WorkerResponse, WorkerDetailResponse
)
from app.dependencies import get_current_user, get_current_worker, create_audit_log
from app.auth import generate_worker_id
from app.services.qr_service import qr_service

router = APIRouter(prefix="/workers", tags=["Workers"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads/selfies")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_base64_image(base64_string: str, worker_id: int) -> str:
    """
    Save a base64-encoded image to disk and return the file path.
    
    Args:
        base64_string: Base64 encoded image (with or without data URI prefix)
        worker_id: Worker ID for organizing files
        
    Returns:
        Relative file path to the saved image
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
        if "," in base64_string and base64_string.startswith("data:"):
            base64_string = base64_string.split(",", 1)[1]
        
        # Decode base64 to bytes
        image_data = base64.b64decode(base64_string)
        
        # Generate unique filename
        filename = f"worker_{worker_id}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = UPLOAD_DIR / filename
        
        # Save the file
        with open(filepath, "wb") as f:
            f.write(image_data)
        
        # Return relative path for database storage
        return str(filepath).replace("\\", "/")
    
    except Exception as e:
        print(f"[ERROR] Failed to save image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save image: {str(e)}"
        )


@router.post("/onboard/step1")
async def onboard_step1(
    data: WorkerOnboardingStep1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 1: Category selection and basic info"""
    print(f"\n[WORKER] Onboarding Step 1 - User ID: {current_user.id}, Category: {data.category}, Name: {data.full_name}")
    
    # Check if worker profile already exists
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    # If worker already submitted for verification, don't allow re-submission
    if worker and worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your application is already submitted and pending police verification. Please wait for approval."
        )
    
    # If worker is already verified, don't allow re-onboarding
    if worker and worker.verification_status == VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your profile is already verified. You cannot re-submit the onboarding form."
        )
    
    if worker:
        # Allow updating only if not yet submitted (onboarding_step < 6)
        if worker.onboarding_step < 6:
            worker.category = data.category
            worker.onboarding_step = 1
            worker.onboarding_data = worker.onboarding_data or {}
            worker.onboarding_data.update({"step1": data.dict()})
    else:
        # Create new
        worker = Worker(
            user_id=current_user.id,
            category=data.category,
            onboarding_step=1,
            onboarding_data={"step1": data.dict()}
        )
        db.add(worker)
    
    # Update user info
    current_user.full_name = data.full_name
    current_user.mobile = data.mobile
    
    db.commit()
    db.refresh(worker)
    print(f"[WORKER] Step 1 Complete - Worker ID: {worker.id}, Category: {worker.category.value}")
    
    return {"success": True, "worker_id": worker.id, "next_step": 2}


@router.post("/onboard/step2")
async def onboard_step2(
    data: WorkerOnboardingStep2,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 2: Address information"""
    print(f"\n[WORKER] Onboarding Step 2 - User ID: {current_user.id}, City: {data.city}, State: {data.state}")
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please complete step 1 first"
        )
    
    # Prevent re-submission if already pending verification
    if worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your application is already submitted and pending police verification."
        )
    
    worker.address_current = data.address_current
    worker.city = data.city
    worker.state = data.state
    worker.pincode = data.pincode
    worker.onboarding_step = 2
    worker.onboarding_data["step2"] = data.dict()
    
    db.commit()
    
    return {"success": True, "next_step": 3}


@router.post("/onboard/step3")
async def onboard_step3(
    data: WorkerOnboardingStep3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 3: Selfie capture"""
    print(f"\n[WORKER] Onboarding Step 3 - User ID: {current_user.id}")
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please complete previous steps first"
        )
    
    # Prevent re-submission if already pending verification
    if worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your application is already submitted and pending police verification."
        )
    
    # Save the base64 image to disk and get the file path
    try:
        file_path = save_base64_image(data.selfie_url, worker.id)
        print(f"[WORKER] Selfie saved successfully: {file_path}")
        worker.selfie_url = file_path
    except Exception as e:
        print(f"[ERROR] Failed to save selfie: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save selfie image: {str(e)}"
        )
    
    worker.onboarding_step = 3
    # Store only a reference in onboarding_data, not the full base64
    worker.onboarding_data["step3"] = {"selfie_saved": True, "file_path": file_path}
    
    db.commit()
    print(f"[WORKER] Step 3 Complete - Selfie stored at: {file_path}")
    
    return {"success": True, "next_step": 4, "selfie_path": file_path}


@router.post("/onboard/step4")
async def onboard_step4(
    data: WorkerOnboardingStep4,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 4: Aadhaar reference"""
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please complete previous steps first"
        )
    
    # Prevent re-submission if already pending verification
    if worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your application is already submitted and pending police verification."
        )
    
    worker.aadhaar_reference = data.aadhaar_reference
    worker.onboarding_step = 4
    worker.onboarding_data["step4"] = data.dict()
    
    db.commit()
    
    return {"success": True, "next_step": 5}


@router.post("/onboard/step5")
async def onboard_step5(
    data: WorkerOnboardingStep5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 5: AePS specific information (if applicable)"""
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please complete previous steps first"
        )
    
    # Prevent re-submission if already pending verification
    if worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your application is already submitted and pending police verification."
        )
    
    # Only for AePS agents
    if worker.category == WorkerCategory.AEPS_AGENT:
        worker.bank_affiliation = data.bank_affiliation
        worker.bc_affiliation = data.bc_affiliation
        worker.aeps_operator_id = data.aeps_operator_id
        worker.service_region = data.service_region
        worker.aeps_device_info = data.aeps_device_info
        worker.transaction_role = data.transaction_role
    
    worker.onboarding_step = 5
    worker.onboarding_data["step5"] = data.dict()
    
    db.commit()
    
    return {"success": True, "next_step": 6}


@router.post("/onboard/step6")
async def onboard_step6(
    data: WorkerOnboardingStep6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Step 6: Consent and finalize"""
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please complete previous steps first"
        )
    
    # Prevent re-submission if already pending verification
    if worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your application is already submitted and pending police verification."
        )
    
    worker.consent_given = data.consent_given
    worker.consent_timestamp = datetime.utcnow()
    worker.declaration_signed = data.declaration_signed
    worker.onboarding_step = 6
    worker.onboarding_data["step6"] = data.dict()
    
    # Store device fingerprint
    if data.device_fingerprint:
        current_user.device_fingerprint = data.device_fingerprint
    
    # Mark as pending verification (Worker ID and QR code will be generated AFTER police verification)
    worker.status = WorkerStatus.PENDING_VERIFICATION
    worker.verification_status = VerificationStatus.PENDING
    
    db.commit()
    db.refresh(worker)
    print(f"[WORKER] Onboarding Complete - Internal ID: {worker.id}, Status: {worker.status.value}")
    print(f"[WORKER] Awaiting police verification - Worker ID and QR code will be generated after approval")
    
    # Create audit log
    create_audit_log(
        user_id=current_user.id,
        action="worker_onboarding_complete",
        resource_type="worker",
        resource_id=worker.id,
        details={"category": worker.category.value},
        db=db
    )
    
    return {
        "success": True,
        "message": "Onboarding complete. Your application has been submitted for police verification.",
        "status": worker.status.value,
        "verification_status": worker.verification_status.value
    }


@router.post("/onboard/complete")
async def onboard_complete(
    data: WorkerOnboardingStep6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete onboarding - Finalize after step-by-step process"""
    print(f"\n[WORKER] Onboarding Complete - User ID: {current_user.id}")
    
    # Get existing worker profile (must exist from previous steps)
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please complete previous onboarding steps first"
        )
    
    # Check if already submitted for verification
    if worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your application is already submitted and pending police verification. Please wait for approval."
        )
    
    # Check if already verified
    if worker.verification_status == VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your profile is already verified. You cannot re-submit the onboarding form."
        )
    
    # Validate that required fields from previous steps exist
    missing_fields = []
    if not worker.category:
        missing_fields.append("category (step 1)")
    if not worker.address_current:
        missing_fields.append("address (step 2)")
    if not worker.city:
        missing_fields.append("city (step 2)")
    if not worker.state:
        missing_fields.append("state (step 2)")
    if not worker.pincode:
        missing_fields.append("pincode (step 2)")
    if not worker.selfie_url:
        missing_fields.append("selfie (step 3)")
    if not worker.aadhaar_reference:
        missing_fields.append("aadhaar (step 4)")
    
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required data from previous steps: {', '.join(missing_fields)}"
        )
    
    # Update final step data
    worker.consent_given = data.consent_given
    worker.consent_timestamp = datetime.utcnow()
    worker.declaration_signed = data.declaration_signed
    worker.onboarding_step = 6
    
    # Store device fingerprint
    if data.device_fingerprint:
        current_user.device_fingerprint = data.device_fingerprint
    
    # Mark as pending verification (Worker ID and QR code will be generated AFTER police verification)
    worker.status = WorkerStatus.PENDING_VERIFICATION
    worker.verification_status = VerificationStatus.PENDING
    
    db.commit()
    db.refresh(worker)
    print(f"[WORKER] Onboarding Complete - Internal ID: {worker.id}, Status: {worker.status.value}")
    print(f"[WORKER] Awaiting police verification - Worker ID and QR code will be generated after approval")
    
    # Create audit log
    create_audit_log(
        user_id=current_user.id,
        action="worker_onboarding_complete",
        resource_type="worker",
        resource_id=worker.id,
        details={"category": worker.category.value},
        db=db
    )
    
    return {
        "success": True,
        "message": "Onboarding complete. Your application has been submitted for police verification.",
        "status": worker.status.value,
        "verification_status": worker.verification_status.value
    }


def get_worker_profile_data(current_user: User, db: Session):
    """Helper function to get worker profile data"""
    print(f"\n[WORKER] Profile request - User ID: {current_user.id}, Role: {current_user.role.value}")
    
    # Get worker profile
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        print(f"[WORKER] No worker profile found for user {current_user.id}")
        # Return empty profile if not onboarded yet
        return {
            "has_profile": False,
            "message": "No worker profile found. Please complete onboarding.",
            "full_name": current_user.full_name,
            "email": current_user.email,
            "mobile": current_user.mobile,
            "role": current_user.role.value
        }
    
    print(f"[WORKER] Profile found - Internal ID: {worker.id}, Official Worker ID: {worker.worker_id}, Category: {worker.category}, Step: {worker.onboarding_step}")
    
    # Determine what to show as Worker ID - ONLY show if police verified
    if worker.verification_status == VerificationStatus.VERIFIED and worker.worker_id:
        # Official Worker ID exists AND police verified
        display_worker_id = worker.worker_id
        worker_id_status = "verified"
    elif worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        # Onboarding complete, waiting for police verification
        display_worker_id = "Pending Verification"
        worker_id_status = "pending"
    else:
        # Still onboarding
        display_worker_id = "Not Assigned"
        worker_id_status = "not_assigned"
    
    return {
        # Profile exists
        "has_profile": True,
        
        # Worker details - NEVER show internal database ID
        "worker_id": display_worker_id,  # Official Worker ID or status message
        "worker_id_status": worker_id_status,  # For frontend to handle display
        "category": worker.category.value if worker.category else None,
        "status": worker.status.value if worker.status else None,
        "verification_status": worker.verification_status.value if worker.verification_status else None,
        "onboarding_step": worker.onboarding_step,
        
        # User details
        "full_name": current_user.full_name,
        "email": current_user.email,
        "mobile": current_user.mobile,
        
        # Address details
        "address_current": worker.address_current,
        "city": worker.city,
        "state": worker.state,
        "pincode": worker.pincode,
        
        # Documents & verification
        "selfie_url": worker.selfie_url,
        "aadhaar_reference": worker.aadhaar_reference,
        "qr_code_url": worker.qr_code_url,
        "verification_endpoint": worker.verification_endpoint,
        
        # AePS specific (if applicable)
        "bank_affiliation": worker.bank_affiliation,
        "bc_affiliation": worker.bc_affiliation,
        "aeps_operator_id": worker.aeps_operator_id,
        "service_region": worker.service_region,
        
        # Risk & company
        "risk_score": worker.risk_score,
        "complaint_count": worker.complaint_count,
        "current_company_id": worker.current_company_id,
        
        # Timestamps
        "created_at": worker.created_at.isoformat() if worker.created_at else None,
        "updated_at": worker.updated_at.isoformat() if worker.updated_at else None
    }


@router.get("/profile")
async def get_worker_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current worker profile (used by frontend)"""
    return get_worker_profile_data(current_user, db)


@router.get("/me")
async def get_my_worker_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current worker profile (alternative endpoint)"""
    return get_worker_profile_data(current_user, db)


@router.get("/verification/status")
async def get_verification_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive verification status (onboarding, police, face verification)"""
    from app.models import PoliceVerification
    
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        return {
            "onboarding": {
                "status": "not_started",
                "label": "NOT STARTED",
                "description": "Complete registration process",
                "current_step": 0,
                "total_steps": 6
            },
            "police_verification": {
                "status": "pending",
                "label": "PENDING",
                "description": "Awaiting onboarding completion"
            },
            "face_verification": {
                "status": "pending",
                "label": "PENDING",
                "description": "Awaiting police verification"
            }
        }
    
    # Get latest police verification record
    latest_verification = db.query(PoliceVerification).filter(
        PoliceVerification.worker_id == worker.id
    ).order_by(PoliceVerification.created_at.desc()).first()
    
    # Determine onboarding status
    if worker.onboarding_step == 6:
        onboarding_status = "completed"
        onboarding_label = "COMPLETED"
        onboarding_desc = "Registration process completed"
    elif worker.onboarding_step > 0:
        onboarding_status = "in_progress"
        onboarding_label = "IN PROGRESS"
        onboarding_desc = f"Step {worker.onboarding_step} of 6 completed"
    else:
        onboarding_status = "not_started"
        onboarding_label = "NOT STARTED"
        onboarding_desc = "Start your registration"
    
    # Determine police verification status
    if worker.verification_status == VerificationStatus.VERIFIED:
        police_status = "verified"
        police_label = "VERIFIED"
        police_desc = "Background check completed"
    elif worker.verification_status == VerificationStatus.REJECTED:
        police_status = "rejected"
        police_label = "REJECTED"
        police_desc = "Verification rejected"
    elif worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        police_status = "pending"
        police_label = "PENDING"
        police_desc = "Background check by law enforcement"
    else:
        police_status = "not_started"
        police_label = "NOT STARTED"
        police_desc = "Awaiting onboarding completion"
    
    # Determine face verification status
    if latest_verification and latest_verification.face_match_performed:
        if latest_verification.liveness_check and latest_verification.face_match_score >= 0.8:
            face_status = "verified"
            face_label = "VERIFIED"
            face_desc = f"Biometric match: {int(latest_verification.face_match_score * 100)}%"
        else:
            face_status = "failed"
            face_label = "FAILED"
            face_desc = "Biometric verification failed"
    elif worker.verification_status == VerificationStatus.VERIFIED:
        # Verified without explicit face check
        face_status = "verified"
        face_label = "VERIFIED"
        face_desc = "Biometric facial recognition"
    elif worker.onboarding_step == 6:
        face_status = "pending"
        face_label = "PENDING"
        face_desc = "Biometric facial recognition"
    else:
        face_status = "not_started"
        face_label = "NOT STARTED"
        face_desc = "Awaiting submission"
    
    return {
        "onboarding": {
            "status": onboarding_status,
            "label": onboarding_label,
            "description": onboarding_desc,
            "current_step": worker.onboarding_step,
            "total_steps": 6
        },
        "police_verification": {
            "status": police_status,
            "label": police_label,
            "description": police_desc,
            "verified_at": latest_verification.verification_date.isoformat() if latest_verification and latest_verification.verification_date else None
        },
        "face_verification": {
            "status": face_status,
            "label": face_label,
            "description": face_desc,
            "match_score": latest_verification.face_match_score if latest_verification else None,
            "liveness_check": latest_verification.liveness_check if latest_verification else None,
            "verified_at": latest_verification.created_at.isoformat() if latest_verification and latest_verification.face_match_performed else None
        },
        "overall": {
            "worker_id": worker.worker_id,
            "status": worker.status.value if worker.status else None,
            "verification_status": worker.verification_status.value if worker.verification_status else None,
            "is_active": worker.status == WorkerStatus.ACTIVE if worker.status else False
        }
    }


@router.get("/onboarding/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get onboarding progress"""
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        return {
            "current_step": 0,
            "completed": False,
            "can_proceed": True,
            "message": "Start your onboarding process",
            "data": {}
        }
    
    # Check if already submitted and pending
    if worker.onboarding_step == 6 and worker.status == WorkerStatus.PENDING_VERIFICATION:
        return {
            "current_step": 6,
            "completed": True,
            "can_proceed": False,
            "worker_id": worker.worker_id,
            "status": worker.status.value,
            "verification_status": worker.verification_status.value,
            "message": "Your application is pending police verification. Please wait for approval.",
            "submitted_at": worker.updated_at.isoformat() if worker.updated_at else None,
            "data": worker.onboarding_data
        }
    
    # Check if verified
    if worker.verification_status == VerificationStatus.VERIFIED:
        return {
            "current_step": 6,
            "completed": True,
            "can_proceed": False,
            "worker_id": worker.worker_id,
            "status": worker.status.value,
            "verification_status": worker.verification_status.value,
            "message": "Your profile is verified and active!",
            "qr_code_url": worker.qr_code_url,
            "verification_endpoint": worker.verification_endpoint,
            "data": worker.onboarding_data
        }
    
    # Check if rejected
    if worker.verification_status == VerificationStatus.REJECTED:
        return {
            "current_step": worker.onboarding_step,
            "completed": False,
            "can_proceed": True,
            "worker_id": worker.worker_id,
            "status": worker.status.value,
            "verification_status": worker.verification_status.value,
            "message": "Your application was rejected. Please contact support or resubmit with correct information.",
            "data": worker.onboarding_data
        }
    
    # In progress
    return {
        "current_step": worker.onboarding_step,
        "completed": False,
        "can_proceed": True,
        "worker_id": worker.worker_id,
        "status": worker.status.value if worker.status else None,
        "verification_status": worker.verification_status.value if worker.verification_status else None,
        "message": f"Continue from step {worker.onboarding_step + 1}",
        "data": worker.onboarding_data
    }


@router.put("/me")
async def update_worker_profile(
    data: dict,
    worker: Worker = Depends(get_current_worker),
    db: Session = Depends(get_db)
):
    """Update worker profile (limited fields)"""
    # Only allow updating certain fields
    allowed_fields = ["address_current", "city", "state", "pincode", "mobile"]
    
    for field, value in data.items():
        if field in allowed_fields:
            setattr(worker, field, value)
    
    db.commit()
    
    return {"success": True, "message": "Profile updated"}


@router.get("/activities")
async def get_worker_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get worker's activity history (last 2 weeks)"""
    print(f"\n[WORKER] Activities requested - User ID: {current_user.id}")
    
    # Get worker profile
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    
    if not worker:
        return {
            "activities": [],
            "total": 0,
            "message": "No worker profile found"
        }
    
    # Get activities from last 2 weeks
    two_weeks_ago = datetime.now() - timedelta(days=14)
    activities = db.query(WorkerActivity).filter(
        WorkerActivity.worker_id == worker.id,
        WorkerActivity.activity_date >= two_weeks_ago
    ).order_by(WorkerActivity.activity_date.desc()).all()
    
    print(f"[WORKER] Found {len(activities)} activities for worker ID: {worker.id}")
    
    # Format activities based on type
    result = []
    for activity in activities:
        activity_data = {
            "id": activity.id,
            "activity_type": activity.activity_type,
            "activity_date": activity.activity_date.isoformat(),
            "location": activity.location,
            "city": activity.city,
            "state": activity.state,
            "pincode": activity.pincode,
            "status": activity.status,
            "notes": activity.notes
        }
        
        # Add type-specific fields
        if activity.activity_type == "delivery":
            activity_data.update({
                "package_id": activity.package_id,
                "delivery_partner": activity.delivery_partner,
                "package_type": activity.package_type,
                "recipient_name": activity.recipient_name,
                "recipient_contact": activity.recipient_contact
            })
        elif activity.activity_type == "transaction":
            activity_data.update({
                "customer_name": activity.customer_name,
                "customer_contact": activity.customer_contact,
                "transaction_type": activity.transaction_type,
                "transaction_amount": activity.transaction_amount,
                "bank_name": activity.bank_name
            })
        
        result.append(activity_data)
    
    return {
        "activities": result,
        "total": len(result),
        "worker_category": worker.category.value if worker.category else None
    }

