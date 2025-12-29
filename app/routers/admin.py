"""
Admin routes for platform governance
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Worker, Company, Complaint, AuditLog, PoliceVerification, WorkerStatus
from app.schemas import DashboardStats, WorkerUpdateStatus
from app.dependencies import require_role, create_audit_log

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    total_workers = db.query(Worker).count()
    active_workers = db.query(Worker).filter(Worker.status == WorkerStatus.ACTIVE).count()
    pending_verifications = db.query(Worker).filter(
        Worker.status == WorkerStatus.PENDING_VERIFICATION
    ).count()
    total_complaints = db.query(Complaint).count()
    high_risk_workers = db.query(Worker).filter(Worker.risk_score > 50).count()
    
    return DashboardStats(
        total_workers=total_workers,
        active_workers=active_workers,
        pending_verifications=pending_verifications,
        total_complaints=total_complaints,
        high_risk_workers=high_risk_workers
    )


@router.get("/users")
async def list_users(
    role: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """List all users"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    users = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "users": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "mobile": u.mobile,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at
            } for u in users
        ],
        "total": total
    }


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    data: dict,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Suspend a user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=current_user.id,
        action="user_suspended",
        resource_type="user",
        resource_id=user_id,
        details={"reason": data.get("reason")},
        db=db
    )
    
    return {"success": True, "message": "User suspended"}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Activate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=current_user.id,
        action="user_activated",
        resource_type="user",
        resource_id=user_id,
        details={},
        db=db
    )
    
    return {"success": True, "message": "User activated"}


@router.get("/workers")
async def list_workers(
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """List all workers"""
    query = db.query(Worker)
    
    if status:
        query = query.filter(Worker.status == status)
    
    workers = query.offset(skip).limit(limit).all()
    total = query.count()
    
    result = []
    for worker in workers:
        user = db.query(User).filter(User.id == worker.user_id).first()
        result.append({
            "id": worker.id,
            "worker_id": worker.worker_id,
            "full_name": user.full_name if user else "Unknown",
            "category": worker.category.value,
            "status": worker.status.value,
            "verification_status": worker.verification_status.value,
            "risk_score": worker.risk_score,
            "created_at": worker.created_at
        })
    
    return {"workers": result, "total": total}


@router.post("/workers/status")
async def update_worker_status(
    data: WorkerUpdateStatus,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Update worker status (admin override)"""
    worker = db.query(Worker).filter(Worker.id == data.worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    worker.status = data.status
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=current_user.id,
        action="worker_status_override",
        resource_type="worker",
        resource_id=worker.id,
        details={"status": data.status.value, "reason": data.reason},
        db=db
    )
    
    return {"success": True, "message": "Worker status updated"}


@router.get("/companies")
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """List all companies"""
    companies = db.query(Company).offset(skip).limit(limit).all()
    total = db.query(Company).count()
    
    return {
        "companies": [
            {
                "id": c.id,
                "company_name": c.company_name,
                "cin": c.cin,
                "is_approved": c.is_approved,
                "created_at": c.created_at
            } for c in companies
        ],
        "total": total
    }


@router.post("/companies/{company_id}/approve")
async def approve_company(
    company_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Approve a company"""
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    company.is_approved = True
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=current_user.id,
        action="company_approved",
        resource_type="company",
        resource_id=company_id,
        details={},
        db=db
    )
    
    return {"success": True, "message": "Company approved"}


@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Get audit logs"""
    logs = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    total = db.query(AuditLog).count()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "created_at": log.created_at
            } for log in logs
        ],
        "total": total
    }


@router.post("/blacklist/{worker_id}")
async def blacklist_worker(
    worker_id: int,
    data: dict,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Add worker to global blacklist"""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    
    worker.is_blacklisted = True
    worker.blacklist_reason = data.get("reason")
    worker.status = WorkerStatus.BLOCKED
    
    db.commit()
    
    # Create audit log
    create_audit_log(
        user_id=current_user.id,
        action="worker_blacklisted",
        resource_type="worker",
        resource_id=worker_id,
        details={"reason": data.get("reason")},
        db=db
    )
    
    return {"success": True, "message": "Worker blacklisted"}


@router.get("/analytics")
async def get_analytics(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Get platform analytics"""
    # Workers by category
    workers_by_category = db.query(
        Worker.category,
        func.count(Worker.id)
    ).group_by(Worker.category).all()
    
    # Workers by status
    workers_by_status = db.query(
        Worker.status,
        func.count(Worker.id)
    ).group_by(Worker.status).all()
    
    # Complaints by category
    complaints_by_category = db.query(
        Complaint.category,
        func.count(Complaint.id)
    ).group_by(Complaint.category).all()
    
    return {
        "workers_by_category": {str(cat): count for cat, count in workers_by_category},
        "workers_by_status": {str(status): count for status, count in workers_by_status},
        "complaints_by_category": {str(cat): count for cat, count in complaints_by_category}
    }

