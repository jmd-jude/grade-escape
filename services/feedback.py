# services/feedback.py
from typing import Dict, Optional
import json
import logging
from openai import OpenAI
from models.assessment import AssessmentResult
from models.assignment import Assignment
from config.settings import get_settings

class FeedbackService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.logger = logging.getLogger(__name__)

    def generate_feedback(self,
                         assessment: AssessmentResult,
                         assignment: Assignment,
                         student_response: str = None) -> str:
        """
        Generate personalized feedback based on submission analysis
        """
        try:
            prompt = f"""CONTEXT
Question: {assignment.question_text}
Rubric: {json.dumps(assignment.rubric_structure.model_dump(), indent=2)}

Student Response: {student_response}

INSTRUCTIONS
1. Identify which rubric points student addressed/missed using the provided assessment:
{json.dumps(assessment.rubric_points_evaluation, indent=2)}

2. Generate ~50 word feedback that:
   - Acknowledges correct understanding of rubric points
   - Targets 1-2 key missing concepts
   - Links to fundamental principles
   - Uses direct, personal language ("You explain...")
   - Maintains precise biochemical terminology

STYLE GUIDANCE
- Direct, conversational academic tone
- Focus on understanding gaps
- No study suggestions
- Connect pathways to principles

Example feedback style:
"You explain the role of fermentation in regenerating NAD⁺ and oxygen's role in the electron transport chain well. To improve, clarify pyruvate's role during fermentation, specifically how it is reduced rather than oxidizing. Strengthening this detail will enhance your understanding of redox processes."

OUTPUT FORMAT
- Feedback text only"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )

            feedback = response.choices[0].message.content.strip()
            return feedback

        except Exception as e:
            self.logger.error(f"Feedback generation failed: {str(e)}")
            raise

    def validate_feedback(self,
                         feedback: str,
                         assessment: AssessmentResult,
                         assignment: Assignment) -> Dict:
        """
        Validate generated feedback against quality criteria
        """
        try:
            prompt = f"""CONTEXT
Generated Feedback: {feedback}

Assessment Results:
{json.dumps(assessment.model_dump(), indent=2)}

Assignment Requirements:
{json.dumps(assignment.model_dump(), indent=2)}

Evaluate the feedback against these criteria (Y/N):
1. Is it scientifically accurate?
2. Does it address key rubric points?
3. Is it constructive and actionable?
4. Is the tone appropriate?
5. Is it clear and concise?
6. Does it maintain academic rigor?

Return only a JSON object:
{{
    "criteria_met": ["list of passed criteria numbers"],
    "issues": ["list of any problems found"],
    "score": 0-100
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=500
            )

            validation = response.choices[0].message.content
            return json.loads(validation)  # Convert string to dict safely

        except Exception as e:
            self.logger.error(f"Feedback validation failed: {str(e)}")
            return {
                "criteria_met": [],
                "issues": [str(e)],
                "score": 0
            }
