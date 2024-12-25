# models/assignment.py
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class RubricRequirement(BaseModel):
    """Single requirement in a rubric"""
    text: str
    points: int

class RubricMetadata(BaseModel):
    """Metadata for future rubric enhancements"""
    notes: str = ""
    examples: List[str] = Field(default_factory=list)
    version: int = 1

class RubricStructure(BaseModel):
    """Complete rubric structure"""
    requirements: List[RubricRequirement] = Field(default_factory=list)
    metadata: RubricMetadata = Field(default_factory=RubricMetadata)

class Assignment(BaseModel):
    """Assignment model"""
    id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    name: str
    question_text: str
    points_possible: int
    rubric_structure: RubricStructure = Field(default_factory=RubricStructure)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            "name": self.name,
            "question_text": self.question_text,
            "points_possible": self.points_possible,
            "rubric_structure": self.rubric_structure.dict(),
            "teacher_id": str(self.teacher_id) if self.teacher_id else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Assignment":
        """Create from database dictionary"""
        if "rubric_structure" in data and isinstance(data["rubric_structure"], str):
            # Handle JSON string from database
            import json
            data["rubric_structure"] = json.loads(data["rubric_structure"])
        return cls(**data)
