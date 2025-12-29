"""
FastAPI dependencies for authentication and authorization
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User, Worker, Company, PoliceOfficer
from app.auth import decode_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("user_id")
        print(f"[AUTH-CHECK] Token decoded - User ID: {user_id}")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"[AUTH-CHECK] ✗ User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            print(f"[AUTH-CHECK] ✗ User inactive: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        print(f"[AUTH-CHECK] ✓ User authenticated: {user.id} ({user.role.value})")
        return user
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def require_role(*roles: str):
    """Dependency to require specific roles"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(roles)}"
            )
        return current_user
    return role_checker


def get_current_worker(
    current_user: User = Depends(require_role("worker", "delivery_worker", "aeps_agent")),
    db: Session = Depends(get_db)
) -> Worker:
    """Get current worker profile"""
    worker = db.query(Worker).filter(Worker.user_id == current_user.id).first()
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker profile not found"
        )
    return worker


def get_current_company(
    current_user: User = Depends(require_role("company")),
    db: Session = Depends(get_db)
) -> Company:
    """Get current company profile"""
    company = db.query(Company).filter(Company.user_id == current_user.id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    return company


def get_current_police_officer(
    current_user: User = Depends(require_role("police")),
    db: Session = Depends(get_db)
) -> PoliceOfficer:
    """Get current police officer profile"""
    officer = db.query(PoliceOfficer).filter(PoliceOfficer.user_id == current_user.id).first()
    if not officer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Police officer profile not found"
        )
    return officer


def verify_api_key(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Company:
    """Verify company API key"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    company = db.query(Company).filter(Company.api_key == x_api_key).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return company


def create_audit_log(
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[str],
    details: Optional[dict],
    db: Session
):
    """Create audit log entry"""
    from app.models import AuditLog
    
    print(f"\n[AUDIT-LOG] Creating audit entry")
    print(f"[AUDIT-LOG] User ID: {user_id}, Action: {action}")
    print(f"[AUDIT-LOG] Resource: {resource_type}/{resource_id}")
    
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        details=details
    )
    db.add(log)
    db.commit()
    print(f"[AUDIT-LOG] ✓ Audit entry created (ID: {log.id})")

