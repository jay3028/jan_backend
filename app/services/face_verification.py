"""
Face verification service using AWS Rekognition
"""
import boto3
import os
from typing import Dict, Tuple
import requests
from io import BytesIO


class FaceVerificationService:
    def __init__(self):
        # AWS Rekognition client
        self.rekognition = boto3.client(
            'rekognition',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
    
    def download_image(self, image_url: str) -> bytes:
        """Download image from URL"""
        response = requests.get(image_url)
        response.raise_for_status()
        return response.content
    
    def compare_faces(self, source_image_url: str, target_image_url: str) -> Dict:
        """
        Compare two faces using AWS Rekognition
        Returns match score and confidence
        """
        try:
            # Download images
            source_bytes = self.download_image(source_image_url)
            target_bytes = self.download_image(target_image_url)
            
            # Compare faces
            response = self.rekognition.compare_faces(
                SourceImage={'Bytes': source_bytes},
                TargetImage={'Bytes': target_bytes},
                SimilarityThreshold=70  # Minimum similarity threshold
            )
            
            if response['FaceMatches']:
                match = response['FaceMatches'][0]
                return {
                    'is_match': True,
                    'similarity': match['Similarity'],
                    'confidence': match['Face']['Confidence']
                }
            else:
                return {
                    'is_match': False,
                    'similarity': 0.0,
                    'confidence': 0.0
                }
        
        except Exception as e:
            print(f"Error comparing faces: {str(e)}")
            raise Exception(f"Face comparison failed: {str(e)}")
    
    def detect_faces(self, image_url: str) -> Dict:
        """Detect faces in an image"""
        try:
            image_bytes = self.download_image(image_url)
            
            response = self.rekognition.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )
            
            if response['FaceDetails']:
                face = response['FaceDetails'][0]
                return {
                    'face_detected': True,
                    'confidence': face['Confidence'],
                    'age_range': face.get('AgeRange', {}),
                    'gender': face.get('Gender', {}),
                    'emotions': face.get('Emotions', [])
                }
            else:
                return {
                    'face_detected': False
                }
        
        except Exception as e:
            print(f"Error detecting faces: {str(e)}")
            raise Exception(f"Face detection failed: {str(e)}")
    
    def check_liveness(self, image_url: str) -> Dict:
        """
        Basic liveness check
        In production, use AWS Rekognition Liveness API or similar
        """
        try:
            face_details = self.detect_faces(image_url)
            
            if not face_details['face_detected']:
                return {
                    'is_live': False,
                    'confidence': 0.0,
                    'reason': 'No face detected'
                }
            
            # Simple heuristic: check if face looks natural
            # In production, use proper liveness detection
            confidence = face_details.get('confidence', 0)
            
            return {
                'is_live': confidence > 90,
                'confidence': confidence,
                'reason': 'Basic liveness check passed' if confidence > 90 else 'Low confidence'
            }
        
        except Exception as e:
            print(f"Error checking liveness: {str(e)}")
            raise Exception(f"Liveness check failed: {str(e)}")
    
    def verify_worker_face(self, worker_selfie_url: str, live_image_url: str) -> Tuple[bool, float, bool]:
        """
        Complete face verification workflow
        Returns: (is_match, match_score, is_live)
        """
        # Check liveness of live image
        liveness = self.check_liveness(live_image_url)
        
        if not liveness['is_live']:
            return False, 0.0, False
        
        # Compare faces
        comparison = self.compare_faces(worker_selfie_url, live_image_url)
        
        return (
            comparison['is_match'],
            comparison['similarity'],
            liveness['is_live']
        )


face_verification_service = FaceVerificationService()

