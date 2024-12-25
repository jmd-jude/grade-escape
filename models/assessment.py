# models/assessment.py
from typing import Dict, List, Optional
from pydantic import BaseModel

class AssessmentCriteria(BaseModel):
    """Standard assessment categories that work across subjects"""
    concept_understanding: bool = False  # Does student understand core concept
    application: bool = False           # Can they apply it
    technical_accuracy: bool = False    # Are technical details correct
    clarity: bool = False              # Clear communication
    reasoning: bool = False            # Shows logical reasoning
    points_awarded: int = 0
    feedback: Optional[str] = None

class GPTEvaluation(BaseModel):
    """GPT's evaluation response structure"""
    student_response: str
    rubric_points: Dict[str, bool]     # Point-by-point evaluation
    points_earned: List[str]           # Specific points demonstrated
    misconceptions: List[str]          # Errors or misunderstandings
    explanation: str                   # Detailed feedback

class RubricMapping(BaseModel):
    """Maps teacher's rubric points to standard assessment criteria"""
    rubric_point: str                  # Original rubric text
    criteria_category: str             # Which standard criteria it maps to
    weight: float                      # How much this point is worth
    required: bool = False             # Is this required for full credit

class AssessmentResult(BaseModel):
    """Final assessment combining GPT eval with rubric"""
    raw_score: float
    weighted_score: float
    teacher_score: str                 # e.g., "8/10"
    rubric_points_evaluation: Dict[str, bool]  # Point-by-point evaluation results
    rubric_points_earned: List[str]    # List of points demonstrated
    misconceptions: List[str]          # List of misconceptions
    feedback: str                      # Detailed feedback
    confidence: float                  # Confidence in assessment
