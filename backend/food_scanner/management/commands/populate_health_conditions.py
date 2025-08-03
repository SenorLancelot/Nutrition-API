from django.core.management.base import BaseCommand
from food_scanner.models import HealthCondition


class Command(BaseCommand):
    help = 'Populate database with common health conditions and their dietary guidelines'

    def handle(self, *args, **options):
        """Populate health conditions with comprehensive dietary guidelines"""
        
        health_conditions_data = [
            {
                'name': 'Diabetes',
                'description': 'Type 2 diabetes requiring blood sugar management through diet',
                'severity': 'moderate',
                'dietary_restrictions': {
                    'max_sugar_g': 25,           # Max added sugar per serving
                    'max_carbohydrates_g': 45,   # Max carbs per meal
                    'max_glycemic_index': 55,    # Low to medium GI foods
                    'avoid_ingredients': ['high fructose corn syrup', 'refined sugar', 'white flour']
                },
                'nutritional_targets': {
                    'min_fiber_g': 8,            # Minimum fiber per serving
                    'max_sodium_mg': 2000,       # Daily sodium limit
                    'min_protein_g': 15,         # Protein for satiety
                    'max_saturated_fat_g': 7     # Heart health
                },
                'warning_template': 'This food may cause blood sugar spikes due to high {nutrient} content.',
                'recommendation_template': 'Consider pairing with protein or fiber-rich foods to slow absorption.'
            },
            {
                'name': 'Hypertension',
                'description': 'High blood pressure requiring sodium restriction and heart-healthy nutrition',
                'severity': 'moderate',
                'dietary_restrictions': {
                    'max_sodium_mg': 1500,       # DASH diet recommendation
                    'max_saturated_fat_g': 6,    # Heart health
                    'avoid_ingredients': ['processed meats', 'canned soups', 'pickled foods']
                },
                'nutritional_targets': {
                    'min_potassium_mg': 400,     # Counteracts sodium
                    'min_magnesium_mg': 80,      # Blood pressure support
                    'min_fiber_g': 6,            # Heart health
                    'max_cholesterol_mg': 200    # Cardiovascular health
                },
                'warning_template': 'High sodium content may increase blood pressure.',
                'recommendation_template': 'Choose fresh, unprocessed alternatives when possible.'
            },
            {
                'name': 'Heart Disease',
                'description': 'Cardiovascular disease requiring heart-healthy dietary patterns',
                'severity': 'severe',
                'dietary_restrictions': {
                    'max_saturated_fat_g': 5,    # AHA guidelines
                    'max_trans_fat_g': 0,        # Eliminate trans fats
                    'max_cholesterol_mg': 150,   # Strict cholesterol limit
                    'max_sodium_mg': 1500,       # Blood pressure management
                    'avoid_ingredients': ['trans fats', 'palm oil', 'coconut oil']
                },
                'nutritional_targets': {
                    'min_omega3_mg': 250,        # Heart-protective fats
                    'min_fiber_g': 10,           # Cholesterol management
                    'min_potassium_mg': 500,     # Blood pressure
                    'max_added_sugar_g': 20      # Inflammation reduction
                },
                'warning_template': 'This food contains {nutrient} that may not be heart-healthy.',
                'recommendation_template': 'Focus on omega-3 rich fish, nuts, and whole grains instead.'
            },
            {
                'name': 'Celiac Disease',
                'description': 'Autoimmune condition requiring strict gluten-free diet',
                'severity': 'severe',
                'dietary_restrictions': {
                    'avoid_ingredients': [
                        'wheat', 'barley', 'rye', 'triticale', 'malt', 'brewer\'s yeast',
                        'wheat flour', 'semolina', 'durum', 'spelt', 'kamut'
                    ]
                },
                'nutritional_targets': {
                    'min_iron_mg': 8,            # Often deficient
                    'min_folate_mcg': 200,       # B-vitamin support
                    'min_fiber_g': 8,            # Digestive health
                    'min_calcium_mg': 300        # Bone health
                },
                'warning_template': 'This food may contain gluten - check ingredients carefully.',
                'recommendation_template': 'Look for certified gluten-free alternatives.'
            },
            {
                'name': 'Kidney Disease',
                'description': 'Chronic kidney disease requiring protein, phosphorus, and potassium management',
                'severity': 'severe',
                'dietary_restrictions': {
                    'max_protein_g': 20,         # Reduce kidney workload
                    'max_phosphorus_mg': 200,    # Prevent bone disease
                    'max_potassium_mg': 600,     # Prevent hyperkalemia
                    'max_sodium_mg': 2000,       # Fluid management
                    'avoid_ingredients': ['processed meats', 'nuts', 'seeds', 'chocolate']
                },
                'nutritional_targets': {
                    'max_protein_g': 15,         # Strict protein control
                    'min_calories': 150,         # Prevent malnutrition
                    'max_phosphorus_mg': 150     # Bone health
                },
                'warning_template': 'High {nutrient} content may strain kidney function.',
                'recommendation_template': 'Consult your nephrologist about portion sizes.'
            },
            {
                'name': 'GERD',
                'description': 'Gastroesophageal reflux disease requiring trigger food avoidance',
                'severity': 'mild',
                'dietary_restrictions': {
                    'avoid_ingredients': [
                        'citrus fruits', 'tomatoes', 'chocolate', 'mint', 'spicy foods',
                        'caffeine', 'alcohol', 'onions', 'garlic'
                    ],
                    'max_fat_g': 10,             # Slow gastric emptying
                    'avoid_acidic_foods': True
                },
                'nutritional_targets': {
                    'min_fiber_g': 5,            # Digestive health
                    'alkaline_foods_preferred': True
                },
                'warning_template': 'This food may trigger acid reflux symptoms.',
                'recommendation_template': 'Try smaller portions and avoid eating 3 hours before bedtime.'
            },
            {
                'name': 'High Cholesterol',
                'description': 'Elevated blood cholesterol requiring dietary cholesterol and saturated fat restriction',
                'severity': 'moderate',
                'dietary_restrictions': {
                    'max_cholesterol_mg': 200,   # Daily limit
                    'max_saturated_fat_g': 7,    # <7% of calories
                    'avoid_ingredients': ['egg yolks', 'organ meats', 'full-fat dairy']
                },
                'nutritional_targets': {
                    'min_fiber_g': 10,           # Soluble fiber lowers cholesterol
                    'min_plant_sterols_mg': 400, # Natural cholesterol blockers
                    'omega3_preferred': True     # Anti-inflammatory
                },
                'warning_template': 'High cholesterol or saturated fat content may raise blood cholesterol.',
                'recommendation_template': 'Choose lean proteins and increase soluble fiber intake.'
            },
            {
                'name': 'Lactose Intolerance',
                'description': 'Inability to digest lactose requiring dairy avoidance or lactase supplementation',
                'severity': 'mild',
                'dietary_restrictions': {
                    'avoid_ingredients': [
                        'milk', 'cheese', 'butter', 'cream', 'yogurt', 'ice cream',
                        'whey', 'casein', 'lactose'
                    ]
                },
                'nutritional_targets': {
                    'min_calcium_mg': 300,       # Replace dairy calcium
                    'min_vitamin_d_iu': 100,     # Calcium absorption
                    'lactose_free_alternatives': True
                },
                'warning_template': 'This food contains lactose which may cause digestive discomfort.',
                'recommendation_template': 'Look for lactose-free alternatives or take lactase supplements.'
            },
            {
                'name': 'Iron Deficiency Anemia',
                'description': 'Low iron levels requiring iron-rich foods and absorption enhancers',
                'severity': 'moderate',
                'dietary_restrictions': {
                    'limit_with_iron': ['tea', 'coffee', 'calcium supplements'],  # Iron inhibitors
                    'avoid_with_iron_meals': ['dairy products', 'whole grains']
                },
                'nutritional_targets': {
                    'min_iron_mg': 6,            # Boost iron intake
                    'min_vitamin_c_mg': 30,      # Enhance iron absorption
                    'heme_iron_preferred': True, # Better absorbed
                    'folate_support': True       # Red blood cell production
                },
                'warning_template': 'This food may inhibit iron absorption if eaten with iron-rich meals.',
                'recommendation_template': 'Pair iron-rich foods with vitamin C sources like citrus or bell peppers.'
            },
            {
                'name': 'Osteoporosis',
                'description': 'Bone density loss requiring calcium, vitamin D, and bone-supporting nutrients',
                'severity': 'moderate',
                'dietary_restrictions': {
                    'limit_sodium_mg': 2000,     # Calcium loss prevention
                    'limit_caffeine_mg': 300,    # Calcium absorption
                    'avoid_excess_protein': True  # Calcium excretion
                },
                'nutritional_targets': {
                    'min_calcium_mg': 400,       # Bone building
                    'min_vitamin_d_iu': 200,     # Calcium absorption
                    'min_magnesium_mg': 100,     # Bone matrix
                    'min_vitamin_k_mcg': 50,     # Bone protein synthesis
                    'weight_bearing_exercise': True
                },
                'warning_template': 'High sodium or caffeine may interfere with calcium absorption.',
                'recommendation_template': 'Focus on calcium-rich foods with vitamin D for optimal bone health.'
            }
        ]

        created_count = 0
        updated_count = 0

        for condition_data in health_conditions_data:
            condition, created = HealthCondition.objects.get_or_create(
                name=condition_data['name'],
                defaults=condition_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created health condition: {condition.name}')
                )
            else:
                # Update existing condition with new data
                for field, value in condition_data.items():
                    if field != 'name':  # Don't update the name field
                        setattr(condition, field, value)
                condition.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated health condition: {condition.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🏥 Health Conditions Summary:\n'
                f'   • Created: {created_count} new conditions\n'
                f'   • Updated: {updated_count} existing conditions\n'
                f'   • Total: {created_count + updated_count} conditions in database\n'
            )
        )
        
        # Display usage instructions
        self.stdout.write(
            self.style.HTTP_INFO(
                f'\n📋 Usage Instructions:\n'
                f'   • Health conditions are now available in the API\n'
                f'   • Frontend can fetch conditions from /api/health-conditions/\n'
                f'   • Each scan can include health_conditions array\n'
                f'   • System will provide personalized nutrition analysis\n'
            )
        )
