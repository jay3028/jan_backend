"""
Services initialization
"""
from .otp_service import otp_service
from .face_verification import face_verification_service
from .qr_service import qr_service

__all__ = ['otp_service', 'face_verification_service', 'qr_service']

