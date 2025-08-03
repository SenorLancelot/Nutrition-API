import logging
import requests
import google.generativeai as genai
from django.conf import settings
from PIL import Image
from ..models import Food, NutritionProfile
from ..serializers import FoodListSerializer

logger = logging.getLogger('food_scanner')


class BarcodeScannerService:
    """Service for scanning barcodes and looking up food information"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.user_agent = settings.OPEN_FOOD_FACTS_USER_AGENT
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
    
    def scan_from_image(self, image_file):
        """
        Extract barcode from image and lookup food information
        
        Args:
            image_file: Django UploadedFile object containing barcode image
            
        Returns:
            dict: {
                'found': bool,
                'barcode_id': str,
                'food_name': str,
                'food_details': dict,
                'confidence_score': float,
                'source': str
            }
        """
        try:
            # Step 1: Extract barcode from image
            barcode_id = self._extract_barcode_from_image(image_file)
            
            if not barcode_id:
                return {
                    'found': False,
                    'barcode_id': None,
                    'food_name': None,
                    'food_details': None,
                    'confidence_score': 0.0,
                    'source': 'image_scan_failed'
                }
            
            # Step 2: Lookup barcode
            return self.lookup_barcode(barcode_id)
            
        except Exception as e:
            logger.error(f"Error scanning barcode from image: {str(e)}")
            return {
                'found': False,
                'barcode_id': None,
                'food_name': None,
                'food_details': None,
                'confidence_score': 0.0,
                'source': 'error'
            }
    
    def lookup_barcode(self, barcode_id):
        """
        Look up food information by barcode ID
        
        Args:
            barcode_id: String barcode identifier
            
        Returns:
            dict: Food information or not found result
        """
        try:
            # Step 1: Check local database first
            local_result = self._lookup_local_database(barcode_id)
            if local_result['found']:
                return local_result
            
            # Step 2: Check Open Food Facts
            off_result = self._lookup_open_food_facts(barcode_id)
            if off_result['found']:
                # Optionally save to local database for future use
                self._save_to_local_database(off_result)
                return off_result
            
            # Step 3: Not found anywhere
            return {
                'found': False,
                'barcode_id': barcode_id,
                'food_name': None,
                'food_details': None,
                'confidence_score': 0.0,
                'source': 'not_found'
            }
            
        except Exception as e:
            logger.error(f"Error looking up barcode {barcode_id}: {str(e)}")
            return {
                'found': False,
                'barcode_id': barcode_id,
                'food_name': None,
                'food_details': None,
                'confidence_score': 0.0,
                'source': 'error'
            }
    
    def _extract_barcode_from_image(self, image_file):
        """Extract barcode number from image using Gemini Vision"""
        if not self.model:
            logger.warning("Gemini API not available for barcode extraction")
            return None
        
        try:
            image = Image.open(image_file)
            
            prompt = """
            Analyze this image and extract any barcode numbers you can see.
            Look for:
            - UPC barcodes (usually 12 digits)
            - EAN barcodes (usually 13 digits)
            - Any other product identification numbers
            
            Return only the barcode number as a plain string, no additional text.
            If multiple barcodes are present, return the clearest/largest one.
            If no barcode is found, return "NONE".
            """
            
            response = self.model.generate_content([prompt, image])
            barcode_text = response.text.strip()
            
            # Clean and validate barcode
            barcode_text = ''.join(filter(str.isdigit, barcode_text))
            
            if barcode_text and barcode_text != "NONE" and len(barcode_text) >= 8:
                logger.info(f"Extracted barcode: {barcode_text}")
                return barcode_text
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting barcode from image: {str(e)}")
            return None
    
    def _lookup_local_database(self, barcode_id):
        """Look up barcode in local database"""
        try:
            food = Food.objects.filter(barcode=barcode_id).first()
            
            if food:
                serializer = FoodListSerializer(food)
                return {
                    'found': True,
                    'barcode_id': barcode_id,
                    'food_name': food.name,
                    'food_details': serializer.data,
                    'confidence_score': 1.0,
                    'source': 'local_database'
                }
            
            return {'found': False}
            
        except Exception as e:
            logger.error(f"Error looking up local database: {str(e)}")
            return {'found': False}
    
    def _lookup_open_food_facts(self, barcode_id):
        """Look up barcode in Open Food Facts API"""
        try:
            url = f"https://world.openfoodfacts.org/api/v0/product/{barcode_id}.json"
            headers = {
                'User-Agent': self.user_agent
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 1 and 'product' in data:
                    product = data['product']
                    
                    # Extract product information
                    food_name = (
                        product.get('product_name') or 
                        product.get('product_name_en') or 
                        product.get('generic_name') or 
                        'Unknown Product'
                    )
                    
                    # Extract nutrition information if available
                    nutriments = product.get('nutriments', {})
                    
                    food_details = {
                        'name': food_name,
                        'brand': product.get('brands', ''),
                        'categories': product.get('categories', ''),
                        'ingredients': product.get('ingredients_text', ''),
                        'nutrition': {
                            'energy_kcal': nutriments.get('energy-kcal_100g'),
                            'proteins': nutriments.get('proteins_100g'),
                            'carbohydrates': nutriments.get('carbohydrates_100g'),
                            'fat': nutriments.get('fat_100g'),
                            'fiber': nutriments.get('fiber_100g'),
                            'sugars': nutriments.get('sugars_100g'),
                            'salt': nutriments.get('salt_100g'),
                            'sodium': nutriments.get('sodium_100g')
                        },
                        'nutriscore_grade': product.get('nutriscore_grade', '').upper(),
                        'image_url': product.get('image_url', ''),
                        'barcode': barcode_id
                    }
                    
                    return {
                        'found': True,
                        'barcode_id': barcode_id,
                        'food_name': food_name,
                        'food_details': food_details,
                        'confidence_score': 0.9,
                        'source': 'open_food_facts'
                    }
            
            return {'found': False}
            
        except requests.RequestException as e:
            logger.error(f"Open Food Facts API error: {str(e)}")
            return {'found': False}
        except Exception as e:
            logger.error(f"Error parsing Open Food Facts response: {str(e)}")
            return {'found': False}
    
    def _save_to_local_database(self, food_data):
        """Save Open Food Facts data to local database for future use"""
        try:
            if not food_data.get('found') or not food_data.get('food_details'):
                return
            
            details = food_data['food_details']
            nutrition = details.get('nutrition', {})
            
            # Check if food already exists
            existing_food = Food.objects.filter(barcode=food_data['barcode_id']).first()
            if existing_food:
                return  # Already exists
            
            # Create new food entry
            food = Food.objects.create(
                name=details['name'],
                food_type='packaged',
                category='packaged_food',
                barcode=food_data['barcode_id'],
                brand=details.get('brand', ''),
                calories_per_100g=nutrition.get('energy_kcal'),
                nutri_score=details.get('nutriscore_grade'),
                image_url=details.get('image_url', ''),
                is_verified=False  # Mark as unverified since it's from external source
            )
            
            # Create nutrition profile if nutrition data is available
            if nutrition.get('energy_kcal'):
                from ..models import NutritionSource
                
                # Get or create Open Food Facts source
                source, created = NutritionSource.objects.get_or_create(
                    name='Open Food Facts',
                    defaults={
                        'source_type': 'open_food_facts',
                        'description': 'Open Food Facts collaborative database',
                        'reliability_score': 0.8
                    }
                )
                
                NutritionProfile.objects.create(
                    food=food,
                    source=source,
                    serving_size='100g',
                    serving_size_grams=100.0,
                    calories=nutrition.get('energy_kcal', 0),
                    protein_g=nutrition.get('proteins', 0) or 0,
                    carbohydrates_g=nutrition.get('carbohydrates', 0) or 0,
                    fat_g=nutrition.get('fat', 0) or 0,
                    fiber_g=nutrition.get('fiber'),
                    sugar_g=nutrition.get('sugars'),
                    sodium_mg=nutrition.get('sodium') * 1000 if nutrition.get('sodium') else None,
                    confidence_score=0.8,
                    is_primary=True,
                    source_metadata={
                        'open_food_facts_url': f"https://world.openfoodfacts.org/product/{food_data['barcode_id']}",
                        'categories': details.get('categories', ''),
                        'ingredients': details.get('ingredients', '')
                    }
                )
            
            logger.info(f"Saved food from Open Food Facts: {details['name']}")
            
        except Exception as e:
            logger.error(f"Error saving to local database: {str(e)}")
    
    def validate_barcode(self, barcode_id):
        """Validate barcode format"""
        if not barcode_id or not isinstance(barcode_id, str):
            return False, "Invalid barcode format"
        
        # Remove any non-digit characters
        clean_barcode = ''.join(filter(str.isdigit, barcode_id))
        
        # Check length (most common barcode lengths)
        if len(clean_barcode) not in [8, 12, 13, 14]:
            return False, "Invalid barcode length"
        
        return True, clean_barcode
