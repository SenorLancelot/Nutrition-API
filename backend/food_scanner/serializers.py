from rest_framework import serializers
from .models import Food, NutritionProfile, NutritionSource, HealthCondition, ScanHistory


class NutritionSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutritionSource
        fields = '__all__'


class NutritionProfileSerializer(serializers.ModelSerializer):
    source = NutritionSourceSerializer(read_only=True)
    calories_per_100g = serializers.ReadOnlyField()
    macros_per_100g = serializers.ReadOnlyField()
    
    class Meta:
        model = NutritionProfile
        fields = '__all__'


class FoodSerializer(serializers.ModelSerializer):
    primary_nutrition = NutritionProfileSerializer(read_only=True)
    nutrition_profiles = NutritionProfileSerializer(many=True, read_only=True)
    food_type_display = serializers.CharField(source='get_food_type_display', read_only=True)
    
    class Meta:
        model = Food
        fields = '__all__'


class FoodListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for food lists"""
    primary_nutrition = NutritionProfileSerializer(read_only=True)
    food_type_display = serializers.CharField(source='get_food_type_display', read_only=True)
    
    class Meta:
        model = Food
        fields = [
            'id', 'name', 'food_type', 'food_type_display', 'category', 'barcode',
            'brand', 'calories_per_100g', 'nutri_score', 'glycemic_load_index',
            'is_verified', 'primary_nutrition'
        ]


class HealthConditionSerializer(serializers.ModelSerializer):
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = HealthCondition
        fields = '__all__'


class ScanHistorySerializer(serializers.ModelSerializer):
    food = FoodListSerializer(read_only=True)
    scan_type_display = serializers.CharField(source='get_scan_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ScanHistory
        fields = '__all__'


# API Endpoint Serializers

class IdentifyFoodSerializer(serializers.Serializer):
    """Serializer for identify-food endpoint"""
    image = serializers.ImageField(help_text="Food image to identify")


class IdentifyFoodResponseSerializer(serializers.Serializer):
    """Response serializer for identify-food endpoint"""
    food_name = serializers.CharField()
    confidence_score = serializers.FloatField()
    suggested_foods = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Alternative food suggestions with confidence scores"
    )
    processing_time_ms = serializers.IntegerField(required=False)


class ScanBarcodeSerializer(serializers.Serializer):
    """Serializer for scan-barcode endpoint"""
    barcode_image = serializers.ImageField(
        required=False,
        help_text="Image containing barcode to scan"
    )
    barcode_id = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Direct barcode number input"
    )
    
    def validate(self, data):
        if not data.get('barcode_image') and not data.get('barcode_id'):
            raise serializers.ValidationError(
                "Either barcode_image or barcode_id must be provided"
            )
        return data


class ScanBarcodeResponseSerializer(serializers.Serializer):
    """Response serializer for scan-barcode endpoint"""
    food_name = serializers.CharField()
    barcode_id = serializers.CharField()
    food_details = FoodListSerializer(required=False)
    confidence_score = serializers.FloatField()
    source = serializers.CharField(help_text="Data source: local_db, open_food_facts, etc.")
    processing_time_ms = serializers.IntegerField(required=False)


class ScanAnalyzeSerializer(serializers.Serializer):
    """Serializer for comprehensive scan endpoint"""
    food_name = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Direct food name input"
    )
    barcode_id = serializers.CharField(
        max_length=50,
        required=False,
        help_text="Barcode number"
    )
    image = serializers.ImageField(
        required=False,
        help_text="Food image for identification or nutrition label OCR"
    )
    image_type = serializers.ChoiceField(
        choices=[('food', 'Food Image'), ('nutrition_label', 'Nutrition Label')],
        default='food',
        required=False,
        help_text="Type of image provided"
    )
    health_conditions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        help_text="List of health conditions for personalized analysis"
    )
    serving_size = serializers.CharField(
        max_length=50,
        required=False,
        default='100g',
        help_text="Serving size for nutrition calculation"
    )
    
    def validate(self, data):
        if not any([data.get('food_name'), data.get('barcode_id'), data.get('image')]):
            raise serializers.ValidationError(
                "At least one of food_name, barcode_id, or image must be provided"
            )
        return data


class MacronutrientsSerializer(serializers.Serializer):
    """Serializer for macronutrient information"""
    calories = serializers.FloatField()
    protein_g = serializers.FloatField()
    carbohydrates_g = serializers.FloatField()
    fat_g = serializers.FloatField()
    fiber_g = serializers.FloatField(required=False)
    sugar_g = serializers.FloatField(required=False)
    sodium_mg = serializers.FloatField(required=False)
    serving_size = serializers.CharField()
    serving_size_grams = serializers.FloatField()


class HealthRemarkSerializer(serializers.Serializer):
    """Serializer for health remarks"""
    condition = serializers.CharField()
    severity = serializers.ChoiceField(choices=[('info', 'Info'), ('warning', 'Warning'), ('danger', 'Danger')])
    message = serializers.CharField()
    recommendation = serializers.CharField(required=False)


class NutritionAnalysisResponseSerializer(serializers.Serializer):
    """Comprehensive response serializer for scan endpoint"""
    # Food identification
    food_name = serializers.CharField()
    food_id = serializers.IntegerField(required=False)
    barcode_id = serializers.CharField(required=False, allow_null=True)
    food_type = serializers.CharField()
    category = serializers.CharField()
    brand = serializers.CharField(required=False)
    
    # Nutrition information
    macros = MacronutrientsSerializer()
    nutri_score = serializers.CharField(required=False, allow_null=True)
    glycemic_load_index = serializers.FloatField(required=False, allow_null=True)
    
    # Health analysis
    health_remarks = HealthRemarkSerializer(many=True)
    overall_health_score = serializers.FloatField(
        required=False,
        help_text="Overall health score from 0-10 based on conditions"
    )
    
    # Quality indicators
    confidence_score = serializers.FloatField()
    data_sources = serializers.ListField(
        child=serializers.CharField(),
        help_text="Sources used for nutrition data"
    )
    
    # Processing metadata
    processing_time_ms = serializers.IntegerField(required=False)
    scan_id = serializers.IntegerField(required=False, help_text="Scan history ID")


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response serializer"""
    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField()
