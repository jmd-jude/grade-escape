# services/grading.py
import json
import logging
from openai import OpenAI
from models.assessment import GPTEvaluation, AssessmentResult
from models.submission import Submission
from models.assignment import Assignment
from config.settings import get_settings

class GradingService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.logger = logging.getLogger(__name__)

    def grade_submission(self, submission: Submission, assignment: Assignment) -> AssessmentResult:
        """Grade a submission using standardized criteria"""
        try:
            if not submission.ocr_text:
                raise ValueError("Submission text not available")
                
            # Store current submission text for _parse_response
            self.current_submission_text = submission.ocr_text

            # Get rubric requirements
            requirements = [req.text for req in assignment.rubric_structure.requirements]
            
            # Prepare evaluation prompt
            prompt = f"""
            Question: {assignment.question_text}
            
            Student Response: {submission.ocr_text}

            Evaluate this response against each of these specific rubric points:
            {json.dumps(requirements, indent=2)}

            Return a JSON evaluation with:
            {{
                "rubric_points": {{
                    # For each rubric point, indicate if it was demonstrated
                    point_text: true/false
                }},
                "points_earned": ["list of specific points that were demonstrated"],
                "misconceptions": ["list any misconceptions or errors"],
                "explanation": "detailed feedback explaining the evaluation"
            }}
            """

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            # Parse GPT's evaluation
            gpt_eval = GPTEvaluation(**self._parse_response(response))

            # Map GPT's evaluation to rubric points
            result = self._map_to_rubric(gpt_eval, assignment)

            return result

        except Exception as e:
            self.logger.error(f"Grading failed: {str(e)}")
            raise

    def _parse_response(self, response) -> dict:
        """Parse and validate GPT's response"""
        content = response.choices[0].message.content
        content = content.replace('```json\n', '').replace('\n```', '').strip()
        gpt_response = json.loads(content)
        # Add student_response from the original prompt context
        gpt_response['student_response'] = self.current_submission_text
        return gpt_response

    def _map_to_rubric(self, eval: GPTEvaluation, assignment: Assignment) -> AssessmentResult:
        """Map evaluation to rubric points and calculate score"""
        # Count earned points
        earned_points = sum(1 for point, earned in eval.rubric_points.items() if earned)
        max_points = len(assignment.rubric_structure.requirements)
        
        # Calculate scores
        weighted_score = earned_points / max_points if max_points > 0 else 0
        
        return AssessmentResult(
            raw_score=weighted_score,
            weighted_score=weighted_score,
            teacher_score=f"{earned_points}/{max_points}",
            rubric_points_evaluation=eval.rubric_points,  # Store point-by-point evaluation
            rubric_points_earned=eval.points_earned,
            misconceptions=eval.misconceptions,
            feedback=eval.explanation,
            confidence=0.95
        )

    def _calculate_weighted_score(self, eval: GPTEvaluation, assignment: Assignment) -> float:
        """Calculate final score considering rubric weights"""
        # This would implement your specific scoring logic
        # For MVP, we could use a simple average
        return eval.score
