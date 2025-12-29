"""
Database models for Jan Suraksha platform
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    WORKER = "worker"
    DELIVERY_WORKER = "delivery_worker"
    AEPS_AGENT = "aeps_agent"
    COMPANY = "company"
    POLICE = "police"
    ADMIN = "admin"


class WorkerCategory(str, enum.Enum):
    DELIVERY_WORKER = "delivery_worker"
    AEPS_AGENT = "aeps_agent"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class WorkerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"
    PENDING_VERIFICATION = "pending_verification"


class ComplaintCategory(str, enum.Enum):
    FRAUD = "fraud"
    MISBEHAVIOR = "misbehavior"
    MISUSE = "misuse"
    THEFT = "theft"
    OTHER = "other"


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class User(Base):
    """Base user table for all roles"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    mobile = Column(String(20), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    mobile_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Device binding fingerprint
    device_fingerprint = Column(String(255), nullable=True)
    
    # Relationships
    worker = relationship("Worker", back_populates="user", uselist=False)
    company = relationship("Company", back_populates="user", uselist=False)
    police_officer = relationship("PoliceOfficer", back_populates="user", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="user")


class Worker(Base):
    """Worker profile - Delivery Worker or AePS Agent"""
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Universal Worker ID: IND-WRK-ROLE-YYYY-XXXXXX
    worker_id = Column(String(50), unique=True, index=True)
    
    # Category
    category = Column(Enum(WorkerCategory), nullable=False)
    
    # Common Fields
    address_current = Column(Text, nullable=True)
    address_permanent = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    
    # Aadhaar reference (token, not raw number)
    aadhaar_reference = Column(String(255), nullable=True)
    
    # Selfie & biometrics
    selfie_url = Column(String(500), nullable=True)
    selfie_embedding = Column(Text, nullable=True)  # Face embedding for matching
    
    # Consent
    consent_given = Column(Boolean, default=False)
    consent_timestamp = Column(DateTime(timezone=True), nullable=True)
    declaration_signed = Column(Boolean, default=False)
    
    # AePS specific fields
    bank_affiliation = Column(String(255), nullable=True)
    bc_affiliation = Column(String(255), nullable=True)
    aeps_operator_id = Column(String(100), nullable=True)
    service_region = Column(String(255), nullable=True)
    aeps_device_info = Column(Text, nullable=True)
    transaction_role = Column(String(255), nullable=True)
    
    # Status
    status = Column(Enum(WorkerStatus), default=WorkerStatus.PENDING_VERIFICATION)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    
    # Risk management
    risk_score = Column(Float, default=0.0)
    complaint_count = Column(Integer, default=0)
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(Text, nullable=True)
    
    # Company affiliation
    current_company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # QR Code
    qr_code_url = Column(String(500), nullable=True)
    verification_endpoint = Column(String(500), nullable=True)
    
    # Onboarding progress
    onboarding_step = Column(Integer, default=1)
    onboarding_data = Column(JSON, nullable=True)  # Store step-wise data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="worker")
    current_company = relationship("Company", back_populates="workers")
    police_verifications = relationship("PoliceVerification", back_populates="worker")
    complaints = relationship("Complaint", back_populates="worker")
    company_links = relationship("WorkerCompanyLink", back_populates="worker")


class Company(Base):
    """Company/Platform that employs workers"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    company_name = Column(String(255), nullable=False)
    cin = Column(String(50), unique=True, nullable=True)
    registration_id = Column(String(100), unique=True, nullable=True)
    
    # Authorized signatory
    signatory_name = Column(String(255), nullable=True)
    signatory_email = Column(String(255), nullable=True)
    signatory_mobile = Column(String(20), nullable=True)
    
    # API access
    api_key = Column(String(255), unique=True, nullable=True)
    api_key_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Company details
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    
    is_approved = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="company")
    workers = relationship("Worker", back_populates="current_company")
    complaints_submitted = relationship("Complaint", back_populates="submitted_by_company")
    worker_links = relationship("WorkerCompanyLink", back_populates="company")


class WorkerCompanyLink(Base):
    """Link workers to companies with status tracking"""
    __tablename__ = "worker_company_links"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    
    status = Column(Enum(WorkerStatus), default=WorkerStatus.ACTIVE)
    linked_at = Column(DateTime(timezone=True), server_default=func.now())
    unlinked_at = Column(DateTime(timezone=True), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    # Relationships
    worker = relationship("Worker", back_populates="company_links")
    company = relationship("Company", back_populates="worker_links")


class PoliceOfficer(Base):
    """Police officer profile"""
    __tablename__ = "police_officers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    officer_id = Column(String(50), unique=True)
    station_code = Column(String(50))
    station_name = Column(String(255))
    district = Column(String(100))
    state = Column(String(100))
    rank = Column(String(100))
    
    # Digital signature reference
    digital_signature_ref = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="police_officer")
    verifications = relationship("PoliceVerification", back_populates="officer")
    incidents = relationship("Incident", back_populates="officer")


class PoliceVerification(Base):
    """Police verification records for workers"""
    __tablename__ = "police_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    officer_id = Column(Integer, ForeignKey("police_officers.id"))
    
    # Verification details
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # External verification (ICJS/CCTNS reference only)
    external_verification_ref = Column(String(255), nullable=True)
    external_system = Column(String(50), nullable=True)  # "ICJS", "CCTNS"
    
    # Certificate
    certificate_url = Column(String(500), nullable=True)
    certificate_number = Column(String(100), nullable=True)
    
    # Face verification
    face_match_score = Column(Float, nullable=True)
    face_match_performed = Column(Boolean, default=False)
    liveness_check = Column(Boolean, default=False)
    
    # Remarks
    remarks = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Audit trail
    verification_steps = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    worker = relationship("Worker", back_populates="police_verifications")
    officer = relationship("PoliceOfficer", back_populates="verifications")


class Complaint(Base):
    """Complaints against workers"""
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_number = Column(String(50), unique=True)
    
    worker_id = Column(Integer, ForeignKey("workers.id"))
    
    # Complaint source
    submitted_by_company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    submitted_by_citizen_name = Column(String(255), nullable=True)
    submitted_by_citizen_contact = Column(String(50), nullable=True)
    submitted_by_police = Column(Boolean, default=False)
    
    # Complaint details
    category = Column(Enum(ComplaintCategory))
    title = Column(String(500))
    description = Column(Text)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.OPEN)
    
    # Evidence
    evidence_urls = Column(JSON, nullable=True)
    
    # Investigation
    assigned_officer_id = Column(Integer, ForeignKey("police_officers.id"), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    worker = relationship("Worker", back_populates="complaints")
    submitted_by_company = relationship("Company", back_populates="complaints_submitted")
    assigned_officer = relationship("PoliceOfficer")


class Incident(Base):
    """Police incident logs"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_number = Column(String(50), unique=True)
    
    worker_id = Column(Integer, ForeignKey("workers.id"))
    officer_id = Column(Integer, ForeignKey("police_officers.id"))
    
    title = Column(String(500))
    description = Column(Text)
    incident_type = Column(String(100))
    severity = Column(String(50))
    
    incident_date = Column(DateTime(timezone=True))
    location = Column(String(500), nullable=True)
    
    action_taken = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    worker = relationship("Worker")
    officer = relationship("PoliceOfficer", back_populates="incidents")


class OTPVerification(Base):
    """OTP verification tracking"""
    __tablename__ = "otp_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    email = Column(String(255), nullable=True)
    mobile = Column(String(20), nullable=True)
    
    otp_code = Column(String(10))
    purpose = Column(String(50))  # signup, login, email_verification
    
    is_verified = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    verified_at = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """Audit trail for all actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    action = Column(String(255))
    resource_type = Column(String(100))
    resource_id = Column(String(100), nullable=True)
    
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class SystemConfig(Base):
    """System configuration and settings"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True)
    value = Column(Text)
    description = Column(Text, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

