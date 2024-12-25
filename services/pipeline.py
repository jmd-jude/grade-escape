# services/pipeline.py
import logging
from typing import Optional, Dict
from pathlib import Path

from models.submission import Submission
from models.assignment import Assignment
from services.ocr_service import OCRService
from services.grading import GradingService
from services.feedback import FeedbackService
from services.storage import StorageService
from config.settings import get_settings

class ProcessingPipeline:
    def __init__(self):
        self.settings = get_settings()
        self.ocr_service = OCRService()
        self.grading_service = GradingService()
        self.feedback_service = FeedbackService()
        self.storage_service = StorageService()
        self.logger = logging.getLogger(__name__)
    
    def process_submission(self,
                         image_path: str,
                         assignment_id: str,
                         student_id: str,
                         on_stage_change: callable = None) -> Optional[Dict]:
        """
        Process a single submission through the entire pipeline
        """
        try:
            # 1. Get assignment details first
            assignment_data = self.storage_service.get_assignment(assignment_id)
            if not assignment_data:
                raise ValueError(f"Assignment {assignment_id} not found")
            
            # 2. Upload image and create submission
            try:
                self.logger.info("Starting image upload...")
                if on_stage_change:
                    on_stage_change("UPLOAD", "Uploading image...")
                
                public_url = self.storage_service.upload_image(
                    image_path, 
                    assignment_id
                )
                self.logger.info(f"Image uploaded successfully: {public_url}")
                
                # Log the URL for debugging
                self.logger.info(f"Creating submission with image URL: {public_url}")
                
                # Create submission instance with public URL
                submission = Submission(
                    assignment_id=assignment_id,
                    student_id=student_id,
                    image_path=public_url,
                    status="pending"
                )
                
                # Log submission data
                self.logger.info(f"Submission data: {submission.to_dict()}")
                
                submission_id = self.storage_service.create_submission(submission)
                
            except Exception as upload_error:
                self.logger.error(f"Failed to upload image or create submission: {str(upload_error)}")
                raise ValueError(f"Submission creation failed: {str(upload_error)}")
            
            # 3. Process image with OCR and update submission
            try:
                self.logger.info("Starting OCR processing...")
                if on_stage_change:
                    on_stage_change("OCR", "Processing image with OCR...")
                
                ocr_result = self.ocr_service.process_image(image_path, assignment_data)
                self.logger.info("OCR processing complete")
                if not ocr_result or 'student_response' not in ocr_result:
                    raise ValueError("OCR processing failed to extract student response")
            except Exception as ocr_error:
                self.logger.error(f"OCR processing failed: {str(ocr_error)}")
                raise ValueError(f"OCR processing failed: {str(ocr_error)}")
                
            # Update submission with OCR text
            updates = {
                'status': 'processing',
                'ocr_text': ocr_result['student_response']  # Extract student's response
            }
            self.storage_service.update_submission(submission_id, updates)
            
            # Get updated submission
            submission.ocr_text = ocr_result['student_response']
            assignment = Assignment.from_dict(assignment_data)
            
            # 4. Grade submission
            self.logger.info("Starting grading...")
            if on_stage_change:
                on_stage_change("GRADING", "Grading submission...")
            
            grading_result = self.grading_service.grade_submission(
                submission,
                assignment
            )
            self.logger.info("Grading complete")
            
            # 5. Generate feedback
            self.logger.info("Starting feedback generation...")
            if on_stage_change:
                on_stage_change("FEEDBACK", "Generating feedback...")
            
            feedback = self.feedback_service.generate_feedback(
                grading_result,
                assignment,
                student_response=ocr_result['student_response']
            )
            self.logger.info("Feedback generation complete")
            
            # 6. Update submission with results
            updates = {
                'status': 'complete',
                'ocr_text': ocr_result['student_response'],
                'feedback_md': feedback,
                'score': grading_result.model_dump()
            }
            
            self.storage_service.update_submission(submission_id, updates)
            
            if on_stage_change:
                on_stage_change("COMPLETE", "Processing complete")
            
            return {
                'submission_id': submission_id,
                'status': 'complete',
                'feedback': feedback,
                'score': grading_result.model_dump()
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline processing failed: {str(e)}")
            
            if 'submission_id' in locals():
                self.storage_service.update_submission(
                    submission_id,
                    {
                        'status': 'error',
                        'error_message': str(e)
                    }
                )
            
            return None
