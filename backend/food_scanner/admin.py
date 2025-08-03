from django.contrib import admin
from .models import Food, NutritionProfile, NutritionSource, HealthCondition, ScanHistory


@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ['name', 'food_type', 'category', 'brand', 'barcode', 'calories_per_100g', 'nutri_score', 'is_verified']
    list_filter = ['food_type', 'category', 'nutri_score', 'is_verified']
    search_fields = ['name', 'brand', 'barcode']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'food_type', 'category', 'description')
        }),
        ('Product Details', {
            'fields': ('brand', 'package_size', 'barcode', 'image_url')
        }),
        ('Quick Nutrition (for fast queries)', {
            'fields': ('calories_per_100g', 'nutri_score', 'glycemic_load_index')
        }),
        ('Status', {
            'fields': ('is_verified', 'created_at', 'updated_at')
        }),
    )


@admin.register(NutritionSource)
class NutritionSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'reliability_score', 'is_active']
    list_filter = ['source_type', 'is_active']
    search_fields = ['name', 'description']


@admin.register(NutritionProfile)
class NutritionProfileAdmin(admin.ModelAdmin):
    list_display = ['food', 'source', 'serving_size', 'calories', 'is_primary', 'confidence_score', 'is_verified']
    list_filter = ['source', 'is_primary', 'is_verified']
    search_fields = ['food__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('food', 'source', 'serving_size', 'serving_size_grams')
        }),
        ('Macronutrients', {
            'fields': ('calories', 'protein_g', 'carbohydrates_g', 'fat_g')
        }),
        ('Detailed Nutrients', {
            'fields': ('fiber_g', 'sugar_g', 'sodium_mg', 'cholesterol_mg', 'saturated_fat_g', 'trans_fat_g')
        }),
        ('Additional Info', {
            'fields': ('vitamins_minerals', 'source_metadata')
        }),
        ('Quality Indicators', {
            'fields': ('confidence_score', 'is_primary', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(HealthCondition)
class HealthConditionAdmin(admin.ModelAdmin):
    list_display = ['name', 'severity', 'is_active']
    list_filter = ['severity', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'severity', 'is_active')
        }),
        ('Dietary Guidelines', {
            'fields': ('dietary_restrictions', 'nutritional_targets')
        }),
        ('Health Remarks Templates', {
            'fields': ('warning_template', 'recommendation_template')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    list_display = ['food', 'scan_type', 'status', 'confidence_score', 'processing_time_ms', 'created_at']
    list_filter = ['scan_type', 'status', 'created_at']
    search_fields = ['food__name', 'input_data']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Scan Information', {
            'fields': ('food', 'scan_type', 'status', 'input_data', 'input_metadata')
        }),
        ('Health Analysis', {
            'fields': ('health_conditions',)
        }),
        ('Results', {
            'fields': ('scan_result', 'confidence_score', 'processing_time_ms')
        }),
        ('Error Handling', {
            'fields': ('error_message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
