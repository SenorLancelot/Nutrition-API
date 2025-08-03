from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Food(models.Model):
    """Unified food model with essential fields for fast queries"""
    FOOD_TYPE_CHOICES = [
        ('packaged', 'Packaged Food'),
        ('fresh', 'Fresh Food'),
        ('prepared', 'Prepared Food'),
        ('restaurant', 'Restaurant Food'),
    ]
    
    name = models.CharField(max_length=200, db_index=True)
    food_type = models.CharField(max_length=20, choices=FOOD_TYPE_CHOICES, default='fresh')
    category = models.CharField(max_length=100, default='general', db_index=True)
    
    # Packaged food specific fields
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    brand = models.CharField(max_length=100, blank=True)
    package_size = models.CharField(max_length=50, blank=True)  # e.g., "500g", "1L"
    
    # Common nutrition fields for fast queries/sorting
    calories_per_100g = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    nutri_score = models.CharField(
        max_length=1, 
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E')],
        null=True, blank=True
    )
    glycemic_load_index = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Metadata
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_food_type_display()})"

    @property
    def primary_nutrition(self):
        """Get the primary nutrition information"""
        return self.nutrition_profiles.filter(is_primary=True).first()

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'food_type']),
            models.Index(fields=['category', 'food_type']),
        ]


class NutritionSource(models.Model):
    """Model to track different sources of nutrition data"""
    SOURCE_TYPE_CHOICES = [
        ('database', 'Local Database'),
        ('open_food_facts', 'Open Food Facts'),
        ('nutrition_label', 'Nutrition Label (OCR)'),
        ('ai_estimated', 'AI Estimated'),
        ('user_input', 'User Input'),
        ('manual', 'Manual Entry'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    description = models.TextField(blank=True)
    reliability_score = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"
    
    class Meta:
        ordering = ['-reliability_score', 'name']


class NutritionProfile(models.Model):
    """Detailed nutrition information with multiple sources support"""
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='nutrition_profiles')
    source = models.ForeignKey(NutritionSource, on_delete=models.CASCADE)
    
    # Serving information
    serving_size = models.CharField(max_length=50, default='100g')
    serving_size_grams = models.FloatField(default=100.0, validators=[MinValueValidator(0)])
    
    # Macronutrients (per serving)
    calories = models.FloatField(validators=[MinValueValidator(0)])
    protein_g = models.FloatField(validators=[MinValueValidator(0)])
    carbohydrates_g = models.FloatField(validators=[MinValueValidator(0)])
    fat_g = models.FloatField(validators=[MinValueValidator(0)])
    
    # Detailed nutrients (optional)
    fiber_g = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    sugar_g = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    sodium_mg = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    cholesterol_mg = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    saturated_fat_g = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    trans_fat_g = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    
    # Vitamins and minerals (stored as JSON for flexibility)
    vitamins_minerals = models.JSONField(default=dict, blank=True)
    
    # Quality indicators
    confidence_score = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Source-specific metadata
    source_metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Ensure only one primary nutrition profile per food
        if self.is_primary:
            NutritionProfile.objects.filter(
                food=self.food, is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        # Update food's quick access fields from primary nutrition
        if self.is_primary:
            calories_per_100g = (self.calories / self.serving_size_grams) * 100
            self.food.calories_per_100g = calories_per_100g
            self.food.save(update_fields=['calories_per_100g'])
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.food.name} - {self.source.name} ({self.serving_size})"
    
    @property
    def calories_per_100g(self):
        """Calculate calories per 100g"""
        return (self.calories / self.serving_size_grams) * 100
    
    @property
    def macros_per_100g(self):
        """Get macronutrients per 100g"""
        multiplier = 100 / self.serving_size_grams
        return {
            'calories': self.calories * multiplier,
            'protein_g': self.protein_g * multiplier,
            'carbohydrates_g': self.carbohydrates_g * multiplier,
            'fat_g': self.fat_g * multiplier,
        }
    
    class Meta:
        ordering = ['-is_primary', '-confidence_score', '-created_at']
        unique_together = ['food', 'source', 'serving_size']


class HealthCondition(models.Model):
    """Model to store health conditions and their dietary restrictions"""
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='moderate')
    
    # Dietary restrictions and recommendations
    dietary_restrictions = models.JSONField(default=dict)  # e.g., {"max_sugar_g": 25, "avoid_ingredients": ["gluten"]}
    nutritional_targets = models.JSONField(default=dict)  # e.g., {"min_fiber_g": 25, "max_sodium_mg": 2300}
    
    # Health remarks templates
    warning_template = models.TextField(blank=True)  # Template for warnings
    recommendation_template = models.TextField(blank=True)  # Template for recommendations
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class ScanHistory(models.Model):
    """Model to store scan history with enhanced tracking"""
    SCAN_TYPE_CHOICES = [
        ('image', 'Image Recognition'),
        ('barcode', 'Barcode Scan'),
        ('text', 'Text Input'),
        ('nutrition_label', 'Nutrition Label OCR'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    food = models.ForeignKey(Food, on_delete=models.SET_NULL, null=True, blank=True)
    scan_type = models.CharField(max_length=20, choices=SCAN_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Input data
    input_data = models.TextField()  # Store image path, barcode, or text
    input_metadata = models.JSONField(default=dict)  # Additional input info
    
    # Health conditions for this scan
    health_conditions = models.JSONField(default=list)
    
    # Results
    scan_result = models.JSONField(default=dict)
    confidence_score = models.FloatField(null=True, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        food_name = self.food.name if self.food else "Unknown"
        return f"{food_name} - {self.get_scan_type_display()} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['scan_type', 'status']),
            models.Index(fields=['created_at']),
        ]
