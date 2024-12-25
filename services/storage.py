# services/storage.py
from typing import Dict, List, Optional
import logging
from pathlib import Path
from supabase import create_client, Client
from models.submission import Submission
from models.assignment import Assignment
from config.settings import get_settings
import streamlit as st
import json
import time

class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.supabase: Client = create_client(
            self.settings.supabase_url,
            self.settings.supabase_key
        )
        # Sets the auth token from session state if both tokens exist
        if 'access_token' in st.session_state and 'refresh_token' in st.session_state:
            self.supabase.auth.set_session(
                access_token=st.session_state.access_token,
                refresh_token=st.session_state.refresh_token
            )
        self.logger = logging.getLogger(__name__)

    def _get_teacher_id(self) -> str:
        """Get current teacher's ID from auth context"""
        if 'user' not in st.session_state:
            raise ValueError("No authenticated user found")
            
        auth_id = st.session_state.user.id
        result = self.supabase.table('teachers') \
            .select('id') \
            .eq('auth_id', auth_id) \
            .single() \
            .execute()
            
        return result.data['id']

    def upload_image(self, file_path: str, assignment_id: str) -> str:
        """Upload image to Supabase storage"""
        try:
            path = Path(file_path)
            timestamp = int(time.time())
            storage_path = f"{assignment_id}/{timestamp}_{path.name}"
            self.logger.info(f"Storage path: {storage_path}")
            
            with open(file_path, 'rb') as f:
                try:
                    # Upload file
                    self.logger.info(f"Uploading to bucket: {self.settings.storage_bucket}")
                    upload_result = self.supabase.storage \
                        .from_(self.settings.storage_bucket) \
                        .upload(storage_path, f)
                    
                    if not upload_result:
                        raise Exception("Upload failed - no response received")

                    # Get signed URL with 1 year expiration
                    expiry = 365 * 24 * 60 * 60  # 1 year in seconds
                    signed_url = self.supabase.storage \
                        .from_(self.settings.storage_bucket) \
                        .create_signed_url(storage_path, expiry)
                    
                    self.logger.info(f"Generated signed URL: {signed_url}")
                    return signed_url['signedURL']
                        
                except Exception as upload_error:
                    raise Exception(f"Upload failed: {str(upload_error)}")

        except Exception as e:
            self.logger.error(f"Image upload failed: {str(e)}")
            raise

    def create_submission(self, submission: Submission) -> str:
        """
        Create new submission record
        """
        try:
            data = submission.to_dict()
            result = self.supabase.table('submissions') \
                .insert(data) \
                .execute()
                
            return result.data[0]['id']

        except Exception as e:
            self.logger.error(f"Submission creation failed: {str(e)}")
            raise

    def update_submission(self, 
                         submission_id: str,
                         updates: Dict) -> None:
        """
        Update submission record
        """
        try:
            self.supabase.table('submissions') \
                .update(updates) \
                .eq('id', submission_id) \
                .execute()

        except Exception as e:
            self.logger.error(f"Submission update failed: {str(e)}")
            raise

    def get_submission(self, submission_id: str) -> Optional[Dict]:
        """
        Get submission by ID
        """
        try:
            result = self.supabase.table('submissions') \
                .select('*') \
                .eq('id', submission_id) \
                .single() \
                .execute()
                
            return result.data

        except Exception as e:
            self.logger.error(f"Submission retrieval failed: {str(e)}")
            return None

    def _refresh_image_url(self, image_path: str) -> str:
        """Refresh a signed URL for an image"""
        try:
            # Extract storage path from full URL, avoiding double bucket names
            path_parts = image_path.split('/storage/v1/object/')[1].split('?')[0]
            
            # Remove any prefix and bucket name from path
            clean_path = path_parts
            for prefix in ['public/', 'sign/']:
                if clean_path.startswith(prefix):
                    clean_path = clean_path[len(prefix):]
            
            # Remove bucket name if it appears twice
            bucket_prefix = f"{self.settings.storage_bucket}/"
            if clean_path.startswith(bucket_prefix):
                clean_path = clean_path[len(bucket_prefix):]
            
            storage_path = clean_path
                
            # Create new signed URL
            expiry = 365 * 24 * 60 * 60  # 1 year in seconds
            signed_url = self.supabase.storage \
                .from_(self.settings.storage_bucket) \
                .create_signed_url(storage_path, expiry)
            
            return signed_url['signedURL']
        except Exception as e:
            self.logger.error(f"Failed to refresh URL: {str(e)}")
            return image_path  # Return original URL if refresh fails

    def get_submissions_by_assignment(self, assignment_id: str) -> List[Dict]:
        """
        Get all submissions for an assignment
        """
        try:
            result = self.supabase.table('submissions') \
                .select('*') \
                .eq('assignment_id', assignment_id) \
                .order('created_at', desc=True) \
                .execute()
            
            # Refresh image URLs
            submissions = result.data
            for submission in submissions:
                if submission.get('image_path'):
                    submission['image_path'] = self._refresh_image_url(submission['image_path'])
                
            return submissions

        except Exception as e:
            self.logger.error(f"Assignment submissions retrieval failed: {str(e)}")
            return []

    def get_assignment(self, assignment_id: str) -> Optional[Dict]:
        """
        Get assignment by ID
        """
        try:
            result = self.supabase.table('assignments') \
                .select('*') \
                .eq('id', assignment_id) \
                .single() \
                .execute()
                
            return result.data

        except Exception as e:
            self.logger.error(f"Assignment retrieval failed: {str(e)}")
            return None

    def create_assignment(self, assignment: Assignment) -> str:
        """
        Create new assignment record
        """
        try:
            teacher_id = self._get_teacher_id()
            
            # Set teacher ID
            assignment.teacher_id = teacher_id
            
            # Convert to database format
            data = assignment.to_dict()
            
            # Convert rubric structure to JSON string
            data['rubric_structure'] = json.dumps(data['rubric_structure'])
            
            result = self.supabase.table('assignments') \
                .insert(data) \
                .execute()
                
            return result.data[0]['id']

        except Exception as e:
            self.logger.error(f"Assignment creation failed: {str(e)}")
            raise

    def list_assignments(self) -> List[Dict]:
        """
        Get all assignments for current teacher
        """
        try:
            teacher_id = self._get_teacher_id()
            
            result = self.supabase.table('assignments') \
                .select('*') \
                .eq('teacher_id', teacher_id) \
                .order('created_at', desc=True) \
                .execute()
                
            return result.data

        except Exception as e:
            self.logger.error(f"Assignment listing failed: {str(e)}")
            return []

    def list_subjects(self) -> List[Dict]:
        """
        Get all subjects for current teacher
        """
        try:
            teacher_id = self._get_teacher_id()
            
            result = self.supabase.table('subjects') \
                .select('*') \
                .eq('teacher_id', teacher_id) \
                .order('name') \
                .execute()
                
            return result.data

        except Exception as e:
            self.logger.error(f"Subject listing failed: {str(e)}")
            return []

    def create_subject(self, name: str) -> str:
        """
        Create new subject
        """
        try:
            teacher_id = self._get_teacher_id()
            
            result = self.supabase.table('subjects') \
                .insert({
                    'name': name,
                    'teacher_id': teacher_id
                }) \
                .execute()
                
            return result.data[0]['id']

        except Exception as e:
            self.logger.error(f"Subject creation failed: {str(e)}")
            raise
