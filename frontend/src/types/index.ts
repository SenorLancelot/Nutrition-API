// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  details?: any;
  timestamp?: number;
}

// Food Types
export interface Food {
  id: number;
  name: string;
  food_type: string;
  food_type_display: string;
  category: string;
  brand?: string;
  barcode?: string;
  calories_per_100g?: number;
  nutri_score?: string;
  glycemic_load_index?: number;
  is_verified: boolean;
  primary_nutrition?: NutritionProfile;
}

export interface NutritionProfile {
  id: number;
  source: NutritionSource;
  serving_size: string;
  serving_size_grams: number;
  calories: number;
  protein_g: number;
  carbohydrates_g: number;
  fat_g: number;
  fiber_g?: number;
  sugar_g?: number;
  sodium_mg?: number;
  confidence_score: number;
  is_primary: boolean;
  calories_per_100g: number;
  macros_per_100g: MacrosPer100g;
}

export interface NutritionSource {
  id: number;
  name: string;
  source_type: string;
  reliability_score: number;
}

export interface MacrosPer100g {
  calories: number;
  protein_g: number;
  carbohydrates_g: number;
  fat_g: number;
}

// Health Types
export interface HealthCondition {
  id?: number;
  name: string;
  severity?: 'mild' | 'moderate' | 'severe' | string;
  description?: string;
  dietary_restrictions?: any;
}

export interface HealthRemark {
  condition: string;
  severity: 'info' | 'warning' | 'danger';
  message: string;
  recommendation?: string;
}

// Nutrition Analysis Types
export interface Macronutrients {
  calories: number;
  protein_g: number;
  carbohydrates_g: number;
  fat_g: number;
  fiber_g?: number;
  sugar_g?: number;
  sodium_mg?: number;
  serving_size: string;
  serving_size_grams: number;
}

export interface NutritionAnalysisResponse {
  food_name: string;
  food_id?: number;
  barcode_id?: string;
  food_type: string;
  category: string;
  brand?: string;
  macros: Macronutrients;
  nutri_score?: string;
  glycemic_load_index?: number;
  health_remarks: HealthRemark[];
  overall_health_score?: number;
  confidence_score: number;
  data_sources: string[];
  processing_time_ms?: number;
  scan_id?: number;
}

// API Request Types
export interface IdentifyFoodRequest {
  image: File;
}

export interface IdentifyFoodResponse {
  food_name: string;
  confidence_score: number;
  suggested_foods?: Array<{
    name: string;
    confidence: number;
  }>;
  processing_time_ms?: number;
}

export interface ScanBarcodeRequest {
  barcode_image?: File;
  barcode_id?: string;
}

export interface ScanBarcodeResponse {
  food_name: string;
  barcode_id: string;
  food_details?: Food;
  confidence_score: number;
  source: string;
  processing_time_ms?: number;
}

export interface ScanAnalyzeRequest {
  food_name?: string;
  barcode_id?: string;
  image?: File;
  image_type?: 'food' | 'nutrition_label';
  health_conditions?: string[];
  serving_size?: string;
}

// Scan History
export interface ScanHistory {
  id: string;
  user_id?: string;
  scan_type: 'image' | 'barcode' | 'text';
  food_name?: string;
  barcode_id?: string;
  status: 'pending' | 'success' | 'error';
  result?: NutritionAnalysisResponse;
  error_message?: string;
  timestamp: string;
  processing_time_ms?: number;
  metadata?: Record<string, any>;
}

// Alias for ScanHistory to match component usage
export type ScanHistoryItem = ScanHistory;

// Component Props Types
export interface FoodScannerProps {
  healthConditions: HealthCondition[];
  onAddHealthCondition: (condition: HealthCondition) => void;
  onRemoveHealthCondition: (conditionName: string) => void;
}

export interface HealthConditionsProps {
  conditions: HealthCondition[];
  onAdd: (condition: HealthCondition) => void;
  onRemove: (conditionName: string) => void;
}

// UI State Types
export interface ScanState {
  isScanning: boolean;
  scanType: 'image' | 'barcode' | 'text' | null;
  result: NutritionAnalysisResponse | null;
  error: string | null;
  loading: boolean;
}

export interface CameraState {
  isOpen: boolean;
  facingMode: 'user' | 'environment';
  hasPermission: boolean;
}
