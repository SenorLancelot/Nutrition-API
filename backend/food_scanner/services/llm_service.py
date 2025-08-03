"""
Simple LLM Service for Food Scanner

Primary provider: Google Gemini Flash (free tier)
Designed for food identification, nutrition analysis, and health recommendations.
Extensible for future providers while keeping current implementation simple.
"""

import os
import logging
import base64
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger('food_scanner')


class LLMService:
    """Simple LLM service primarily using Gemini Flash"""
    
    def __init__(self):
        self.provider = None
        self.model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini Flash provider"""
        api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        
        if not api_key:
            logger.warning("GEMINI_API_KEY not found in settings or environment variables")
            return
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Use Gemini Flash for cost-effectiveness
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
            self.model = genai.GenerativeModel(model_name)
            self.provider = 'gemini'
            
            logger.info(f"Gemini LLM service initialized with model: {model_name}")
            
        except ImportError:
            logger.error("google-generativeai package not installed. Run: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.model is not None
    
    def identify_food_from_image(self, image_data: bytes, additional_context: str = "") -> Dict[str, Any]:
        """
        Identify food from image using LLM vision capabilities
        
        Args:
            image_data: Raw image bytes
            additional_context: Additional context or constraints
            
        Returns:
            Dict with food identification results
        """
        if not self.is_available():
            raise Exception("LLM service not available. Please configure GEMINI_API_KEY.")
        
        prompt = f"""
        Analyze this food image and provide a JSON response with the following information:
        
        {{
            "food_name": "Primary food item name",
            "category": "Food category (e.g., fruit, vegetable, protein, grain, dairy, snack)",
            "confidence": 0.95,
            "description": "Brief description of what you see",
            "ingredients": ["list", "of", "likely", "ingredients"],
            "preparation_method": "cooking/preparation method if visible",
            "serving_size_estimate": "estimated serving size (e.g., 1 medium apple, 100g)"
        }}
        
        Additional context: {additional_context}
        
        Be accurate and conservative with confidence scores. If uncertain, indicate lower confidence.
        Focus on the main food item if multiple items are present.
        """
        
        try:
            # Convert image data to PIL Image for Gemini
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data))
            
            response = self.model.generate_content([prompt, image])
            
            # Parse JSON response
            import json
            result = json.loads(response.text.strip())
            
            # Validate and set defaults
            result.setdefault('confidence', 0.8)
            result.setdefault('category', 'unknown')
            result.setdefault('ingredients', [])
            
            return result
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            logger.warning(f"LLM response was not valid JSON: {response.text[:200]}...")
            return self._parse_fallback_response(response.text)
        except Exception as e:
            logger.error(f"Food identification error: {str(e)}")
            raise Exception(f"Failed to identify food: {str(e)}")
    
    def _parse_fallback_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response when JSON parsing fails
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            Dict with parsed food identification results
        """
        # Try to extract food name from response text
        food_name = "Unknown Food"
        confidence = 0.5
        
        # Simple text parsing to extract food name
        lines = response_text.lower().split('\n')
        for line in lines:
            if 'food' in line and ('name' in line or ':' in line):
                # Try to extract food name from patterns like "food_name: apple" or "Food: apple"
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        potential_name = parts[1].strip().strip('"\'')
                        if potential_name and len(potential_name) < 50:
                            food_name = potential_name.title()
                            confidence = 0.7
                            break
        
        # If still unknown, try to find any food-related words
        if food_name == "Unknown Food":
            common_foods = ['apple', 'banana', 'bread', 'chicken', 'rice', 'pasta', 'pizza', 'burger', 'fries', 'salad']
            for food in common_foods:
                if food in response_text.lower():
                    food_name = food.title()
                    confidence = 0.6
                    break
        
        return {
            'food_name': food_name,
            'confidence': confidence,
            'category': 'unknown',
            'description': f"Parsed from response: {response_text[:100]}...",
            'ingredients': [],
            'preparation_method': 'unknown',
            'serving_size_estimate': '100g'
        }
    
    def extract_nutrition_from_label(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract nutrition information from food label image
        
        Args:
            image_data: Raw image bytes of nutrition label
            
        Returns:
            Dict with nutrition facts
        """
        if not self.is_available():
            raise Exception("LLM service not available. Please configure GEMINI_API_KEY.")
        
        prompt = """
        Extract nutrition information from this food label image and provide a JSON response:
        
        {
            "serving_size": "serving size from label",
            "calories": 0,
            "protein_g": 0.0,
            "carbohydrates_g": 0.0,
            "fat_g": 0.0,
            "fiber_g": 0.0,
            "sugar_g": 0.0,
            "sodium_mg": 0.0,
            "ingredients": ["list", "of", "ingredients"],
            "allergens": ["list", "of", "allergens"],
            "brand": "brand name if visible",
            "product_name": "product name if visible"
        }
        
        Extract exact values from the nutrition facts panel. Use 0 for missing values.
        Be precise with numbers and units.
        """
        
        try:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_data))
            
            response = self.model.generate_content([prompt, image])
            
            import json
            result = json.loads(response.text.strip())
            
            # Ensure numeric values
            numeric_fields = ['calories', 'protein_g', 'carbohydrates_g', 'fat_g', 'fiber_g', 'sugar_g', 'sodium_mg']
            for field in numeric_fields:
                if field in result:
                    try:
                        result[field] = float(result[field])
                    except (ValueError, TypeError):
                        result[field] = 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"Nutrition label extraction error: {str(e)}")
            raise Exception(f"Failed to extract nutrition info: {str(e)}")
    
    def generate_health_recommendations(self, nutrition_data: Dict[str, Any], health_conditions: list) -> Dict[str, Any]:
        """
        Generate personalized health recommendations based on nutrition data and health conditions
        
        Args:
            nutrition_data: Nutrition information
            health_conditions: List of health condition names
            
        Returns:
            Dict with health analysis and recommendations
        """
        if not self.is_available():
            raise Exception("LLM service not available. Please configure GEMINI_API_KEY.")
        
        conditions_text = ", ".join(health_conditions) if health_conditions else "none specified"
        
        prompt = f"""
        Analyze this nutrition data for someone with the following health conditions: {conditions_text}
        
        Nutrition Data:
        - Calories: {nutrition_data.get('calories', 0)}
        - Protein: {nutrition_data.get('protein_g', 0)}g
        - Carbohydrates: {nutrition_data.get('carbohydrates_g', 0)}g
        - Fat: {nutrition_data.get('fat_g', 0)}g
        - Fiber: {nutrition_data.get('fiber_g', 0)}g
        - Sugar: {nutrition_data.get('sugar_g', 0)}g
        - Sodium: {nutrition_data.get('sodium_mg', 0)}mg
        
        Provide a JSON response with health analysis:
        
        {{
            "overall_health_score": 7.5,
            "health_remarks": [
                {{
                    "condition": "condition name or general",
                    "severity": "info|warning|danger",
                    "message": "specific health remark",
                    "recommendation": "actionable recommendation"
                }}
            ],
            "nutri_score": "B",
            "glycemic_load_index": 5.2,
            "key_nutrients": ["highlight", "important", "nutrients"],
            "concerns": ["list", "of", "concerns"],
            "benefits": ["list", "of", "benefits"]
        }}
        
        Health score should be 1-10 (10 being healthiest).
        Nutri-Score should be A-E (A being healthiest).
        Be specific about health condition interactions.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            import json
            result = json.loads(response.text.strip())
            
            # Validate and set defaults
            result.setdefault('overall_health_score', 5.0)
            result.setdefault('health_remarks', [])
            result.setdefault('nutri_score', 'C')
            result.setdefault('glycemic_load_index', 0.0)
            
            return result
            
        except Exception as e:
            logger.error(f"Health recommendation error: {str(e)}")
            raise Exception(f"Failed to generate health recommendations: {str(e)}")
    
    def estimate_nutrition(self, food_name: str, serving_size: str = "100g") -> Dict[str, Any]:
        """
        Estimate nutrition information for a food item by name
        
        Args:
            food_name: Name of the food item
            serving_size: Serving size for estimation
            
        Returns:
            Dict with estimated nutrition data
        """
        if not self.is_available():
            raise Exception("LLM service not available. Please configure GEMINI_API_KEY.")
        
        prompt = f"""
        Provide estimated nutrition information for "{food_name}" per {serving_size}.
        
        Return a JSON response with nutritional estimates:
        
        {{
            "food_name": "{food_name}",
            "serving_size": "{serving_size}",
            "calories": 0,
            "protein_g": 0.0,
            "carbohydrates_g": 0.0,
            "fat_g": 0.0,
            "fiber_g": 0.0,
            "sugar_g": 0.0,
            "sodium_mg": 0.0,
            "confidence": 0.8,
            "data_source": "AI Estimated",
            "notes": "any important notes about the food"
        }}
        
        Use standard nutritional databases as reference. Be conservative with estimates.
        Indicate confidence level (0.0-1.0) based on how common/well-known the food is.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from markdown code blocks if present (same as generate_nutrition_data)
            response_text = response.text.strip()
            if response_text.startswith('```json') and response_text.endswith('```'):
                lines = response_text.split('\n')
                json_lines = lines[1:-1]
                response_text = '\n'.join(json_lines)
            elif response_text.startswith('```') and response_text.endswith('```'):
                lines = response_text.split('\n')
                json_lines = lines[1:-1]
                response_text = '\n'.join(json_lines)
            
            import json
            result = json.loads(response_text)
            
            # Ensure numeric values
            numeric_fields = ['calories', 'protein_g', 'carbohydrates_g', 'fat_g', 'fiber_g', 'sugar_g', 'sodium_mg', 'confidence']
            for field in numeric_fields:
                if field in result:
                    try:
                        result[field] = float(result[field])
                    except (ValueError, TypeError):
                        result[field] = 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"Nutrition estimation error: {str(e)}")
            raise Exception(f"Failed to estimate nutrition: {str(e)}")
    
    def generate_nutrition_data(self, prompt: str) -> Dict[str, Any]:
        """
        Generate nutrition data using custom prompt (used by nutrition analyzer)
        
        Args:
            prompt: Custom prompt for nutrition data generation
            
        Returns:
            Dict with nutrition data or error info
        """
        if not self.is_available():
            return {'error': 'LLM service not available. Please configure GEMINI_API_KEY.'}
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from markdown code blocks if present
            response_text = response.text.strip()
            if response_text.startswith('```json') and response_text.endswith('```'):
                lines = response_text.split('\n')
                json_lines = lines[1:-1]
                response_text = '\n'.join(json_lines)
            elif response_text.startswith('```') and response_text.endswith('```'):
                lines = response_text.split('\n')
                json_lines = lines[1:-1]
                response_text = '\n'.join(json_lines)
            
            import json
            result = json.loads(response_text)
            
            # Ensure numeric values for nutrition fields
            numeric_fields = [
                'calories', 'protein_g', 'carbohydrates_g', 'fat_g', 'fiber_g', 
                'sugar_g', 'sodium_mg', 'potassium_mg', 'vitamin_c_mg', 
                'calcium_mg', 'iron_mg', 'glycemic_index'
            ]
            
            for field in numeric_fields:
                if field in result:
                    try:
                        result[field] = float(result[field])
                    except (ValueError, TypeError):
                        result[field] = 0.0
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in generate_nutrition_data: {str(e)}")
            return {'error': f'Failed to parse LLM response as JSON: {str(e)}'}
        except Exception as e:
            logger.error(f"Nutrition data generation error: {str(e)}")
            return {'error': f'Failed to generate nutrition data: {str(e)}'}
    
    def _parse_fallback_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback parser for non-JSON responses"""
        return {
            "food_name": "Unknown",
            "category": "unknown",
            "confidence": 0.5,
            "description": response_text[:200] + "..." if len(response_text) > 200 else response_text,
            "ingredients": [],
            "preparation_method": "unknown",
            "serving_size_estimate": "unknown"
        }


# Global LLM service instance
llm_service = LLMService()
