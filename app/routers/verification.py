"""
Public verification routes (for citizens)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Worker, User, Company
from app.schemas import VerifyWorkerRequest, VerifyWorkerResponse

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.post("/worker", response_model=VerifyWorkerResponse)
async def verify_worker(
    data: VerifyWorkerRequest,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to verify worker
    Citizens can verify using worker_id, mobile, or QR data
    """
    print(f"\n[VERIFICATION] Public Verification Request - Worker ID: {data.worker_id}, Mobile: {data.mobile}, QR: {bool(data.qr_data)}")
    worker = None
    
    # Find worker
    if data.worker_id:
        worker = db.query(Worker).filter(Worker.worker_id == data.worker_id).first()
    elif data.mobile:
        user = db.query(User).filter(User.mobile == data.mobile).first()
        if user:
            worker = db.query(Worker).filter(Worker.user_id == user.id).first()
    elif data.qr_data:
        # Extract worker_id from QR data
        # Format: https://jansuraksha.gov.in/verify?id=WORKER_ID
        if "id=" in data.qr_data:
            worker_id = data.qr_data.split("id=")[1].split("&")[0]
            worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Get latest verification to check if worker is verified
    from app.models import PoliceVerification, VerificationStatus
    
    # Only allow public verification for police-verified workers
    if worker.verification_status != VerificationStatus.VERIFIED or not worker.worker_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker verification is pending. Worker ID not yet assigned."
        )
    
    # Get user details
    user = db.query(User).filter(User.id == worker.user_id).first()
    
    # Get company details (if linked)
    company_name = None
    if worker.current_company_id:
        company = db.query(Company).filter(Company.id == worker.current_company_id).first()
        if company:
            company_name = company.company_name
    
    # Get latest verification (already imported PoliceVerification above)
    latest_verification = db.query(PoliceVerification).filter(
        PoliceVerification.worker_id == worker.id,
        PoliceVerification.status == VerificationStatus.VERIFIED
    ).order_by(PoliceVerification.verification_date.desc()).first()
    
    # Determine if police verified
    police_verified = latest_verification is not None
    last_verification_date = latest_verification.verification_date if latest_verification else None
    
    print(f"[VERIFICATION] Worker Found - ID: {worker.worker_id}, Status: {worker.status.value}, Police Verified: {police_verified}")
    
    # PUBLIC DATA ONLY - No Aadhaar, no address, no biometrics
    return VerifyWorkerResponse(
        worker_id=worker.worker_id,
        full_name=user.full_name if user else "Unknown",
        photo_url=worker.selfie_url,  # Public photo
        role=worker.category.value,
        company_name=company_name,
        verification_status=worker.verification_status.value,
        police_verified=police_verified,
        last_verification_date=last_verification_date,
        risk_score=worker.risk_score,
        is_active=worker.status.value == "active"
    )


@router.get("/worker/{worker_id}", response_model=VerifyWorkerResponse)
async def verify_worker_by_id(
    worker_id: str,
    db: Session = Depends(get_db)
):
    """
    Public endpoint to verify worker by ID (used by QR codes)
    """
    return await verify_worker(
        VerifyWorkerRequest(worker_id=worker_id),
        db
    )

