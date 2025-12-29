"""
Police verification and management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import (
    PoliceOfficer, PoliceVerification, Worker, Incident, User,
    VerificationStatus, WorkerStatus
)
from app.schemas import (
    PoliceVerificationCreate, PoliceVerificationResponse,
    FaceVerificationRequest, FaceVerificationResponse,
    IncidentCreate
)
from app.dependencies import get_current_user, get_current_police_officer, create_audit_log
from app.services.face_verification import face_verification_service
from app.services.qr_service import qr_service
from app.auth import generate_worker_id

router = APIRouter(prefix="/police", tags=["Police"])


@router.post("/register")
async def register_police_officer(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register police officer profile"""
    # Check if already registered
    existing = db.query(PoliceOfficer).filter(
        PoliceOfficer.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Police officer already registered"
        )
    
    officer = PoliceOfficer(
        user_id=current_user.id,
        officer_id=data.get("officer_id"),
        station_code=data.get("station_code"),
        station_name=data.get("station_name"),
        district=data.get("district"),
        state=data.get("state"),
        rank=data.get("rank")
    )
    
    db.add(officer)
    db.commit()
    db.refresh(officer)
    
    return {"success": True, "officer_id": officer.id}


@router.get("/verification-queue")
async def get_verification_queue(
    officer: PoliceOfficer = Depends(get_current_police_officer),
    db: Session = Depends(get_db)
):
    """Get workers pending verification"""
    workers = db.query(Worker).filter(
        Worker.status == WorkerStatus.PENDING_VERIFICATION,
        Worker.verification_status == VerificationStatus.PENDING
    ).all()
    
    result = []
    for worker in workers:
        user = db.query(User).filter(User.id == worker.user_id).first()
        result.append({
            "id": worker.id,
            "worker_id": worker.worker_id,
            "full_name": user.full_name if user else "Unknown",
            "category": worker.category.value,
            "city": worker.city,
            "state": worker.state,
            "submitted_at": worker.created_at
        })
    
    return {"workers": result, "total": len(result)}


@router.get("/workers/search")
async def search_workers(
    q: str,
    officer: PoliceOfficer = Depends(get_current_police_officer),
    db: Session = Depends(get_db)
):
    """Search for workers"""
    # Search by worker ID, name, or mobile
    workers = db.query(Worker).join(User).filter(
        (Worker.worker_id.like(f"%{q}%")) |
        (User.full_name.like(f"%{q}%")) |
        (User.mobile.like(f"%{q}%"))
    ).limit(50).all()
    
    result = []
    for worker in workers:
        user = db.query(User).filter(User.id == worker.user_id).first()
        result.append({
            "id": worker.id,
            "worker_id": worker.worker_id,
            "full_name": user.full_name if user else "Unknown",
            "mobile": user.mobile if user else None,
            "category": worker.category.value,
            "status": worker.status.value,
            "verification_status": worker.verification_status.value,
            "risk_score": worker.risk_score
        })
    
    return {"workers": result}


@router.get("/workers/{worker_id}")
async def get_worker_details(
    worker_id: str,
    officer: PoliceOfficer = Depends(get_current_police_officer),
    db: Session = Depends(get_db)
):
    """Get full worker details (police access only)"""
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    user = db.query(User).filter(User.id == worker.user_id).first()
    
    # Get verification history
    verifications = db.query(PoliceVerification).filter(
        PoliceVerification.worker_id == worker.id
    ).order_by(PoliceVerification.created_at.desc()).all()
    
    # Get complaints
    from app.models import Complaint
    complaints = db.query(Complaint).filter(
        Complaint.worker_id == worker.id
    ).order_by(Complaint.created_at.desc()).all()
    
    return {
        "worker_id": worker.worker_id,
        "user": {
            "full_name": user.full_name if user else "Unknown",
            "email": user.email if user else None,
            "mobile": user.mobile if user else None
        },
        "category": worker.category.value,
        "address": worker.address_current,
        "city": worker.city,
        "state": worker.state,
        "pincode": worker.pincode,
        "aadhaar_reference": worker.aadhaar_reference,
        "selfie_url": worker.selfie_url,
        "status": worker.status.value,
        "verification_status": worker.verification_status.value,
        "risk_score": worker.risk_score,
        "complaint_count": worker.complaint_count,
        "bank_affiliation": worker.bank_affiliation,
        "aeps_operator_id": worker.aeps_operator_id,
        "verifications": [
            {
                "id": v.id,
                "status": v.status.value,
                "verification_date": v.verification_date,
                "officer_id": v.officer_id,
                "face_match_score": v.face_match_score
            } for v in verifications
        ],
        "complaints": [
            {
                "id": c.id,
                "complaint_number": c.complaint_number,
                "category": c.category.value,
                "title": c.title,
                "status": c.status.value,
                "created_at": c.created_at
            } for c in complaints
        ]
    }


@router.post("/verify-face")
async def verify_worker_face(
    data: FaceVerificationRequest,
    officer: PoliceOfficer = Depends(get_current_police_officer),
    db: Session = Depends(get_db)
):
    """Perform face verification (1:1 match with liveness)"""
    print(f"\n[POLICE] Face Verification Request - Officer ID: {officer.id}, Worker ID: {data.worker_id}")
    # Get worker
    worker = db.query(Worker).filter(Worker.id == data.worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    if not worker.selfie_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker selfie not available"
        )
    
    try:
        # Perform face verification
        print(f"[POLICE] Performing face verification for worker: {worker.worker_id}")
        is_match, match_score, is_live = face_verification_service.verify_worker_face(
            worker.selfie_url,
            data.live_face_image_url
        )
        print(f"[POLICE] Face Verification Result - Match: {is_match}, Score: {match_score}, Live: {is_live}")
        
        # Create or update verification record
        verification = db.query(PoliceVerification).filter(
            PoliceVerification.worker_id == worker.id,
            PoliceVerification.officer_id == officer.id,
            PoliceVerification.status == VerificationStatus.PENDING
        ).first()
        
        if not verification:
            verification = PoliceVerification(
                worker_id=worker.id,
                officer_id=officer.id,
                status=VerificationStatus.PENDING
            )
            db.add(verification)
        
        verification.face_match_score = match_score
        verification.face_match_performed = True
        verification.liveness_check = is_live
        
        db.commit()
        
        # Create audit log
        create_audit_log(
            user_id=officer.user_id,
            action="face_verification",
            resource_type="worker",
            resource_id=worker.id,
            details={
                "match_score": match_score,
                "is_match": is_match,
                "is_live": is_live
            },
            db=db
        )
        
        return FaceVerificationResponse(
            match_score=match_score,
            is_match=is_match,
            liveness_detected=is_live,
            confidence=match_score
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face verification failed: {str(e)}"
        )


@router.post("/verify")
async def create_verification(
    data: PoliceVerificationCreate,
    officer: PoliceOfficer = Depends(get_current_police_officer),
    db: Session = Depends(get_db)
):
    """Create or update police verification"""
    print(f"\n[POLICE] Verification Request - Officer ID: {officer.id}, Worker ID: {data.worker_id}, Status: {data.status}")
    worker = db.query(Worker).filter(Worker.id == data.worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Create verification record
    verification = PoliceVerification(
        worker_id=worker.id,
        officer_id=officer.id,
        status=data.status,
        verification_date=datetime.utcnow() if data.status == VerificationStatus.VERIFIED else None,
        expiry_date=datetime.utcnow() + timedelta(days=365) if data.status == VerificationStatus.VERIFIED else None,
        external_verification_ref=data.external_verification_ref,
        external_system=data.external_system,
        certificate_url=data.certificate_url,
        certificate_number=data.certificate_number,
        remarks=data.remarks,
        rejection_reason=data.rejection_reason
    )
    
    db.add(verification)
    
    # Update worker status
    worker.verification_status = data.status
    
    if data.status == VerificationStatus.VERIFIED:
        worker.status = WorkerStatus.ACTIVE
        
        # Generate Worker ID ONLY when verified by police (UNIQUE & SEQUENTIAL)
        if not worker.worker_id:
            year = datetime.now().year
            worker.worker_id = generate_worker_id(worker.category.value, year, db)
            print(f"[POLICE] ✅ Worker ID Generated (UNIQUE): {worker.worker_id}")
        
        # Generate QR Code ONLY when verified by police
        if not worker.qr_code_url:
            worker.qr_code_url = qr_service.generate_worker_qr(worker.worker_id)
            worker.verification_endpoint = qr_service.generate_verification_endpoint(worker.worker_id)
            print(f"[POLICE] ✅ QR Code Generated for verified worker: {worker.worker_id}")
            print(f"[POLICE] QR Code Path: {worker.qr_code_url}")
    elif data.status == VerificationStatus.REJECTED:
        worker.status = WorkerStatus.BLOCKED
    
    db.commit()
    db.refresh(verification)
    print(f"[POLICE] Verification Complete - Verification ID: {verification.id}, Worker Status: {worker.status.value}")
    
    # Create audit log
    create_audit_log(
        user_id=officer.user_id,
        action="police_verification",
        resource_type="worker",
        resource_id=worker.id,
        details={
            "status": data.status.value,
            "verification_id": verification.id,
            "worker_id": worker.worker_id if data.status == VerificationStatus.VERIFIED else None,
            "qr_generated": bool(worker.qr_code_url) if data.status == VerificationStatus.VERIFIED else False
        },
        db=db
    )
    print(f"[AUDIT] Police verification logged - Verification ID: {verification.id}")
    
    response = {
        "success": True,
        "verification_id": verification.id,
        "message": f"Worker {data.status.value}",
        "worker_status": worker.status.value
    }
    
    # Include Worker ID and QR code info if verified
    if data.status == VerificationStatus.VERIFIED:
        response["worker_id"] = worker.worker_id
        response["qr_code_url"] = worker.qr_code_url
        response["verification_endpoint"] = worker.verification_endpoint
    
    return response


@router.post("/incident")
async def log_incident(
    data: IncidentCreate,
    officer: PoliceOfficer = Depends(get_current_police_officer),
    db: Session = Depends(get_db)
):
    """Log an incident"""
    worker = db.query(Worker).filter(Worker.id == data.worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Generate incident number
    incident_number = f"INC-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}"
    
    incident = Incident(
        incident_number=incident_number,
        worker_id=worker.id,
        officer_id=officer.id,
        title=data.title,
        description=data.description,
        incident_type=data.incident_type,
        severity=data.severity,
        incident_date=data.incident_date,
        location=data.location,
        action_taken=data.action_taken
    )
    
    db.add(incident)
    
    # Update risk score based on severity
    severity_scores = {"low": 5, "medium": 15, "high": 30, "critical": 50}
    worker.risk_score += severity_scores.get(data.severity.lower(), 10)
    
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=officer.user_id,
        action="incident_logged",
        resource_type="incident",
        resource_id=incident.id,
        details={"worker_id": worker.id, "severity": data.severity},
        db=db
    )
    
    return {
        "success": True,
        "incident_number": incident_number,
        "message": "Incident logged successfully"
    }


@router.post("/suspend")
async def suspend_worker(
    data: dict,
    officer: PoliceOfficer = Depends(get_current_police_officer),
    db: Session = Depends(get_db)
):
    """Suspend a worker"""
    worker_id = data.get("worker_id")
    reason = data.get("reason")
    temporary = data.get("temporary", True)
    
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Update status
    worker.status = WorkerStatus.SUSPENDED if temporary else WorkerStatus.BLOCKED
    
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=officer.user_id,
        action="worker_suspended",
        resource_type="worker",
        resource_id=worker.id,
        details={"reason": reason, "temporary": temporary},
        db=db
    )
    
    return {
        "success": True,
        "message": f"Worker {'suspended' if temporary else 'blocked'}"
    }

