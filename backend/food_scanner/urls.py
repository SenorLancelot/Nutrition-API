from django.urls import path
from . import views

app_name = 'food_scanner'

urlpatterns = [
    # API endpoints
    path('api/identify-food/', views.identify_food, name='identify_food'),
    path('api/scan-barcode/', views.scan_barcode, name='scan_barcode'),
    path('api/scan/', views.scan_analyze, name='scan_analyze'),
    path('api/health-conditions/', views.get_health_conditions, name='get_health_conditions'),
    path('api/scan-history/', views.get_scan_history, name='get_scan_history'),
]
