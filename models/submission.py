# models/submission.py
from typing import Dict, List, Optional
from pydantic import BaseModel, UUID4, Field
from datetime import datetime
import uuid

class RubricResult(BaseModel):
    """Represents the evaluation of a single rubric point"""
    value: bool
    explanation: Optional[str] = None

class SubmissionAnalysis(BaseModel):
    """Represents the AI analysis of a student submission"""
    student_response: str
    teacher_score: str
    rubric_points: Dict[str, bool]
    misconceptions: List[str]
    points_earned: List[str]

class Submission(BaseModel):
    """Main submission model"""
    id: UUID4 = Field(default_factory=uuid.uuid4)
    assignment_id: UUID4
    student_id: str
    status: str = "pending"
    image_path: str
    ocr_text: Optional[str] = None
    feedback_md: Optional[str] = None
    score: Optional[Dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    async def create_from_image(cls, assignment_id: str, student_id: str, 
                            image_path: str) -> "Submission":
        """Create new submission from uploaded image"""
        try:
            assignment_uuid = uuid.UUID(assignment_id)
        except ValueError:
            assignment_uuid = uuid.uuid4()  # Generate a new UUID for testing
                
        return cls(
            assignment_id=assignment_uuid,
            student_id=student_id,  # Just use the string directly
            image_path=image_path,
            status="pending"
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "id": str(self.id),
            "assignment_id": str(self.assignment_id),
            "student_id": str(self.student_id),
            "status": self.status,
            "image_path": self.image_path,
            "ocr_text": self.ocr_text,
            "feedback_md": self.feedback_md,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "retry_count": self.retry_count,
            "error_message": self.error_message
        }
