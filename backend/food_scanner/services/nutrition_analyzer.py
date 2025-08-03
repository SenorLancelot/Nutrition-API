import logging
import os
import requests
import time
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from ..models import Food, NutritionProfile, NutritionSource
from .llm_service import llm_service

logger = logging.getLogger('food_scanner')


class NutritionAnalyzerService:
    """Service for analyzing nutrition data from various sources"""
    
    def __init__(self):
        pass
    
    def get_food_by_name(self, food_name, use_llm_fallback=True):
        """
        Find food by name in local database with LLM fallback
        
        Args:
            food_name: String name of the food
            use_llm_fallback: Whether to use LLM if not found in database
            
        Returns:
            dict: Food information with nutrition data
        """
        try:
            # Step 1: Try to find in database first
            food = self._find_food_in_database(food_name)
            
            if food:
                logger.info(f"Found {food_name} in database (ID: {food.id})")
                return self._format_database_food_response(food)
            
            # Step 2: If not found and LLM fallback enabled, query LLM
            if use_llm_fallback:
                logger.info(f"Food '{food_name}' not in database, querying LLM...")
                llm_result = self._get_nutrition_from_llm(food_name)
                
                if llm_result and llm_result.get('success'):
                    # Step 3: Save LLM result to database for future use
                    saved_food = self._save_llm_food_to_database(food_name, llm_result)
                    
                    if saved_food:
                        logger.info(f"Saved new food '{food_name}' to database from LLM")
                        return self._format_database_food_response(saved_food, source='LLM')
                    else:
                        # Return LLM data even if save failed
                        return self._format_llm_response(food_name, llm_result)
                
            # Step 4: Fallback - not found anywhere
            logger.warning(f"Food '{food_name}' not found in database or LLM")
            return {
                'found': False,
                'food_name': food_name,
                'source': 'Not Found'
            }
            
        except Exception as e:
            logger.error(f"Error finding food by name: {str(e)}")
            return {'found': False, 'food_name': food_name, 'error': str(e)}
    
    def _find_food_in_database(self, food_name: str) -> Optional[Food]:
        """
        Search for food in database using multiple matching strategies
        
        Args:
            food_name: Name of food to search for
            
        Returns:
            Food object if found, None otherwise
        """
        # Try exact match first
        food = Food.objects.filter(name__iexact=food_name).first()
        
        if not food:
            # Try partial match
            food = Food.objects.filter(name__icontains=food_name).first()
        
        if not food:
            # Try fuzzy matching with common variations
            variations = self._generate_name_variations(food_name)
            for variation in variations:
                food = Food.objects.filter(
                    Q(name__icontains=variation) | 
                    Q(description__icontains=variation)
                ).first()
                if food:
                    break
        
        return food
    
    def _get_nutrition_from_llm(self, food_name: str) -> Dict[str, Any]:
        """
        Query LLM for nutrition information about a food
        
        Args:
            food_name: Name of food to get nutrition for
            
        Returns:
            Dict with nutrition data or error info
        """
        try:
            prompt = f"""
            Provide detailed nutrition information for "{food_name}" per 100g serving.
            
            Return JSON with this exact structure (use realistic values, 0 if unknown):
            {{
                "food_name": "{food_name}",
                "serving_size": "100g",
                "calories": <number>,
                "protein_g": <number>,
                "carbohydrates_g": <number>,
                "fat_g": <number>,
                "fiber_g": <number>,
                "sugar_g": <number>,
                "sodium_mg": <number>,
                "cholesterol_mg": <number>,
                "saturated_fat_g": <number>,
                "potassium_mg": <number>,
                "vitamin_c_mg": <number>,
                "calcium_mg": <number>,
                "iron_mg": <number>,
                "vitamin_a_iu": <number>,
                "nutri_score": "<A|B|C|D|E>",
                "glycemic_index": <number 0-100>,
                "category": "<food category>",
                "food_type": "<fresh|packaged|processed>",
                "allergens": ["<allergen1>", "<allergen2>"],
                "description": "<brief description>",
                "confidence": <0.1-1.0>
            }}
            
            IMPORTANT: Use only numeric values (no strings like 'trace' or 'unknown'). If a nutrient is unknown, use 0.
            """
            
            result = llm_service.generate_nutrition_data(prompt)
            
            if result and 'error' not in result:
                return {
                    'success': True,
                    'nutrition_data': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'LLM nutrition query failed')
                }
                
        except Exception as e:
            logger.error(f"LLM nutrition query failed for {food_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _save_llm_food_to_database(self, food_name: str, llm_result: Dict[str, Any]) -> Optional[Food]:
        """
        Save LLM nutrition data to database for future use
        
        Args:
            food_name: Name of the food
            llm_result: LLM nutrition data result
            
        Returns:
            Saved Food object or None if failed
        """
        try:
            nutrition_data = llm_result.get('nutrition_data', {})
            
            # Get or create NutritionSource for LLM FIRST
            llm_source, created = NutritionSource.objects.get_or_create(
                name='LLM Generated',
                defaults={
                    'source_type': 'ai_estimated',
                    'description': 'Nutrition data generated by AI/LLM',
                    'reliability_score': 0.8
                }
            )
            
            # Create Food object
            food = Food.objects.create(
                name=nutrition_data.get('food_name', food_name),
                description=nutrition_data.get('description', f'Auto-generated from LLM for {food_name}'),
                category=nutrition_data.get('category', 'Unknown'),
                food_type=nutrition_data.get('food_type', 'fresh'),  # Use valid choice
                is_verified=False  # LLM data is not verified
            )
            
            # Create NutritionProfile with robust data sanitization
            nutrition_profile = self._create_sanitized_nutrition_profile(
                food=food,
                source=llm_source,
                nutrition_data=nutrition_data
            )
            
            logger.info(f"Successfully saved LLM food data for '{food_name}' (ID: {food.id})")
            return food
            
        except Exception as e:
            logger.error(f"Failed to save LLM food data for '{food_name}': {str(e)}")
            return None
    
    def _create_sanitized_nutrition_profile(self, food: Food, source: NutritionSource, nutrition_data: Dict[str, Any]) -> NutritionProfile:
        """
        Create NutritionProfile with robust data sanitization
        
        Args:
            food: Food object to link to
            source: NutritionSource object
            nutrition_data: Raw nutrition data from LLM (may have extra/missing fields)
            
        Returns:
            Created NutritionProfile object
        """
        print(f"DEBUG: Sanitizing nutrition data for {food.name}")
        
        # Define valid direct fields for NutritionProfile model
        valid_direct_fields = {
            'serving_size': 'serving_size',
            'calories': 'calories',
            'protein_g': 'protein_g', 
            'carbohydrates_g': 'carbohydrates_g',
            'fat_g': 'fat_g',
            'fiber_g': 'fiber_g',
            'sugar_g': 'sugar_g',
            'sodium_mg': 'sodium_mg',
            'cholesterol_mg': 'cholesterol_mg',
            'saturated_fat_g': 'saturated_fat_g',
            'trans_fat_g': 'trans_fat_g'
        }
        
        # Fields that should go into vitamins_minerals JSON field
        vitamin_mineral_fields = {
            'potassium_mg': 'potassium_mg',
            'vitamin_c_mg': 'vitamin_c_mg',
            'calcium_mg': 'calcium_mg',
            'iron_mg': 'iron_mg',
            'vitamin_a_iu': 'vitamin_a_iu',
            'vitamin_d_iu': 'vitamin_d_iu',
            'vitamin_e_mg': 'vitamin_e_mg',
            'vitamin_k_mcg': 'vitamin_k_mcg',
            'folate_mcg': 'folate_mcg',
            'magnesium_mg': 'magnesium_mg',
            'phosphorus_mg': 'phosphorus_mg',
            'zinc_mg': 'zinc_mg'
        }
        
        # Special fields that go into source_metadata JSON field
        metadata_fields = {
            'nutri_score': 'nutri_score',
            'glycemic_index': 'glycemic_index',
            'glycemic_load': 'glycemic_load',
            'allergens': 'allergens',
            'food_type': 'food_type',
            'category': 'category'
        }
        
        # Sanitize direct fields
        sanitized_data = {
            'food': food,
            'source': source,
            'is_primary': True,
            'confidence_score': min(0.8, max(0.1, float(nutrition_data.get('confidence', 0.8)))),  # Clamp between 0.1-0.8
            'is_verified': False
        }
        
        # Add valid direct fields with type conversion and validation
        for llm_field, model_field in valid_direct_fields.items():
            if llm_field in nutrition_data:
                value = nutrition_data[llm_field]
                
                if model_field == 'serving_size':
                    # String field
                    sanitized_data[model_field] = str(value) if value else '100g'
                else:
                    # Numeric field - convert and validate
                    try:
                        numeric_value = float(value) if value is not None else 0.0
                        # Ensure non-negative
                        sanitized_data[model_field] = max(0.0, numeric_value)
                    except (ValueError, TypeError):
                        print(f"DEBUG: Invalid numeric value for {model_field}: {value}, using 0.0")
                        sanitized_data[model_field] = 0.0
            else:
                # Set defaults for missing required fields
                if model_field in ['calories', 'protein_g', 'carbohydrates_g', 'fat_g']:
                    sanitized_data[model_field] = 0.0
                elif model_field == 'serving_size':
                    sanitized_data[model_field] = '100g'
        
        # Build vitamins_minerals JSON field
        vitamins_minerals = {}
        for llm_field, json_key in vitamin_mineral_fields.items():
            if llm_field in nutrition_data:
                try:
                    value = float(nutrition_data[llm_field]) if nutrition_data[llm_field] is not None else 0.0
                    vitamins_minerals[json_key] = max(0.0, value)
                except (ValueError, TypeError):
                    print(f"DEBUG: Invalid vitamin/mineral value for {json_key}: {nutrition_data[llm_field]}")
                    vitamins_minerals[json_key] = 0.0
        
        sanitized_data['vitamins_minerals'] = vitamins_minerals
        
        # Build source_metadata JSON field
        source_metadata = {}
        for llm_field, meta_key in metadata_fields.items():
            if llm_field in nutrition_data:
                value = nutrition_data[llm_field]
                if meta_key == 'nutri_score':
                    # Validate Nutri-Score (A-E)
                    if isinstance(value, str) and value.upper() in ['A', 'B', 'C', 'D', 'E']:
                        source_metadata[meta_key] = value.upper()
                    else:
                        source_metadata[meta_key] = 'C'  # Default
                elif meta_key in ['glycemic_index', 'glycemic_load']:
                    # Numeric validation
                    try:
                        numeric_value = float(value) if value is not None else 50.0
                        source_metadata[meta_key] = max(0.0, min(100.0, numeric_value))  # Clamp 0-100
                    except (ValueError, TypeError):
                        source_metadata[meta_key] = 50.0
                else:
                    # String fields
                    source_metadata[meta_key] = str(value) if value else ''
        
        sanitized_data['source_metadata'] = source_metadata
        
        print(f"DEBUG: Sanitized data keys: {list(sanitized_data.keys())}")
        print(f"DEBUG: Vitamins/minerals: {list(vitamins_minerals.keys())}")
        print(f"DEBUG: Metadata: {list(source_metadata.keys())}")
        
        # Create the NutritionProfile with sanitized data
        try:
            nutrition_profile = NutritionProfile.objects.create(**sanitized_data)
            print(f"DEBUG: Successfully created NutritionProfile for {food.name}")
            return nutrition_profile
        except Exception as e:
            print(f"DEBUG: Error creating NutritionProfile: {str(e)}")
            print(f"DEBUG: Sanitized data that failed: {sanitized_data}")
            raise
    
    def _format_database_food_response(self, food: Food, source: str = 'Database') -> Dict[str, Any]:
        """
        Format food from database into standardized response
        
        Args:
            food: Food object from database
            source: Data source (Database, LLM, etc.)
            
        Returns:
            Formatted food response dict
        """
        return {
            'found': True,
            'food_id': food.id,
            'food_name': food.name,
            'food_type': food.food_type,
            'category': food.category,
            'brand': food.brand or '',
            'barcode_id': food.barcode,
            'description': food.description,
            'source': source
        }
    
    def _format_llm_response(self, food_name: str, llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format LLM result into standardized response when database save fails
        
        Args:
            food_name: Name of food
            llm_result: LLM nutrition result
            
        Returns:
            Formatted response dict
        """
        nutrition_data = llm_result.get('nutrition_data', {})
        return {
            'found': True,
            'food_id': None,  # No database ID
            'food_name': nutrition_data.get('food_name', food_name),
            'food_type': nutrition_data.get('food_type', 'unknown'),
            'category': nutrition_data.get('category', 'Unknown'),
            'brand': None,
            'barcode_id': None,
            'description': nutrition_data.get('description', ''),
            'allergens': ','.join(nutrition_data.get('allergens', [])),
            'source': 'LLM (Not Saved)',
            'nutrition_data': nutrition_data
        }
    
    def _format_llm_nutrition_data(self, nutrition_data: Dict[str, Any], serving_size: str) -> Dict[str, Any]:
        """
        Format LLM nutrition data into standardized nutrition response
        
        Args:
            nutrition_data: Raw nutrition data from LLM
            serving_size: Requested serving size
            
        Returns:
            Formatted nutrition data dict
        """
        print(f"DEBUG: Formatting LLM nutrition data: {nutrition_data}")
        
        # Convert to standard nutrition response format
        return {
            'calories': nutrition_data.get('calories', 0),
            'protein_g': nutrition_data.get('protein_g', 0),
            'carbohydrates_g': nutrition_data.get('carbohydrates_g', 0),
            'fat_g': nutrition_data.get('fat_g', 0),
            'fiber_g': nutrition_data.get('fiber_g', 0),
            'sugar_g': nutrition_data.get('sugar_g', 0),
            'sodium_mg': nutrition_data.get('sodium_mg', 0),
            'potassium_mg': nutrition_data.get('potassium_mg', 0),
            'vitamin_c_mg': nutrition_data.get('vitamin_c_mg', 0),
            'calcium_mg': nutrition_data.get('calcium_mg', 0),
            'iron_mg': nutrition_data.get('iron_mg', 0),
            'nutri_score': nutrition_data.get('nutri_score', 'C'),
            'glycemic_index': nutrition_data.get('glycemic_index', 50),
            'serving_size': nutrition_data.get('serving_size', serving_size),
            'data_source': 'LLM Generated',
            'confidence': 0.8,
            'food_name': nutrition_data.get('food_name', 'Unknown'),
            'category': nutrition_data.get('category', 'Unknown'),
            'description': nutrition_data.get('description', '')
        }
    
    def estimate_nutrition_by_name(self, food_name: str, serving_size: str = "100g") -> Dict[str, Any]:
        """
        Estimate nutrition information for a food item by name using LLM service
        
        Args:
            food_name: Name of the food item
            serving_size: Serving size for estimation
            
        Returns:
            Dict containing estimated nutrition data
        """
        start_time = time.time()
        
        try:
            print(f"DEBUG: Estimating nutrition for {food_name} using LLM")
            # Use LLM service for nutrition estimation
            result = llm_service.estimate_nutrition(food_name, serving_size)
            
            print(f"DEBUG: LLM estimation result: {result}")
            
            # Check if result is valid
            if not result or 'error' in result:
                print(f"DEBUG: LLM estimation failed or returned error, using fallback")
                return self._get_fallback_nutrition(food_name, serving_size)
            
            # Add metadata
            result['processing_time_ms'] = int((time.time() - start_time) * 1000)
            result['data_source'] = 'AI Estimated'
            result['estimation_method'] = 'LLM AI'
            result['timestamp'] = time.time()
            
            logger.info(f"Nutrition estimated for: {food_name} ({serving_size})")
            return result
            
        except Exception as e:
            logger.error(f"Nutrition estimation failed: {str(e)}")
            print(f"DEBUG: Exception in nutrition estimation: {str(e)}")
            return self._get_fallback_nutrition(food_name, serving_size)
    
    def _get_fallback_nutrition(self, food_name: str, serving_size: str) -> Dict[str, Any]:
        """
        Provide basic fallback nutrition data when LLM estimation fails
        
        Args:
            food_name: Name of the food
            serving_size: Serving size
            
        Returns:
            Basic nutrition data dict
        """
        print(f"DEBUG: Using fallback nutrition data for {food_name}")
        
        # Basic fallback nutrition values (generic estimates)
        return {
            'calories': 200,  # Generic calorie estimate
            'protein_g': 5.0,
            'carbohydrates_g': 30.0,
            'fat_g': 8.0,
            'fiber_g': 2.0,
            'sugar_g': 5.0,
            'sodium_mg': 300,
            'potassium_mg': 200,
            'vitamin_c_mg': 2.0,
            'calcium_mg': 50,
            'iron_mg': 1.0,
            'nutri_score': 'C',
            'glycemic_index': 50,
            'serving_size': serving_size,
            'data_source': 'Fallback Estimate',
            'confidence': 0.3,
            'food_name': food_name,
            'category': 'Unknown',
            'description': f'Fallback nutrition estimate for {food_name}',
            'processing_time_ms': 0,
            'timestamp': time.time()
        }
    
    def get_nutrition_data(self, food_result, serving_size='100g'):
        """
        Get comprehensive nutrition data for a food item
        
        Args:
            food_result: Dict containing food information
            serving_size: String serving size (e.g., '100g', '1 cup')
            
        Returns:
            dict: Comprehensive nutrition information
        """
        try:
            print(f"DEBUG: get_nutrition_data called with food_result: {food_result}")
            
            if not food_result.get('found', True):
                print(f"DEBUG: Food not found, using estimation for {food_result['food_name']}")
                return self.estimate_nutrition_by_name(food_result['food_name'], serving_size)
            
            # Check if this is LLM data with embedded nutrition_data
            if 'nutrition_data' in food_result:
                print("DEBUG: Found embedded nutrition_data from LLM")
                nutrition_data = food_result['nutrition_data']
                return self._format_llm_nutrition_data(nutrition_data, serving_size)
            
            # Check if we have a database food_id
            food_id = food_result.get('food_id')
            if food_id:
                print(f"DEBUG: Getting nutrition from database for food_id: {food_id}")
                food = Food.objects.get(id=food_id)
                primary_nutrition = food.primary_nutrition
                
                print(f"DEBUG: Primary nutrition for food_id {food_id}: {primary_nutrition}")
                
                if primary_nutrition:
                    print(f"DEBUG: Found primary nutrition, formatting data")
                    return self._format_nutrition_data(primary_nutrition, serving_size)
                else:
                    # Check if there are any nutrition profiles at all
                    all_profiles = food.nutrition_profiles.all()
                    print(f"DEBUG: All nutrition profiles for food_id {food_id}: {list(all_profiles)}")
                    
                    if all_profiles.exists():
                        # Use the first available nutrition profile
                        first_profile = all_profiles.first()
                        print(f"DEBUG: Using first available nutrition profile: {first_profile}")
                        return self._format_nutrition_data(first_profile, serving_size)
            
            # Fallback to estimation if no nutrition data available
            print(f"DEBUG: No nutrition data found, falling back to estimation for {food_result['food_name']}")
            return self.estimate_nutrition_by_name(food_result['food_name'], serving_size)
            
        except Exception as e:
            logger.error(f"Error getting nutrition data: {str(e)}")
            print(f"DEBUG: Exception in get_nutrition_data: {str(e)}")
            return self._get_default_nutrition(serving_size)
    
    def extract_nutrition_from_label(self, image_data: bytes) -> Dict[str, Any]:
        """
        Extract nutrition information from food label using LLM service
        
        Args:
            image_data: Raw image bytes of nutrition label
            
        Returns:
            Dict containing extracted nutrition data
        """
        start_time = time.time()
        
        try:
            # Use LLM service for nutrition label extraction
            result = llm_service.extract_nutrition_from_label(image_data)
            
            # Add metadata
            result['processing_time_ms'] = int((time.time() - start_time) * 1000)
            result['data_source'] = 'Nutrition Label OCR'
            result['extraction_method'] = 'LLM Vision'
            result['timestamp'] = time.time()
            
            logger.info(f"Nutrition extracted from label: {result.get('product_name', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Nutrition label extraction failed: {str(e)}")
            return self._create_error_response(str(e), time.time() - start_time)
    
    def _create_error_response(self, error_message: str, processing_time: float) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'error': error_message,
            'processing_time_ms': int(processing_time * 1000),
            'data_source': 'Nutrition Analysis',
            'timestamp': time.time()
        }
    
    def _generate_name_variations(self, food_name):
        """Generate common variations of a food name for fuzzy matching"""
        variations = []
        name_lower = food_name.lower()
        
        # Remove common words
        common_words = ['fresh', 'organic', 'raw', 'cooked', 'grilled', 'fried', 'baked']
        for word in common_words:
            if word in name_lower:
                variations.append(name_lower.replace(word, '').strip())
        
        # Add plural/singular variations
        if name_lower.endswith('s'):
            variations.append(name_lower[:-1])
        else:
            variations.append(name_lower + 's')
        
        # Split compound words
        if ' ' in name_lower:
            words = name_lower.split()
            variations.extend(words)
        
        return list(set(variations))
    
    def _format_nutrition_data(self, nutrition_profile, serving_size):
        """Format nutrition profile data for API response"""
        try:
            # Calculate serving size multiplier
            serving_grams = self._parse_serving_size(serving_size)
            multiplier = serving_grams / nutrition_profile.serving_size_grams
            
            return {
                'calories': nutrition_profile.calories * multiplier,
                'protein_g': nutrition_profile.protein_g * multiplier,
                'carbohydrates_g': nutrition_profile.carbohydrates_g * multiplier,
                'fat_g': nutrition_profile.fat_g * multiplier,
                'fiber_g': nutrition_profile.fiber_g * multiplier if nutrition_profile.fiber_g else None,
                'sugar_g': nutrition_profile.sugar_g * multiplier if nutrition_profile.sugar_g else None,
                'sodium_mg': nutrition_profile.sodium_mg * multiplier if nutrition_profile.sodium_mg else None,
                'serving_size': serving_size,
                'serving_size_grams': serving_grams,
                'nutri_score': nutrition_profile.food.nutri_score,
                'glycemic_load_index': nutrition_profile.food.glycemic_load_index,
                'confidence_score': nutrition_profile.confidence_score,
                'sources': [nutrition_profile.source.name]
            }
            
        except Exception as e:
            logger.error(f"Error formatting nutrition data: {str(e)}")
            return self._get_default_nutrition(serving_size)
    
    def _get_estimated_nutrition(self, food_name, serving_size):
        """Get estimated nutrition using AI when exact data is not available"""
        try:
            if not self.model:
                return self._get_default_nutrition(serving_size)
            
            prompt = f"""
            Estimate the nutrition information for "{food_name}" per {serving_size}.
            
            Provide realistic estimates based on typical values for this type of food.
            Respond in JSON format:
            {{
                "calories": estimated_calories,
                "protein_g": estimated_protein,
                "carbohydrates_g": estimated_carbs,
                "fat_g": estimated_fat,
                "fiber_g": estimated_fiber_or_null,
                "sugar_g": estimated_sugar_or_null,
                "sodium_mg": estimated_sodium_or_null,
                "serving_size_grams": estimated_grams,
                "nutri_score": estimated_score_A_to_E_or_null,
                "glycemic_load_index": estimated_GLI_or_null,
                "confidence_score": your_confidence_0_to_1
            }}
            
            Be conservative with estimates and indicate lower confidence for uncommon foods.
            """
            
            response = self.model.generate_content(prompt)
            
            import json
            try:
                data = json.loads(response.text.strip())
                data['sources'] = ['ai_estimated']
                return data
                
            except json.JSONDecodeError:
                return self._get_default_nutrition(serving_size)
                
        except Exception as e:
            logger.error(f"Error getting estimated nutrition: {str(e)}")
            return self._get_default_nutrition(serving_size)
    
    def _get_default_nutrition(self, serving_size):
        """Return default/fallback nutrition data"""
        serving_grams = self._parse_serving_size(serving_size)
        
        return {
            'calories': 200.0,  # Conservative estimate
            'protein_g': 10.0,
            'carbohydrates_g': 20.0,
            'fat_g': 10.0,
            'fiber_g': None,
            'sugar_g': None,
            'sodium_mg': None,
            'serving_size': serving_size,
            'serving_size_grams': serving_grams,
            'nutri_score': None,
            'glycemic_load_index': None,
            'confidence_score': 0.1,
            'sources': ['default_estimate']
        }
    
    def _parse_serving_size(self, serving_size):
        """Parse serving size string to grams"""
        serving_size = serving_size.lower().strip()
        
        # Common serving size conversions
        conversions = {
            '1 cup': 240,
            '1/2 cup': 120,
            '1 tbsp': 15,
            '1 tsp': 5,
            '1 slice': 30,
            '1 piece': 50,
            '1 medium': 150,
            '1 large': 200,
            '1 small': 100,
        }
        
        # Check for direct gram specification
        if 'g' in serving_size:
            try:
                return float(''.join(filter(str.isdigit, serving_size.split('g')[0])))
            except:
                pass
        
        # Check conversions
        for size, grams in conversions.items():
            if size in serving_size:
                return grams
        
        # Default to 100g
        return 100.0
