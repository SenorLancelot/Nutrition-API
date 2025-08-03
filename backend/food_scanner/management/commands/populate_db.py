from django.core.management.base import BaseCommand
from django.db import transaction
from food_scanner.models import Food, NutritionProfile, NutritionSource, HealthCondition


class Command(BaseCommand):
    help = 'Populate database with initial food items and health conditions for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Food.objects.all().delete()
            NutritionSource.objects.all().delete()
            HealthCondition.objects.all().delete()

        with transaction.atomic():
            # Create nutrition sources
            self.create_nutrition_sources()
            
            # Create health conditions
            self.create_health_conditions()
            
            # Create sample foods
            self.create_sample_foods()

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with initial data')
        )

    def create_nutrition_sources(self):
        self.stdout.write('Creating nutrition sources...')
        
        sources = [
            {
                'name': 'Local Database',
                'source_type': 'database',
                'description': 'Curated local food database',
                'reliability_score': 0.95
            },
            {
                'name': 'Open Food Facts',
                'source_type': 'open_food_facts',
                'description': 'Open Food Facts collaborative database',
                'reliability_score': 0.85
            },
            {
                'name': 'Nutrition Label OCR',
                'source_type': 'nutrition_label',
                'description': 'Extracted from nutrition labels using OCR',
                'reliability_score': 0.80
            },
            {
                'name': 'AI Estimated',
                'source_type': 'ai_estimated',
                'description': 'AI-generated nutrition estimates',
                'reliability_score': 0.70
            },
        ]
        
        for source_data in sources:
            source, created = NutritionSource.objects.get_or_create(
                name=source_data['name'],
                defaults=source_data
            )
            if created:
                self.stdout.write(f'Created nutrition source: {source.name}')

    def create_health_conditions(self):
        self.stdout.write('Creating health conditions...')
        
        conditions = [
            {
                'name': 'Diabetes',
                'description': 'Type 1 or Type 2 diabetes requiring blood sugar management',
                'severity': 'moderate',
                'dietary_restrictions': {
                    'max_sugar_g': 25,
                    'max_carbohydrates_g': 45
                },
                'nutritional_targets': {
                    'min_fiber_g': 25,
                    'max_sodium_mg': 2300
                },
                'warning_template': 'High sugar/carb content may affect blood glucose levels',
                'recommendation_template': 'Consider portion control and pairing with protein'
            },
            {
                'name': 'Hypertension',
                'description': 'High blood pressure requiring sodium restriction',
                'severity': 'moderate',
                'dietary_restrictions': {
                    'max_sodium_mg': 1500
                },
                'nutritional_targets': {
                    'min_potassium_mg': 3500
                },
                'warning_template': 'High sodium content may increase blood pressure',
                'recommendation_template': 'Choose low-sodium alternatives'
            },
            {
                'name': 'Heart Disease',
                'description': 'Cardiovascular disease requiring heart-healthy diet',
                'severity': 'severe',
                'dietary_restrictions': {
                    'max_saturated_fat_g': 13,
                    'max_cholesterol_mg': 200,
                    'max_sodium_mg': 2000
                },
                'nutritional_targets': {
                    'min_fiber_g': 30
                },
                'warning_template': 'High saturated fat/cholesterol may impact heart health',
                'recommendation_template': 'Choose lean proteins and increase fiber intake'
            },
            {
                'name': 'Nut Allergy',
                'description': 'Allergic reaction to tree nuts and peanuts',
                'severity': 'severe',
                'dietary_restrictions': {
                    'avoid_ingredients': ['nuts', 'peanuts', 'tree nuts', 'almonds', 'walnuts']
                },
                'warning_template': 'May contain nuts or nut traces - check ingredients carefully',
                'recommendation_template': 'Verify nut-free certification before consumption'
            }
        ]
        
        for condition_data in conditions:
            condition, created = HealthCondition.objects.get_or_create(
                name=condition_data['name'],
                defaults=condition_data
            )
            if created:
                self.stdout.write(f'Created health condition: {condition.name}')

    def create_sample_foods(self):
        self.stdout.write('Creating sample foods...')
        
        # Get the local database source
        local_source = NutritionSource.objects.get(name='Local Database')
        
        foods_data = [
            # Fresh Foods
            {
                'name': 'Apple',
                'food_type': 'fresh',
                'category': 'fruits',
                'calories_per_100g': 52,
                'nutri_score': 'A',
                'glycemic_load_index': 6,
                'nutrition': {
                    'calories': 52, 'protein_g': 0.3, 'carbohydrates_g': 14,
                    'fat_g': 0.2, 'fiber_g': 2.4, 'sugar_g': 10.4
                }
            },
            {
                'name': 'Banana',
                'food_type': 'fresh',
                'category': 'fruits',
                'calories_per_100g': 89,
                'nutri_score': 'A',
                'glycemic_load_index': 12,
                'nutrition': {
                    'calories': 89, 'protein_g': 1.1, 'carbohydrates_g': 23,
                    'fat_g': 0.3, 'fiber_g': 2.6, 'sugar_g': 12.2
                }
            },
            {
                'name': 'Chicken Breast',
                'food_type': 'fresh',
                'category': 'meat',
                'calories_per_100g': 165,
                'nutri_score': 'B',
                'glycemic_load_index': 0,
                'nutrition': {
                    'calories': 165, 'protein_g': 31, 'carbohydrates_g': 0,
                    'fat_g': 3.6, 'fiber_g': 0, 'sodium_mg': 74
                }
            },
            # Packaged Foods with Barcodes
            {
                'name': 'Whole Wheat Bread',
                'food_type': 'packaged',
                'category': 'bakery',
                'brand': 'Sample Brand',
                'barcode': '1234567890123',
                'calories_per_100g': 247,
                'nutri_score': 'B',
                'glycemic_load_index': 9,
                'nutrition': {
                    'calories': 247, 'protein_g': 13, 'carbohydrates_g': 41,
                    'fat_g': 4.2, 'fiber_g': 6, 'sugar_g': 5.7, 'sodium_mg': 491
                }
            },
            {
                'name': 'Greek Yogurt',
                'food_type': 'packaged',
                'category': 'dairy',
                'brand': 'Sample Dairy',
                'barcode': '2345678901234',
                'calories_per_100g': 59,
                'nutri_score': 'A',
                'glycemic_load_index': 3,
                'nutrition': {
                    'calories': 59, 'protein_g': 10, 'carbohydrates_g': 3.6,
                    'fat_g': 0.4, 'fiber_g': 0, 'sugar_g': 3.6, 'sodium_mg': 36
                }
            },
            {
                'name': 'Potato Chips',
                'food_type': 'packaged',
                'category': 'snacks',
                'brand': 'Snack Co',
                'barcode': '3456789012345',
                'calories_per_100g': 536,
                'nutri_score': 'E',
                'glycemic_load_index': 11,
                'nutrition': {
                    'calories': 536, 'protein_g': 7, 'carbohydrates_g': 53,
                    'fat_g': 34, 'fiber_g': 4.8, 'sugar_g': 0.3, 'sodium_mg': 525
                }
            }
        ]
        
        for food_data in foods_data:
            nutrition_data = food_data.pop('nutrition')
            
            food, created = Food.objects.get_or_create(
                name=food_data['name'],
                defaults=food_data
            )
            
            if created:
                # Create nutrition profile
                NutritionProfile.objects.create(
                    food=food,
                    source=local_source,
                    serving_size='100g',
                    serving_size_grams=100.0,
                    is_primary=True,
                    is_verified=True,
                    confidence_score=0.95,
                    **nutrition_data
                )
                self.stdout.write(f'Created food: {food.name}')
        
        self.stdout.write(f'Created {Food.objects.count()} foods total')
