import axios, { AxiosError } from 'axios';
import {
  IdentifyFoodRequest,
  IdentifyFoodResponse,
  ScanBarcodeRequest,
  ScanBarcodeResponse,
  ScanAnalyzeRequest,
  NutritionAnalysisResponse,
  ScanHistory,
  HealthCondition,
  ApiResponse
} from '../types';

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth headers if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API Service Class
export class FoodScannerAPI {
  
  /**
   * Identify food from an uploaded image
   */
  static async identifyFood(request: IdentifyFoodRequest): Promise<IdentifyFoodResponse> {
    const formData = new FormData();
    formData.append('image', request.image);

    const response = await api.post<IdentifyFoodResponse>('/api/identify-food/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Scan barcode from image or direct barcode input
   */
  static async scanBarcode(request: ScanBarcodeRequest): Promise<ScanBarcodeResponse> {
    const formData = new FormData();
    
    if (request.barcode_image) {
      formData.append('barcode_image', request.barcode_image);
    }
    
    if (request.barcode_id) {
      formData.append('barcode_id', request.barcode_id);
    }

    const response = await api.post<ScanBarcodeResponse>('/api/scan-barcode/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Comprehensive food analysis with nutrition and health recommendations
   */
  static async scanAnalyze(request: ScanAnalyzeRequest): Promise<NutritionAnalysisResponse> {
    const formData = new FormData();
    
    if (request.food_name) {
      formData.append('food_name', request.food_name);
    }
    
    if (request.barcode_id) {
      formData.append('barcode_id', request.barcode_id);
    }
    
    if (request.image) {
      formData.append('image', request.image);
    }
    
    if (request.image_type) {
      formData.append('image_type', request.image_type);
    }
    
    if (request.health_conditions && request.health_conditions.length > 0) {
      request.health_conditions.forEach((condition, index) => {
        formData.append(`health_conditions[${index}]`, condition);
      });
    }
    
    if (request.serving_size) {
      formData.append('serving_size', request.serving_size);
    }

    const response = await api.post<NutritionAnalysisResponse>('/api/scan/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Get scan history
   */
  static async getScanHistory(page: number = 1, pageSize: number = 20): Promise<{
    results: ScanHistory[];
    count: number;
    next: string | null;
    previous: string | null;
  }> {
    const response = await api.get('/api/scan-history/', {
      params: {
        page,
        page_size: pageSize,
      },
    });

    return response.data;
  }

  /**
   * Get available health conditions
   */
  static async getHealthConditions(): Promise<{
    health_conditions: Array<{
      id: number;
      name: string;
      description: string;
      severity: string;
      dietary_restrictions?: any;
    }>;
    count: number;
    timestamp: number;
  }> {
    const response = await api.get('/api/health-conditions/');
    return response.data;
  }

  /**
   * Create custom health condition
   */
  static async createHealthCondition(conditionData: {
    name: string;
    description: string;
    severity?: 'mild' | 'moderate' | 'severe';
    dietary_restrictions?: Record<string, any>;
    nutritional_targets?: Record<string, any>;
    warning_template?: string;
    recommendation_template?: string;
  }): Promise<{
    message: string;
    condition: HealthCondition;
  }> {
    const response = await api.post('/api/health-conditions/', conditionData);
    return response.data;
  }

  /**
   * Test API connection
   */
  static async testConnection(): Promise<boolean> {
    try {
      const response = await api.get('/api/health/');
      return response.status === 200;
    } catch (error) {
      console.error('API connection test failed:', error);
      return false;
    }
  }
}

// Helper function to handle API errors
export const handleApiError = (error: any): string => {
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred. Please try again.';
};

// Export a singleton instance for easier usage
export const apiService = FoodScannerAPI;

// Helper function to validate file types
export const validateImageFile = (file: File): { valid: boolean; error?: string } => {
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  const maxSize = 5 * 1024 * 1024; // 5MB

  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Please upload a valid image file (JPEG, PNG, or WebP)',
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: 'Image file size must be less than 5MB',
    };
  }

  return { valid: true };
};

// Default export for backward compatibility
export default FoodScannerAPI;
