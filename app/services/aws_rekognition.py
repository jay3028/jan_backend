"""
AWS Rekognition Service for Face Recognition and Verification
Production-ready implementation with error handling and logging
"""
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import os
from typing import Optional, Dict, List, Tuple
import base64
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSRekognitionService:
    """
    Service class for AWS Rekognition face recognition operations.
    
    This service handles:
    1. Face indexing (adding faces to collection)
    2. Face searching (finding matches in collection)
    3. Collection management
    """
    
    def __init__(self):
        """Initialize AWS Rekognition client and collection"""
        print("\n" + "="*70)
        print("[REKOGNITION-INIT] Initializing AWS Rekognition Service...")
        print("="*70)
        
        try:
            # Get AWS credentials from environment
            self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            self.aws_region = os.getenv("AWS_REGION", "ap-south-1")  # Mumbai region
            self.collection_id = os.getenv("REKOGNITION_COLLECTION_ID", "jansuraksha-workers")
            
            print(f"[REKOGNITION-INIT] AWS Region: {self.aws_region}")
            print(f"[REKOGNITION-INIT] Collection ID: {self.collection_id}")
            print(f"[REKOGNITION-INIT] Access Key ID: {self.aws_access_key[:20] + '...' if self.aws_access_key else 'NOT SET'}")
            
            # Validate credentials
            if not self.aws_access_key or not self.aws_secret_key:
                print("[REKOGNITION-INIT] WARNING: AWS credentials not found in environment variables")
                print("[REKOGNITION-INIT] Face recognition feature will NOT work")
                print("[REKOGNITION-INIT] Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file")
                logger.warning("AWS credentials not found. Face recognition will not work.")
                self.client = None
                return
            
            # Initialize Rekognition client
            print("[REKOGNITION-INIT] Creating AWS Rekognition client...")
            self.client = boto3.client(
                'rekognition',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            print("[REKOGNITION-INIT] AWS Rekognition client created successfully")
            
            # Ensure collection exists
            print("[REKOGNITION-INIT] Checking/creating face collection...")
            self._ensure_collection_exists()
            
            print("[REKOGNITION-INIT] SUCCESS: AWS Rekognition initialized successfully")
            print("="*70 + "\n")
            logger.info(f"✓ AWS Rekognition initialized successfully (Region: {self.aws_region})")
            
        except Exception as e:
            print(f"[REKOGNITION-INIT] ERROR: Failed to initialize AWS Rekognition")
            print(f"[REKOGNITION-INIT] Error: {str(e)}")
            print("="*70 + "\n")
            logger.error(f"Failed to initialize AWS Rekognition: {str(e)}")
            self.client = None
    
    def _ensure_collection_exists(self):
        """Ensure the face collection exists, create if it doesn't"""
        if not self.client:
            print("[REKOGNITION-INIT] WARNING: Client not initialized, skipping collection check")
            return
        
        try:
            # Try to describe the collection
            print(f"[REKOGNITION-INIT] Checking if collection '{self.collection_id}' exists...")
            response = self.client.describe_collection(CollectionId=self.collection_id)
            face_count = response.get('FaceCount', 0)
            print(f"[REKOGNITION-INIT] Collection '{self.collection_id}' exists")
            print(f"[REKOGNITION-INIT] Current indexed faces: {face_count}")
            logger.info(f"✓ Collection '{self.collection_id}' exists")
            
        except self.client.exceptions.ResourceNotFoundException:
            # Collection doesn't exist, create it
            print(f"[REKOGNITION-INIT] Collection '{self.collection_id}' not found")
            print(f"[REKOGNITION-INIT] Creating new collection...")
            try:
                self.client.create_collection(CollectionId=self.collection_id)
                print(f"[REKOGNITION-INIT] SUCCESS: Created new collection '{self.collection_id}'")
                logger.info(f"✓ Created new collection '{self.collection_id}'")
            except ClientError as e:
                print(f"[REKOGNITION-INIT] ERROR: Failed to create collection: {str(e)}")
                logger.error(f"Failed to create collection: {str(e)}")
                raise
        
        except ClientError as e:
            print(f"[REKOGNITION-INIT] ERROR: Failed to check collection: {str(e)}")
            logger.error(f"Error checking collection: {str(e)}")
            raise
    
    def index_face(
        self, 
        image_path: str, 
        worker_id: str,
        external_image_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Index a face into the Rekognition collection.
        
        Args:
            image_path: Path to the image file
            worker_id: Worker's official ID (e.g., IND-WRK-DLV-2025-000001)
            external_image_id: Optional external ID (defaults to worker_id)
        
        Returns:
            Tuple of (success, face_data, error_message)
        """
        print(f"\n[REKOGNITION-INDEX] Starting face indexing process...")
        print(f"[REKOGNITION-INDEX] Worker ID: {worker_id}")
        print(f"[REKOGNITION-INDEX] Image Path: {image_path}")
        print(f"[REKOGNITION-INDEX] Collection: {self.collection_id}")
        
        if not self.client:
            print("[REKOGNITION-INDEX] ERROR: AWS Rekognition client not configured")
            return False, None, "AWS Rekognition not configured"
        
        try:
            # Read image file
            print(f"[REKOGNITION-INDEX] Reading image file...")
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            image_size_kb = len(image_bytes) / 1024
            print(f"[REKOGNITION-INDEX] Image size: {image_size_kb:.2f} KB")
            
            # Use worker_id as external_image_id if not provided
            if not external_image_id:
                external_image_id = worker_id
            
            print(f"[REKOGNITION-INDEX] External Image ID: {external_image_id}")
            
            # Index the face
            print(f"[REKOGNITION-INDEX] Calling AWS Rekognition IndexFaces API...")
            response = self.client.index_faces(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_image_id,
                MaxFaces=1,  # Only index one face (the main subject)
                QualityFilter="AUTO",  # Filter out low-quality faces
                DetectionAttributes=['ALL']
            )
            
            print(f"[REKOGNITION-INDEX] API call successful")
            
            # Check if any faces were indexed
            if not response['FaceRecords']:
                print("[REKOGNITION-INDEX] WARNING: No face detected in the image")
                return False, None, "No face detected in image"
            
            print(f"[REKOGNITION-INDEX] Faces detected: {len(response['FaceRecords'])}")
            
            face_record = response['FaceRecords'][0]
            face_id = face_record['Face']['FaceId']
            confidence = face_record['Face']['Confidence']
            brightness = face_record['FaceDetail']['Quality']['Brightness']
            sharpness = face_record['FaceDetail']['Quality']['Sharpness']
            
            print(f"[REKOGNITION-INDEX] Face ID: {face_id}")
            print(f"[REKOGNITION-INDEX] Confidence: {confidence:.2f}%")
            print(f"[REKOGNITION-INDEX] Image Quality - Brightness: {brightness:.2f}, Sharpness: {sharpness:.2f}")
            
            # Extract face details
            face_data = {
                'face_id': face_id,
                'external_image_id': external_image_id,
                'worker_id': worker_id,
                'confidence': confidence,
                'image_quality': {
                    'brightness': brightness,
                    'sharpness': sharpness
                },
                'bounding_box': face_record['Face']['BoundingBox']
            }
            
            print(f"[REKOGNITION-INDEX] SUCCESS: Face indexed successfully for worker {worker_id}")
            logger.info(f"✓ Face indexed successfully for worker {worker_id} (FaceID: {face_id})")
            
            return True, face_data, None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            print(f"[REKOGNITION-INDEX] ERROR: AWS ClientError occurred")
            print(f"[REKOGNITION-INDEX] Error Code: {error_code}")
            print(f"[REKOGNITION-INDEX] Error Message: {error_message}")
            
            if error_code == 'InvalidParameterException':
                print("[REKOGNITION-INDEX] ERROR: Invalid image format or no face detected")
                return False, None, "Invalid image format or no face detected"
            elif error_code == 'InvalidImageFormatException':
                print("[REKOGNITION-INDEX] ERROR: Invalid image format")
                return False, None, "Invalid image format. Please use JPG or PNG"
            else:
                logger.error(f"AWS Rekognition error: {error_code} - {error_message}")
                return False, None, f"Face indexing failed: {error_message}"
        
        except FileNotFoundError:
            print(f"[REKOGNITION-INDEX] ERROR: Image file not found at path: {image_path}")
            return False, None, f"Image file not found: {image_path}"
        
        except Exception as e:
            print(f"[REKOGNITION-INDEX] ERROR: Unexpected error - {str(e)}")
            logger.error(f"Unexpected error during face indexing: {str(e)}")
            return False, None, f"Face indexing failed: {str(e)}"
    
    def search_face_by_image(
        self, 
        image_path: str,
        threshold: float = 80.0,
        max_faces: int = 5
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Search for matching faces in the collection using an image.
        
        Args:
            image_path: Path to the image file to search with
            threshold: Minimum confidence threshold (0-100)
            max_faces: Maximum number of matches to return
        
        Returns:
            Tuple of (success, matches, error_message)
        """
        if not self.client:
            return False, [], "AWS Rekognition not configured"
        
        try:
            # Read image file
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Search for matching faces
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=max_faces,
                FaceMatchThreshold=threshold
            )
            
            # Check if any matches were found
            if not response['FaceMatches']:
                return True, [], None  # No matches, but no error
            
            # Process matches
            matches = []
            for match in response['FaceMatches']:
                face = match['Face']
                matches.append({
                    'face_id': face['FaceId'],
                    'worker_id': face.get('ExternalImageId', 'Unknown'),
                    'similarity': match['Similarity'],
                    'confidence': face['Confidence']
                })
            
            # Sort by similarity (highest first)
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            
            logger.info(f"✓ Face search completed. Found {len(matches)} matches")
            
            return True, matches, None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'InvalidParameterException':
                return False, [], "No face detected in the search image"
            elif error_code == 'InvalidImageFormatException':
                return False, [], "Invalid image format. Please use JPG or PNG"
            else:
                logger.error(f"AWS Rekognition error: {error_code} - {error_message}")
                return False, [], f"Face search failed: {error_message}"
        
        except FileNotFoundError:
            return False, [], f"Image file not found: {image_path}"
        
        except Exception as e:
            logger.error(f"Unexpected error during face search: {str(e)}")
            return False, [], f"Face search failed: {str(e)}"
    
    def search_face_by_base64(
        self,
        base64_image: str,
        threshold: float = 80.0,
        max_faces: int = 5
    ) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Search for matching faces using a base64-encoded image.
        
        Args:
            base64_image: Base64-encoded image string
            threshold: Minimum confidence threshold (0-100)
            max_faces: Maximum number of matches to return
        
        Returns:
            Tuple of (success, matches, error_message)
        """
        print(f"\n[REKOGNITION-SEARCH] Starting face search process...")
        print(f"[REKOGNITION-SEARCH] Collection: {self.collection_id}")
        print(f"[REKOGNITION-SEARCH] Threshold: {threshold}%")
        print(f"[REKOGNITION-SEARCH] Max Faces: {max_faces}")
        
        if not self.client:
            print("[REKOGNITION-SEARCH] ERROR: AWS Rekognition client not configured")
            return False, [], "AWS Rekognition not configured"
        
        try:
            # Remove data URL prefix if present
            print("[REKOGNITION-SEARCH] Processing base64 image...")
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]
                print("[REKOGNITION-SEARCH] Removed data URL prefix")
            
            # Decode base64 image
            image_bytes = base64.b64decode(base64_image)
            image_size_kb = len(image_bytes) / 1024
            print(f"[REKOGNITION-SEARCH] Decoded image size: {image_size_kb:.2f} KB")
            
            # Search for matching faces
            print(f"[REKOGNITION-SEARCH] Calling AWS Rekognition SearchFacesByImage API...")
            response = self.client.search_faces_by_image(
                CollectionId=self.collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=max_faces,
                FaceMatchThreshold=threshold
            )
            
            print(f"[REKOGNITION-SEARCH] API call successful")
            
            # Check if any matches were found
            if not response['FaceMatches']:
                print("[REKOGNITION-SEARCH] No matching faces found in the collection")
                return True, [], None  # No matches, but no error
            
            print(f"[REKOGNITION-SEARCH] Found {len(response['FaceMatches'])} potential matches")
            
            # Process matches
            matches = []
            for idx, match in enumerate(response['FaceMatches'], 1):
                face = match['Face']
                worker_id = face.get('ExternalImageId', 'Unknown')
                similarity = match['Similarity']
                confidence = face['Confidence']
                
                print(f"[REKOGNITION-SEARCH] Match #{idx}:")
                print(f"  - Worker ID: {worker_id}")
                print(f"  - Similarity: {similarity:.2f}%")
                print(f"  - Confidence: {confidence:.2f}%")
                print(f"  - Face ID: {face['FaceId']}")
                
                matches.append({
                    'face_id': face['FaceId'],
                    'worker_id': worker_id,
                    'similarity': similarity,
                    'confidence': confidence
                })
            
            # Sort by similarity (highest first)
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            
            print(f"[REKOGNITION-SEARCH] SUCCESS: Face search completed with {len(matches)} matches")
            print(f"[REKOGNITION-SEARCH] Top match: {matches[0]['worker_id']} ({matches[0]['similarity']:.2f}% similarity)")
            logger.info(f"✓ Face search completed. Found {len(matches)} matches")
            
            return True, matches, None
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            print(f"[REKOGNITION-SEARCH] ERROR: AWS ClientError occurred")
            print(f"[REKOGNITION-SEARCH] Error Code: {error_code}")
            print(f"[REKOGNITION-SEARCH] Error Message: {error_message}")
            
            if error_code == 'InvalidParameterException':
                print("[REKOGNITION-SEARCH] ERROR: No face detected in the search image")
                return False, [], "No face detected in the search image"
            elif error_code == 'InvalidImageFormatException':
                print("[REKOGNITION-SEARCH] ERROR: Invalid image format")
                return False, [], "Invalid image format. Please use JPG or PNG"
            else:
                logger.error(f"AWS Rekognition error: {error_code} - {error_message}")
                return False, [], f"Face search failed: {error_message}"
        
        except Exception as e:
            print(f"[REKOGNITION-SEARCH] ERROR: Unexpected error - {str(e)}")
            logger.error(f"Unexpected error during face search: {str(e)}")
            return False, [], f"Face search failed: {str(e)}"
    
    def delete_face(self, face_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a face from the collection.
        
        Args:
            face_id: The face ID to delete
        
        Returns:
            Tuple of (success, error_message)
        """
        if not self.client:
            return False, "AWS Rekognition not configured"
        
        try:
            self.client.delete_faces(
                CollectionId=self.collection_id,
                FaceIds=[face_id]
            )
            
            logger.info(f"✓ Face deleted successfully (FaceID: {face_id})")
            return True, None
            
        except ClientError as e:
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to delete face: {error_message}")
            return False, error_message
        
        except Exception as e:
            logger.error(f"Unexpected error deleting face: {str(e)}")
            return False, str(e)
    
    def get_collection_stats(self) -> Optional[Dict]:
        """Get statistics about the face collection"""
        if not self.client:
            return None
        
        try:
            response = self.client.describe_collection(CollectionId=self.collection_id)
            
            return {
                'face_count': response['FaceCount'],
                'collection_arn': response['CollectionARN'],
                'created_timestamp': response['CreationTimestamp']
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return None


# Global instance
rekognition_service = AWSRekognitionService()

