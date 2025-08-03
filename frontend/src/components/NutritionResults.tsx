import React from 'react';
import { NutritionAnalysisResponse } from '../types';

interface NutritionResultsProps {
  result: NutritionAnalysisResponse;
  onReset: () => void;
}

const NutritionResults: React.FC<NutritionResultsProps> = ({ result, onReset }) => {
  const getNutriScoreColor = (score?: string) => {
    if (!score) return 'bg-gray-100 text-gray-600';
    switch (score.toUpperCase()) {
      case 'A': return 'bg-green-100 text-green-800';
      case 'B': return 'bg-lime-100 text-lime-800';
      case 'C': return 'bg-yellow-100 text-yellow-800';
      case 'D': return 'bg-orange-100 text-orange-800';
      case 'E': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  const getHealthScoreColor = (score?: number) => {
    if (!score) return 'text-gray-600';
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    if (score >= 4) return 'text-orange-600';
    return 'text-red-600';
  };

  const formatNutrientValue = (value?: number, unit: string = 'g') => {
    if (value === undefined || value === null) return 'N/A';
    return `${value.toFixed(1)}${unit}`;
  };

  return (
    <div className="space-y-6">
      {/* Food Information Header */}
      <div className="card">
        <div className="card-header flex justify-between items-start">
          <div>
            <h3 className="text-xl font-bold text-gray-900">{result.food_name}</h3>
            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
              {result.brand && <span>Brand: {result.brand}</span>}
              <span>Category: {result.category}</span>
              {result.barcode_id && <span>Barcode: {result.barcode_id}</span>}
            </div>
          </div>
          <button
            onClick={onReset}
            className="btn-secondary"
          >
            New Scan
          </button>
        </div>
        
        <div className="card-body">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* Nutri-Score */}
              {result.nutri_score && (
                <div className="text-center">
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getNutriScoreColor(result.nutri_score)}`}>
                    Nutri-Score: {result.nutri_score}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Nutritional Quality</p>
                </div>
              )}
              
              {/* Glycemic Load Index */}
              {result.glycemic_load_index && (
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {result.glycemic_load_index.toFixed(1)}
                  </div>
                  <p className="text-xs text-gray-500">Glycemic Load</p>
                </div>
              )}
              
              {/* Overall Health Score */}
              {result.overall_health_score && (
                <div className="text-center">
                  <div className={`text-lg font-semibold ${getHealthScoreColor(result.overall_health_score)}`}>
                    {result.overall_health_score.toFixed(1)}/10
                  </div>
                  <p className="text-xs text-gray-500">Health Score</p>
                </div>
              )}
            </div>
            
            {/* Confidence Score */}
            <div className="text-right">
              <div className="text-sm text-gray-600">
                Confidence: {(result.confidence_score * 100).toFixed(0)}%
              </div>
              {result.processing_time_ms && (
                <div className="text-xs text-gray-500">
                  Processed in {result.processing_time_ms}ms
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Macronutrients */}
      <div className="card">
        <div className="card-header">
          <h4 className="text-lg font-semibold">Nutrition Facts</h4>
          <p className="text-sm text-gray-600">Per {result.macros.serving_size}</p>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {Math.round(result.macros.calories)}
              </div>
              <div className="text-sm text-gray-600">Calories</div>
            </div>
            
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {formatNutrientValue(result.macros.protein_g)}
              </div>
              <div className="text-sm text-gray-600">Protein</div>
            </div>
            
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {formatNutrientValue(result.macros.carbohydrates_g)}
              </div>
              <div className="text-sm text-gray-600">Carbs</div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {formatNutrientValue(result.macros.fat_g)}
              </div>
              <div className="text-sm text-gray-600">Fat</div>
            </div>
          </div>
          
          {/* Additional Nutrients */}
          {(result.macros.fiber_g || result.macros.sugar_g || result.macros.sodium_mg) && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h5 className="font-medium text-gray-900 mb-3">Additional Nutrients</h5>
              <div className="grid grid-cols-3 gap-4 text-sm">
                {result.macros.fiber_g && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Fiber:</span>
                    <span className="font-medium">{formatNutrientValue(result.macros.fiber_g)}</span>
                  </div>
                )}
                {result.macros.sugar_g && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sugar:</span>
                    <span className="font-medium">{formatNutrientValue(result.macros.sugar_g)}</span>
                  </div>
                )}
                {result.macros.sodium_mg && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Sodium:</span>
                    <span className="font-medium">{formatNutrientValue(result.macros.sodium_mg, 'mg')}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Health Remarks */}
      {result.health_remarks && result.health_remarks.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h4 className="text-lg font-semibold">Health Analysis</h4>
            <p className="text-sm text-gray-600">Based on your health conditions</p>
          </div>
          <div className="card-body space-y-4">
            {result.health_remarks.map((remark, index) => (
              <div
                key={index}
                className={`health-remark-${remark.severity}`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    {remark.severity === 'danger' && (
                      <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    )}
                    {remark.severity === 'warning' && (
                      <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    )}
                    {remark.severity === 'info' && (
                      <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-sm">{remark.condition}</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        remark.severity === 'danger' ? 'bg-red-100 text-red-800' :
                        remark.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {remark.severity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mt-1">{remark.message}</p>
                    {remark.recommendation && (
                      <p className="text-sm text-gray-600 mt-2 italic">
                        💡 {remark.recommendation}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Data Sources */}
      {result.data_sources && result.data_sources.length > 0 && (
        <div className="card">
          <div className="card-body">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>Data sources: {result.data_sources.join(', ')}</span>
              {result.scan_id && <span>Scan ID: #{result.scan_id}</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NutritionResults;
