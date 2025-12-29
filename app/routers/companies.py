"""
Company management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Company, Worker, WorkerCompanyLink, WorkerStatus, Complaint
from app.schemas import CompanyRegister, CompanyResponse, ComplaintCreate, WorkerUpdateStatus
from app.dependencies import get_current_user, get_current_company, create_audit_log
from app.auth import generate_api_key
from app.models import User

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("/register", response_model=CompanyResponse)
async def register_company(
    data: CompanyRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a company"""
    print(f"\n[COMPANY] Registration Request - User ID: {current_user.id}, Company: {data.company_name}")
    # Check if company already exists
    existing = db.query(Company).filter(Company.user_id == current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company already registered"
        )
    
    # Create company
    company = Company(
        user_id=current_user.id,
        company_name=data.company_name,
        cin=data.cin,
        registration_id=data.registration_id,
        signatory_name=data.signatory_name,
        signatory_email=data.signatory_email,
        signatory_mobile=data.signatory_mobile,
        address=data.address,
        city=data.city,
        state=data.state,
        is_approved=False  # Requires admin approval
    )
    
    db.add(company)
    db.commit()
    db.refresh(company)
    print(f"[COMPANY] Company Registered - ID: {company.id}, Name: {company.company_name}, Approved: {company.is_approved}")
    
    # Create audit log
    create_audit_log(
        user_id=current_user.id,
        action="company_register",
        resource_type="company",
        resource_id=company.id,
        details={"company_name": data.company_name},
        db=db
    )
    print(f"[AUDIT] Company registration logged - Company ID: {company.id}")
    
    return company


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(company: Company = Depends(get_current_company)):
    """Get current company profile"""
    return company


@router.post("/generate-api-key")
async def generate_company_api_key(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Generate API key for company (requires approval)"""
    if not company.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company not approved yet"
        )
    
    # Generate new API key
    api_key = generate_api_key()
    company.api_key = api_key
    company.api_key_created_at = datetime.utcnow()
    
    db.commit()
    
    return {"api_key": api_key, "message": "Store this securely. It won't be shown again."}


@router.post("/workers/{worker_id}/link")
async def link_worker(
    worker_id: str,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Link a worker to company"""
    print(f"\n[COMPANY] Link Worker Request - Company ID: {company.id}, Worker ID: {worker_id}")
    # Find worker
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Check if already linked
    existing_link = db.query(WorkerCompanyLink).filter(
        WorkerCompanyLink.worker_id == worker.id,
        WorkerCompanyLink.company_id == company.id,
        WorkerCompanyLink.unlinked_at.is_(None)
    ).first()
    
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Worker already linked to your company"
        )
    
    # Create link
    link = WorkerCompanyLink(
        worker_id=worker.id,
        company_id=company.id,
        status=WorkerStatus.ACTIVE
    )
    
    worker.current_company_id = company.id
    
    db.add(link)
    db.commit()
    print(f"[COMPANY] Worker Linked - Company ID: {company.id}, Worker ID: {worker_id}")
    
    # Create audit log
    create_audit_log(
        user_id=company.user_id,
        action="worker_linked",
        resource_type="worker",
        resource_id=worker.id,
        details={"company_id": company.id, "worker_id": worker_id},
        db=db
    )
    print(f"[AUDIT] Worker link logged - Worker ID: {worker_id}")
    
    return {"success": True, "message": "Worker linked successfully"}


@router.get("/workers")
async def get_company_workers(
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Get all workers linked to company"""
    links = db.query(WorkerCompanyLink).filter(
        WorkerCompanyLink.company_id == company.id,
        WorkerCompanyLink.unlinked_at.is_(None)
    ).all()
    
    workers = []
    for link in links:
        worker = link.worker
        user = db.query(User).filter(User.id == worker.user_id).first()
        workers.append({
            "id": worker.id,
            "worker_id": worker.worker_id,
            "full_name": user.full_name if user else "Unknown",
            "category": worker.category.value,
            "status": link.status.value,
            "verification_status": worker.verification_status.value,
            "risk_score": worker.risk_score,
            "linked_at": link.linked_at
        })
    
    return {"workers": workers, "total": len(workers)}


@router.post("/workers/{worker_id}/status")
async def update_worker_status(
    worker_id: str,
    data: WorkerUpdateStatus,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Update worker operational status"""
    # Find worker
    worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Check if linked to company
    link = db.query(WorkerCompanyLink).filter(
        WorkerCompanyLink.worker_id == worker.id,
        WorkerCompanyLink.company_id == company.id,
        WorkerCompanyLink.unlinked_at.is_(None)
    ).first()
    
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Worker not linked to your company"
        )
    
    # Update status
    link.status = data.status
    link.notes = data.reason
    
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=company.user_id,
        action="worker_status_update",
        resource_type="worker",
        resource_id=worker.id,
        details={"status": data.status.value, "reason": data.reason},
        db=db
    )
    
    return {"success": True, "message": "Worker status updated"}


@router.post("/complaints")
async def submit_complaint(
    data: ComplaintCreate,
    company: Company = Depends(get_current_company),
    db: Session = Depends(get_db)
):
    """Submit a complaint against a worker"""
    # Verify worker exists and is linked
    worker = db.query(Worker).filter(Worker.id == data.worker_id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    # Generate complaint number
    complaint_number = f"CMP-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}"
    
    complaint = Complaint(
        complaint_number=complaint_number,
        worker_id=worker.id,
        submitted_by_company_id=company.id,
        category=data.category,
        title=data.title,
        description=data.description,
        evidence_urls=data.evidence_urls
    )
    
    db.add(complaint)
    
    # Update worker complaint count and risk score
    worker.complaint_count += 1
    worker.risk_score += 10  # Simple risk score increase
    
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=company.user_id,
        action="complaint_submitted",
        resource_type="complaint",
        resource_id=complaint.id,
        details={"worker_id": worker.id, "category": data.category.value},
        db=db
    )
    
    return {
        "success": True,
        "complaint_number": complaint_number,
        "message": "Complaint submitted successfully"
    }

