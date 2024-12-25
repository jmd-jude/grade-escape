# services/ocr_service.py
import logging
import json
import base64
from openai import OpenAI
from config.settings import get_settings

class OCRService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.logger = logging.getLogger(__name__)
    
    def process_image(self, image_path: str, assignment_data: dict) -> dict:
        """Process image using GPT-4o"""
        try:
            # Read and encode image
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Get rubric requirements from assignment data
            rubric_structure = json.loads(assignment_data.get('rubric_structure', '{}'))
            requirements = [req['text'] for req in rubric_structure.get('requirements', [])]
            
            # Create prompt matching production format
            prompt = f"""
Question: {assignment_data.get('question_text', '')}

First, accurately transcribe the handwritten response from the image.
Then evaluate this response against each of these specific rubric points:
{json.dumps(requirements, indent=2)}

Return a JSON evaluation with:
{{
    "student_response": "The transcribed text from the image",
    "rubric_points": {{
        # For each rubric point, indicate if it was demonstrated
        "point_text": true/false
    }},
    "points_earned": ["list of specific points that were demonstrated"],
    "misconceptions": ["list any misconceptions or errors"],
    "explanation": "detailed feedback explaining the evaluation"
}}

IMPORTANT:
1. Include the full transcribed text in student_response
2. For unclear text in transcription, include [unclear]
3. Return ONLY valid JSON with proper commas
4. Evaluate against EACH rubric point"""
            
            # Make request with JSON mode
            response = self.client.chat.completions.create(
                model="gpt-4o",
                response_format={ "type": "json_object" },
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            self.logger.info("Successfully processed image")
            return result
            
        except Exception as e:
            self.logger.error(f"Image processing failed: {str(e)}")
            # Return error JSON in same format
            return {
                "student_response": "[OCR Error: Processing failed]",
                "teacher_score": f"0/{assignment_data['points_possible']}",
                "rubric_points": {},
                "misconceptions": ["OCR processing failed"],
                "points_earned": []
            }
