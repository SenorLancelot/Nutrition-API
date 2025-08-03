import time
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Food, NutritionProfile, NutritionSource, HealthCondition, ScanHistory
from .serializers import (
    IdentifyFoodSerializer, IdentifyFoodResponseSerializer,
    ScanBarcodeSerializer, ScanBarcodeResponseSerializer,
    ScanAnalyzeSerializer, NutritionAnalysisResponseSerializer,
    ErrorResponseSerializer
)
from .services.food_identification import FoodIdentificationService
from .services.barcode_scanner import BarcodeScannerService
from .services.nutrition_analyzer import NutritionAnalyzerService
from .services.health_analyzer import HealthAnalyzerService

logger = logging.getLogger('food_scanner')


@swagger_auto_schema(
    method='post',
    operation_description="Identify food from an uploaded image using AI",
    request_body=IdentifyFoodSerializer,
    responses={
        200: IdentifyFoodResponseSerializer,
        400: ErrorResponseSerializer,
        500: ErrorResponseSerializer,
    },
    tags=['Food Identification']
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def identify_food(request):
    """
    Identify food from an uploaded image using Gemini 1.5 Flash
    """
    start_time = time.time()
    
    try:
        serializer = IdentifyFoodSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'validation_error',
                'message': 'Invalid input data',
                'details': serializer.errors,
                'timestamp': time.time()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        image = serializer.validated_data['image']
        
        # Use food identification service with LLM
        identification_service = FoodIdentificationService()
        
        # Read image data for LLM service
        image_data = image.read()
        image.seek(0)  # Reset file pointer
        
        result = identification_service.identify_food_from_image(image_data)
        
        # Check if identification was successful
        if 'error' in result:
            return Response({
                'error': 'not_found',
                'message': 'Food not found or could not be identified',
                'details': result,
                'timestamp': time.time()
            }, status=status.HTTP_404_NOT_FOUND)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response_data = {
            'food_name': result.get('food_name', 'Unknown Food'),
            'confidence_score': result.get('confidence', 0.0),
            'suggested_foods': result.get('suggested_foods', []),
            'processing_time_ms': processing_time,
            'database_match': result.get('database_match', False)
        }
        
        logger.info(f"Food identified: {result['food_name']} (confidence: {result['confidence_score']})")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in identify_food: {str(e)}")
        return Response({
            'error': 'internal_error',
            'message': 'Failed to identify food from image',
            'details': {'error': str(e)},
            'timestamp': time.time()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Scan barcode from image or direct barcode input",
    request_body=ScanBarcodeSerializer,
    responses={
        200: ScanBarcodeResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
        500: ErrorResponseSerializer,
    },
    tags=['Barcode Scanning']
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def scan_barcode(request):
    """
    Scan barcode from image or process direct barcode input
    """
    start_time = time.time()
    
    try:
        serializer = ScanBarcodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'validation_error',
                'message': 'Invalid input data',
                'details': serializer.errors,
                'timestamp': time.time()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        barcode_image = serializer.validated_data.get('barcode_image')
        barcode_id = serializer.validated_data.get('barcode_id')
        
        # Use barcode scanner service
        scanner_service = BarcodeScannerService()
        
        if barcode_image:
            result = scanner_service.scan_from_image(barcode_image)
        else:
            result = scanner_service.lookup_barcode(barcode_id)
        
        if not result['found']:
            return Response({
                'error': 'not_found',
                'message': 'Food not found for the provided barcode',
                'details': {'barcode_id': result.get('barcode_id')},
                'timestamp': time.time()
            }, status=status.HTTP_404_NOT_FOUND)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response_data = {
            'food_name': result['food_name'],
            'barcode_id': result['barcode_id'],
            'food_details': result.get('food_details'),
            'confidence_score': result['confidence_score'],
            'source': result['source'],
            'processing_time_ms': processing_time
        }
        
        logger.info(f"Barcode scanned: {result['barcode_id']} -> {result['food_name']}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in scan_barcode: {str(e)}")
        return Response({
            'error': 'internal_error',
            'message': 'Failed to scan barcode',
            'details': {'error': str(e)},
            'timestamp': time.time()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_description="Comprehensive food analysis with nutrition and health recommendations",
    request_body=ScanAnalyzeSerializer,
    responses={
        200: NutritionAnalysisResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
        500: ErrorResponseSerializer,
    },
    tags=['Nutrition Analysis']
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def scan_analyze(request):
    """
    Comprehensive food analysis including nutrition data and health recommendations
    """
    start_time = time.time()
    scan_history = None
    
    try:
        serializer = ScanAnalyzeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'error': 'validation_error',
                'message': 'Invalid input data',
                'details': serializer.errors,
                'timestamp': time.time()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract validated data
        food_name = serializer.validated_data.get('food_name')
        barcode_id = serializer.validated_data.get('barcode_id')
        image = serializer.validated_data.get('image')
        image_type = serializer.validated_data.get('image_type', 'food')
        health_conditions = serializer.validated_data.get('health_conditions', [])
        serving_size = serializer.validated_data.get('serving_size', '100g')
        
        # Create scan history record
        scan_type = 'text' if food_name else ('barcode' if barcode_id else 'image')
        if image and image_type == 'nutrition_label':
            scan_type = 'nutrition_label'
        
        scan_history = ScanHistory.objects.create(
            scan_type=scan_type,
            status='processing',
            input_data=food_name or barcode_id or 'image_upload',
            health_conditions=health_conditions,
            input_metadata={
                'serving_size': serving_size,
                'image_type': image_type if image else None
            }
        )

        # Initialize services
        nutrition_service = NutritionAnalyzerService()
        health_service = HealthAnalyzerService()

        # Step 1: Get or identify food
        food_result = None

        if food_name:
            food_result = nutrition_service.get_food_by_name(food_name)
        elif barcode_id:
            scanner_service = BarcodeScannerService()
            barcode_result = scanner_service.lookup_barcode(barcode_id)
            if barcode_result['found']:
                food_result = barcode_result
        elif image:
            if image_type == 'nutrition_label':
                food_result = nutrition_service.extract_nutrition_from_label(image)
            else:
                identification_service = FoodIdentificationService()
                identify_result = identification_service.identify_from_image(image)
                print(identify_result)
                if identify_result['confidence_score'] > 0.6:
                    food_result = nutrition_service.get_food_by_name(identify_result['food_name'])
                    print(food_result)

        if not food_result or not food_result.get('found', True):
            scan_history.status = 'failed'
            scan_history.error_message = 'Food not found or could not be identified'
            scan_history.save()

            return Response({
                'error': 'not_found',
                'message': 'Food not found or could not be identified',
                'details': {},
                'timestamp': time.time()
            }, status=status.HTTP_404_NOT_FOUND)

        # Step 2: Get nutrition information
        nutrition_data = nutrition_service.get_nutrition_data(
            food_result,
            serving_size=serving_size
        )

        # Step 3: Analyze health implications
        health_analysis = health_service.analyze_for_conditions(
            nutrition_data,
            health_conditions
        )

        # Step 4: Calculate processing time and update scan history
        processing_time = int((time.time() - start_time) * 1000)

        # Prepare response data
        response_data = {
            'food_name': food_result['food_name'],
            'food_id': food_result.get('food_id'),
            'barcode_id': food_result.get('barcode_id'),
            'food_type': food_result.get('food_type', 'unknown'),
            'category': food_result.get('category', 'general'),
            'brand': food_result.get('brand', ''),

            'macros': {
                'calories': nutrition_data['calories'],
                'protein_g': nutrition_data['protein_g'],
                'carbohydrates_g': nutrition_data['carbohydrates_g'],
                'fat_g': nutrition_data['fat_g'],
                'fiber_g': nutrition_data.get('fiber_g'),
                'sugar_g': nutrition_data.get('sugar_g'),
                'sodium_mg': nutrition_data.get('sodium_mg'),
                'serving_size': serving_size,
                'serving_size_grams': nutrition_data.get('serving_size_grams', 100.0)
            },

            'nutri_score': nutrition_data.get('nutri_score'),
            'glycemic_load_index': nutrition_data.get('glycemic_load_index'),

            'health_remarks': health_analysis['remarks'],
            'overall_health_score': health_analysis.get('overall_score'),

            'confidence_score': nutrition_data.get('confidence_score', 1.0),
            'data_sources': nutrition_data.get('sources', []),

            'processing_time_ms': processing_time,
            'scan_id': scan_history.id
        }

        # Update scan history with results
        scan_history.food_id = food_result.get('food_id')
        scan_history.status = 'completed'
        scan_history.scan_result = response_data
        scan_history.confidence_score = response_data['confidence_score']
        scan_history.processing_time_ms = processing_time
        scan_history.save()

        logger.info(f"Scan completed: {food_result['food_name']} for conditions: {health_conditions}")

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in scan_analyze: {str(e)}")

        if scan_history:
            scan_history.status = 'failed'
            scan_history.error_message = str(e)
            scan_history.processing_time_ms = int((time.time() - start_time) * 1000)
            scan_history.save()

        return Response({
            'error': 'internal_error',
            'message': 'Failed to analyze food',
            'details': {'error': str(e)},
            'timestamp': time.time()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary="Get Health Conditions",
    operation_description="Retrieve all available health conditions for user selection",
    responses={
        200: openapi.Response(
            description="Health conditions retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'conditions': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'description': openapi.Schema(type=openapi.TYPE_STRING),
                                'severity': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    ),
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )
        ),
        500: ErrorResponseSerializer,
    },
    tags=['Health Conditions']
)
@swagger_auto_schema(
    method='post',
    operation_summary="Create Custom Health Condition",
    operation_description="Create a new custom health condition with dietary restrictions and nutritional targets",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['name', 'description'],
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='Condition name'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Condition description'),
            'severity': openapi.Schema(type=openapi.TYPE_STRING, enum=['mild', 'moderate', 'severe'], default='moderate'),
            'dietary_restrictions': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='JSON object with dietary restrictions (e.g., {"max_sugar_g": 25})'
            ),
            'nutritional_targets': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description='JSON object with nutritional targets (e.g., {"min_fiber_g": 8})'
            ),
            'warning_template': openapi.Schema(type=openapi.TYPE_STRING, description='Warning message template'),
            'recommendation_template': openapi.Schema(type=openapi.TYPE_STRING, description='Recommendation template'),
        }
    ),
    responses={
        201: openapi.Response(
            description="Health condition created successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'condition': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                            'description': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    )
                }
            )
        ),
        400: ErrorResponseSerializer,
        500: ErrorResponseSerializer,
    },
    tags=['Health Conditions']
)
@api_view(['GET', 'POST'])
def get_health_conditions(request):
    """
    Get all available health conditions for user selection
    """
    try:
        if request.method == 'GET':
            health_conditions = HealthCondition.objects.filter(is_active=True).order_by('name')
            
            conditions_data = []
            for condition in health_conditions:
                conditions_data.append({
                    'id': condition.id,
                    'name': condition.name,
                    'description': condition.description,
                    'severity': condition.severity,
                    'dietary_restrictions': condition.dietary_restrictions,
                    'nutritional_targets': condition.nutritional_targets
                })
            
            return Response({
                'conditions': conditions_data,
                'count': len(conditions_data),
                'timestamp': time.time()
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Validate required fields
            required_fields = ['name', 'description']
            for field in required_fields:
                if not request.data.get(field):
                    return Response({
                        'error': 'validation_error',
                        'message': f'Field "{field}" is required',
                        'timestamp': time.time()
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if condition already exists
            if HealthCondition.objects.filter(name__iexact=request.data['name']).exists():
                return Response({
                    'error': 'duplicate_condition',
                    'message': 'A health condition with this name already exists',
                    'timestamp': time.time()
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the health condition
            condition = HealthCondition.objects.create(
                name=request.data['name'].strip(),
                description=request.data['description'].strip(),
                severity=request.data.get('severity', 'moderate'),
                dietary_restrictions=request.data.get('dietary_restrictions', {}),
                nutritional_targets=request.data.get('nutritional_targets', {}),
                warning_template=request.data.get('warning_template', ''),
                recommendation_template=request.data.get('recommendation_template', ''),
                is_active=True
            )
            
            logger.info(f"Created custom health condition: {condition.name}")
            
            return Response({
                'message': 'Health condition created successfully',
                'condition': {
                    'id': condition.id,
                    'name': condition.name,
                    'description': condition.description,
                    'severity': condition.severity,
                    'dietary_restrictions': condition.dietary_restrictions,
                    'nutritional_targets': condition.nutritional_targets
                },
                'timestamp': time.time()
            }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Failed to fetch health conditions: {str(e)}")
        return Response({
            'error': 'fetch_failed',
            'message': 'Failed to fetch health conditions',
            'details': {'error': str(e)},
            'timestamp': time.time()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='get',
    operation_summary="Get Scan History",
    operation_description="Retrieve user's scan history with pagination",
    manual_parameters=[
        openapi.Parameter(
            'page',
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            default=1
        ),
        openapi.Parameter(
            'page_size',
            openapi.IN_QUERY,
            description="Number of items per page",
            type=openapi.TYPE_INTEGER,
            default=20
        ),
    ],
    responses={
        200: openapi.Response(
            description="Scan history retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'food_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'scan_type': openapi.Schema(type=openapi.TYPE_STRING),
                                'created_at': openapi.Schema(type=openapi.TYPE_STRING),
                                'health_score': openapi.Schema(type=openapi.TYPE_NUMBER),
                            }
                        )
                    ),
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'next': openapi.Schema(type=openapi.TYPE_STRING),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        500: ErrorResponseSerializer,
    },
    tags=['Scan History']
)
@api_view(['GET'])
def get_scan_history(request):
    """
    Get user's scan history with pagination
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        # Get all scan history ordered by most recent
        scan_history = ScanHistory.objects.all().order_by('-created_at')
        
        # Simple pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_scans = scan_history[start_idx:end_idx]
        
        # Format response data
        results = []
        for scan in paginated_scans:
            # Get food name from food relationship or scan result
            food_name = 'Unknown Food'
            if scan.food:
                food_name = scan.food.name
            elif scan.scan_result and scan.scan_result.get('food_name'):
                food_name = scan.scan_result['food_name']
            
            # Get health score from scan result if available
            health_score = None
            if scan.scan_result and scan.scan_result.get('overall_health_score'):
                health_score = scan.scan_result['overall_health_score']
            
            results.append({
                'id': scan.id,
                'food_name': food_name,
                'scan_type': scan.scan_type,
                'created_at': scan.created_at.isoformat(),
                'health_score': health_score,
                'status': scan.status,
                'processing_time_ms': scan.processing_time_ms,
                'confidence_score': scan.confidence_score,
                'health_conditions': scan.health_conditions,
                'scan_result': scan.scan_result,
                'error_message': scan.error_message,
                'food': {
                    'id': scan.food.id if scan.food else None,
                    'name': scan.food.name if scan.food else None,
                } if scan.food else None
            })
        
        # Calculate pagination info
        total_count = scan_history.count()
        has_next = end_idx < total_count
        has_previous = page > 1
        
        return Response({
            'results': results,
            'count': total_count,
            'next': f"?page={page + 1}&page_size={page_size}" if has_next else None,
            'previous': f"?page={page - 1}&page_size={page_size}" if has_previous else None,
            'page': page,
            'page_size': page_size,
            'timestamp': time.time()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to fetch scan history: {str(e)}")
        return Response({
            'error': 'fetch_failed',
            'message': 'Failed to fetch scan history',
            'details': {'error': str(e)},
            'timestamp': time.time()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
