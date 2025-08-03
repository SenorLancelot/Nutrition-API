import os
import logging
import time
from typing import Dict, Any, Optional
from django.conf import settings
from ..models import Food, NutritionProfile, NutritionSource
from .llm_service import llm_service
import google.generativeai as genai
from PIL import Image
import io

logger = logging.getLogger('food_scanner')


class FoodIdentificationService:
    """Service for identifying food from images using Gemini 1.5 Flash"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.warning("Gemini API key not configured. Food identification will use fallback method.")
            self.model = None
    
    def identify_food_from_image(self, image_data: bytes, additional_context: str = "") -> Dict[str, Any]:
        """
        Identify food from image using LLM service
        
        Args:
            image_data: Raw image bytes
            additional_context: Additional context or user preferences
            
        Returns:
            Dict containing food identification results
        """
        start_time = time.time()
        
        try:
            # Use LLM service for food identification
            result = llm_service.identify_food_from_image(image_data, additional_context)
            
            # Try to find existing food in database
            existing_food = self._find_existing_food(result.get('food_name', ''))
            if existing_food:
                result['food_id'] = existing_food.id
                result['database_match'] = True
            else:
                result['database_match'] = False
            
            # Add processing metadata
            result['processing_time_ms'] = int((time.time() - start_time) * 1000)
            result['data_source'] = 'LLM Analysis'
            result['timestamp'] = time.time()
            
            logger.info(f"Food identified: {result.get('food_name')} (confidence: {result.get('confidence', 0)})")
            return result
            
        except Exception as e:
            logger.error(f"Food identification failed: {str(e)}")
            return self._create_error_response(str(e), time.time() - start_time)
    
    def _find_existing_food(self, food_name: str) -> Optional[Food]:
        try:
            return Food.objects.get(name=food_name)
        except Food.DoesNotExist:
            return None
    
    def _create_error_response(self, error_message: str, processing_time: float) -> Dict[str, Any]:
        return {
            'error': error_message,
            'processing_time_ms': int(processing_time * 1000),
            'data_source': 'LLM Analysis',
            'timestamp': time.time()
        }
    
    def identify_from_image(self, image_file):
        """
        Identify food from an uploaded image
        
        Args:
            image_file: Django UploadedFile object
            
        Returns:
            dict: {
                'food_name': str,
                'confidence_score': float,
                'suggested_foods': list,
            }
        """
        try:
            # Convert uploaded file to PIL Image
            image = Image.open(image_file)
            
            if self.model and self.api_key:
                return self._identify_with_gemini(image)
            else:
                return self._identify_fallback(image)
                
        except Exception as e:
            logger.error(f"Error in food identification: {str(e)}")
            return {
                'food_name': 'Unknown Food',
                'confidence_score': 0.0,
                'suggested_foods': []
            }
    
    def _identify_with_gemini(self, image):
        """Use Gemini 1.5 Flash for food identification"""
        try:
            prompt = """
            Analyze this food image and identify the main food item. Provide:
            1. The most likely food name (be specific, e.g., "grilled chicken breast" not just "chicken")
            2. Your confidence level (0-1)
            3. Up to 3 alternative suggestions if confidence is low
            
            Respond in JSON format:
            {
                "food_name": "specific food name",
                "confidence_score": 0.95,
                "suggested_foods": [
                    {"name": "alternative 1", "confidence": 0.8},
                    {"name": "alternative 2", "confidence": 0.7}
                ]
            }
            
            Focus on identifying prepared foods, ingredients, and packaged items accurately.
            """
            
            response = self.model.generate_content([prompt, image])
            
            # Parse the JSON response
            import json
            try:
                # Extract JSON from markdown code blocks if present
                json_text = self._extract_json_from_response(response.text)
                result = json.loads(json_text)
                
                # Clean up the food_name if it contains nested JSON
                food_name = result.get('food_name', 'Unknown Food')
                food_name = self._clean_food_name(food_name)
                
                return {
                    'food_name': food_name,
                    'confidence_score': float(result.get('confidence_score', 0.0)),
                    'suggested_foods': result.get('suggested_foods', [])
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return self._parse_text_response(response.text)
                
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return self._identify_fallback(image)
    
    def _clean_food_name(self, food_name: str) -> str:
        """
        Clean up malformed food names that contain nested JSON structure
        
        Args:
            food_name: Raw food name from LLM response
            
        Returns:
            Clean food name string
        """
        if not food_name or food_name == 'Unknown Food':
            return 'Unknown Food'
        
        # Handle cases like '"Food_Name": "French Fries",' 
        if ':' in food_name and '"' in food_name:
            # Extract the value after the colon
            parts = food_name.split(':')
            if len(parts) > 1:
                # Get the part after colon, remove quotes and commas
                clean_name = parts[1].strip().strip('"\',').strip()
                if clean_name:
                    return clean_name
        
        # Remove any JSON-like artifacts
        clean_name = food_name.strip('"\',{}[]').strip()
        
        # If still malformed, try to extract from common patterns
        if '"' in clean_name:
            # Find text between quotes
            import re
            matches = re.findall(r'"([^"]+)"', clean_name)
            if matches:
                return matches[-1]  # Take the last match
        
        return clean_name if clean_name else 'Unknown Food'
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """
        Extract JSON content from LLM response, handling markdown code blocks
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            Clean JSON string ready for parsing
        """
        text = response_text.strip()
        
        # Check if response is wrapped in markdown code blocks
        if text.startswith('```json') and text.endswith('```'):
            # Extract content between ```json and ```
            lines = text.split('\n')
            # Remove first line (```json) and last line (```)
            json_lines = lines[1:-1]
            return '\n'.join(json_lines)
        elif text.startswith('```') and text.endswith('```'):
            # Generic code block
            lines = text.split('\n')
            json_lines = lines[1:-1]
            return '\n'.join(json_lines)
        else:
            # No code blocks, return as is
            return text
    
    def _parse_text_response(self, text):
        """Parse non-JSON text response from Gemini"""
        # Simple text parsing fallback
        lines = text.strip().split('\n')
        food_name = 'Unknown Food'
        confidence = 0.5
        
        for line in lines:
            line = line.strip().lower()
            if 'food' in line or 'dish' in line or 'item' in line:
                # Extract potential food name
                words = line.split()
                if len(words) > 2:
                    food_name = ' '.join(words[-3:]).title()
                    confidence = 0.7
                break
        
        return {
            'food_name': food_name,
            'confidence_score': confidence,
            'suggested_foods': []
        }
    
    def _identify_fallback(self, image):
        """Fallback method when Gemini is not available"""
        # Simple fallback - could be enhanced with local ML models
        # For now, return a generic response
        logger.info("Using fallback food identification method")
        
        return {
            'food_name': 'Unidentified Food Item',
            'confidence_score': 0.3,
            'suggested_foods': [
                {'name': 'Mixed Food', 'confidence': 0.2},
                {'name': 'Prepared Meal', 'confidence': 0.2}
            ]
        }
    
    def validate_image(self, image_file):
        """Validate uploaded image file"""
        try:
            # Check file size
            if image_file.size > settings.MAX_IMAGE_SIZE:
                return False, "Image file too large"
            
            # Check file extension
            import os
            ext = os.path.splitext(image_file.name)[1].lower()
            if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
                return False, "Invalid image format"
            
            # Try to open as image
            Image.open(image_file)
            image_file.seek(0)  # Reset file pointer
            
            return True, "Valid image"
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
