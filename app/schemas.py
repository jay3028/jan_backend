"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    WORKER = "worker"
    DELIVERY_WORKER = "delivery_worker"
    AEPS_AGENT = "aeps_agent"
    COMPANY = "company"
    POLICE = "police"
    ADMIN = "admin"


class WorkerCategory(str, Enum):
    DELIVERY_WORKER = "delivery_worker"
    AEPS_AGENT = "aeps_agent"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class WorkerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"
    PENDING_VERIFICATION = "pending_verification"


class ComplaintCategory(str, Enum):
    FRAUD = "fraud"
    MISBEHAVIOR = "misbehavior"
    MISUSE = "misuse"
    THEFT = "theft"
    OTHER = "other"


# Auth Schemas
class SignupRequest(BaseModel):
    full_name: str
    role: UserRole
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    otp: Optional[str] = None


class LoginRequest(BaseModel):
    login_method: str  # email_password, mobile_otp, mobile_password
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    password: Optional[str] = None
    otp: Optional[str] = None


class OTPRequest(BaseModel):
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    purpose: str  # signup, login, email_verification


class OTPVerify(BaseModel):
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    otp: str
    purpose: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# User Schemas
class UserBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None
    mobile: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    email_verified: bool
    mobile_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Worker Schemas
class WorkerOnboardingStep1(BaseModel):
    """Step 1: Basic info and category"""
    category: WorkerCategory
    full_name: str
    mobile: str


class WorkerOnboardingStep2(BaseModel):
    """Step 2: Address"""
    address_current: str
    city: str
    state: str
    pincode: str


class WorkerOnboardingStep3(BaseModel):
    """Step 3: Selfie (URL after upload)"""
    selfie_url: str


class WorkerOnboardingStep4(BaseModel):
    """Step 4: Aadhaar reference"""
    aadhaar_reference: str


class WorkerOnboardingStep5(BaseModel):
    """Step 5: AePS specific (if applicable)"""
    bank_affiliation: Optional[str] = None
    bc_affiliation: Optional[str] = None
    aeps_operator_id: Optional[str] = None
    service_region: Optional[str] = None
    aeps_device_info: Optional[str] = None
    transaction_role: Optional[str] = None


class WorkerOnboardingStep6(BaseModel):
    """Step 6: Consent and declaration"""
    consent_given: bool
    declaration_signed: bool
    device_fingerprint: Optional[str] = None


class WorkerOnboardComplete(BaseModel):
    """Complete onboarding data"""
    category: WorkerCategory
    address_current: str
    city: str
    state: str
    pincode: str
    selfie_url: str
    aadhaar_reference: str
    consent_given: bool
    declaration_signed: bool
    device_fingerprint: Optional[str] = None
    # AePS specific
    bank_affiliation: Optional[str] = None
    bc_affiliation: Optional[str] = None
    aeps_operator_id: Optional[str] = None
    service_region: Optional[str] = None
    aeps_device_info: Optional[str] = None
    transaction_role: Optional[str] = None


class WorkerResponse(BaseModel):
    id: int
    worker_id: Optional[str] = None
    user_id: int
    category: str
    status: str
    verification_status: str
    risk_score: float
    complaint_count: int
    qr_code_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkerDetailResponse(WorkerResponse):
    address_current: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    selfie_url: Optional[str] = None
    bank_affiliation: Optional[str] = None
    current_company_id: Optional[int] = None
    onboarding_step: int


# Company Schemas
class CompanyRegister(BaseModel):
    company_name: str
    cin: Optional[str] = None
    registration_id: Optional[str] = None
    signatory_name: str
    signatory_email: EmailStr
    signatory_mobile: str
    address: str
    city: str
    state: str


class CompanyResponse(BaseModel):
    id: int
    company_name: str
    cin: Optional[str] = None
    is_approved: bool
    api_key: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Police Verification Schemas
class PoliceVerificationCreate(BaseModel):
    worker_id: int
    status: VerificationStatus
    external_verification_ref: Optional[str] = None
    external_system: Optional[str] = None
    certificate_url: Optional[str] = None
    certificate_number: Optional[str] = None
    remarks: Optional[str] = None
    rejection_reason: Optional[str] = None


class PoliceVerificationResponse(BaseModel):
    id: int
    worker_id: int
    officer_id: int
    status: str
    verification_date: Optional[datetime] = None
    face_match_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FaceVerificationRequest(BaseModel):
    worker_id: int
    live_face_image_url: str


class FaceVerificationResponse(BaseModel):
    match_score: float
    is_match: bool
    liveness_detected: bool
    confidence: float


# Complaint Schemas
class ComplaintCreate(BaseModel):
    worker_id: int
    category: ComplaintCategory
    title: str
    description: str
    evidence_urls: Optional[List[str]] = None


class ComplaintResponse(BaseModel):
    id: int
    complaint_number: str
    worker_id: int
    category: str
    title: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Incident Schemas
class IncidentCreate(BaseModel):
    worker_id: int
    title: str
    description: str
    incident_type: str
    severity: str
    incident_date: datetime
    location: Optional[str] = None
    action_taken: Optional[str] = None


# Verification Schemas
class VerifyWorkerRequest(BaseModel):
    worker_id: Optional[str] = None
    mobile: Optional[str] = None
    qr_data: Optional[str] = None


class VerifyWorkerResponse(BaseModel):
    worker_id: str
    full_name: str
    photo_url: str
    role: str
    company_name: Optional[str] = None
    verification_status: str
    police_verified: bool
    last_verification_date: Optional[datetime] = None
    risk_score: float
    is_active: bool


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_workers: int
    active_workers: int
    pending_verifications: int
    total_complaints: int
    high_risk_workers: int


class WorkerUpdateStatus(BaseModel):
    worker_id: int
    status: WorkerStatus
    reason: Optional[str] = None

