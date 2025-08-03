import React, { useState } from 'react';
import { FoodScannerAPI } from '../services/api';
import { HealthCondition } from '../types';

interface CustomHealthConditionFormProps {
  onConditionCreated: (condition: HealthCondition) => void;
  onCancel: () => void;
}

const CustomHealthConditionForm: React.FC<CustomHealthConditionFormProps> = ({
  onConditionCreated,
  onCancel
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    severity: 'moderate' as 'mild' | 'moderate' | 'severe',
    warning_template: '',
    recommendation_template: ''
  });

  const [restrictions, setRestrictions] = useState<Array<{ key: string; value: string; type: 'max' | 'min' | 'avoid' }>>([
    { key: '', value: '', type: 'max' }
  ]);

  const [targets, setTargets] = useState<Array<{ key: string; value: string; type: 'max' | 'min' }>>([
    { key: '', value: '', type: 'min' }
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const addRestriction = () => {
    setRestrictions(prev => [...prev, { key: '', value: '', type: 'max' }]);
  };

  const removeRestriction = (index: number) => {
    setRestrictions(prev => prev.filter((_, i) => i !== index));
  };

  const updateRestriction = (index: number, field: string, value: string) => {
    setRestrictions(prev => prev.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    ));
  };

  const addTarget = () => {
    setTargets(prev => [...prev, { key: '', value: '', type: 'min' }]);
  };

  const removeTarget = (index: number) => {
    setTargets(prev => prev.filter((_, i) => i !== index));
  };

  const updateTarget = (index: number, field: string, value: string) => {
    setTargets(prev => prev.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    ));
  };

  const buildDietaryRestrictions = () => {
    const result: Record<string, any> = {};
    
    restrictions.forEach(restriction => {
      if (restriction.key && restriction.value) {
        if (restriction.type === 'avoid') {
          if (!result.avoid_ingredients) result.avoid_ingredients = [];
          result.avoid_ingredients.push(restriction.value);
        } else {
          const key = `${restriction.type}_${restriction.key}`;
          const numValue = parseFloat(restriction.value);
          if (!isNaN(numValue)) {
            result[key] = numValue;
          }
        }
      }
    });
    
    return result;
  };

  const buildNutritionalTargets = () => {
    const result: Record<string, any> = {};
    
    targets.forEach(target => {
      if (target.key && target.value) {
        const key = `${target.type}_${target.key}`;
        const numValue = parseFloat(target.value);
        if (!isNaN(numValue)) {
          result[key] = numValue;
        }
      }
    });
    
    return result;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Validate required fields
      if (!formData.name.trim() || !formData.description.trim()) {
        throw new Error('Name and description are required');
      }

      const conditionData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        severity: formData.severity,
        dietary_restrictions: buildDietaryRestrictions(),
        nutritional_targets: buildNutritionalTargets(),
        warning_template: formData.warning_template.trim(),
        recommendation_template: formData.recommendation_template.trim()
      };

      const response = await FoodScannerAPI.createHealthCondition(conditionData);
      onConditionCreated(response.condition);
    } catch (err: any) {
      setError(err.response?.data?.message || err.message || 'Failed to create health condition');
    } finally {
      setLoading(false);
    }
  };

  const commonNutrients = [
    'sugar_g', 'sodium_mg', 'saturated_fat_g', 'cholesterol_mg', 'carbohydrates_g',
    'protein_g', 'fiber_g', 'potassium_mg', 'calcium_mg', 'iron_mg', 'vitamin_c_mg'
  ];

  const commonIngredients = [
    'gluten', 'dairy', 'nuts', 'shellfish', 'eggs', 'soy', 'wheat', 'lactose'
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Create Custom Health Condition</h2>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Condition Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., My Custom Condition"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Severity Level
                </label>
                <select
                  name="severity"
                  value={formData.severity}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="mild">Mild</option>
                  <option value="moderate">Moderate</option>
                  <option value="severe">Severe</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description *
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Describe the health condition and its dietary requirements..."
                required
              />
            </div>

            {/* Dietary Restrictions */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium text-gray-900">Dietary Restrictions</h3>
                <button
                  type="button"
                  onClick={addRestriction}
                  className="px-3 py-1 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
                >
                  Add Restriction
                </button>
              </div>

              <div className="space-y-3">
                {restrictions.map((restriction, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <select
                      value={restriction.type}
                      onChange={(e) => updateRestriction(index, 'type', e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      <option value="max">Max</option>
                      <option value="min">Min</option>
                      <option value="avoid">Avoid</option>
                    </select>

                    {restriction.type === 'avoid' ? (
                      <select
                        value={restriction.value}
                        onChange={(e) => updateRestriction(index, 'value', e.target.value)}
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      >
                        <option value="">Select ingredient to avoid</option>
                        {commonIngredients.map(ingredient => (
                          <option key={ingredient} value={ingredient}>{ingredient}</option>
                        ))}
                      </select>
                    ) : (
                      <>
                        <select
                          value={restriction.key}
                          onChange={(e) => updateRestriction(index, 'key', e.target.value)}
                          className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                        >
                          <option value="">Select nutrient</option>
                          {commonNutrients.map(nutrient => (
                            <option key={nutrient} value={nutrient}>{nutrient.replace('_', ' ')}</option>
                          ))}
                        </select>
                        <input
                          type="number"
                          value={restriction.value}
                          onChange={(e) => updateRestriction(index, 'value', e.target.value)}
                          placeholder="Value"
                          className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                          step="0.1"
                        />
                      </>
                    )}

                    <button
                      type="button"
                      onClick={() => removeRestriction(index)}
                      className="text-red-500 hover:text-red-700 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Nutritional Targets */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium text-gray-900">Nutritional Targets</h3>
                <button
                  type="button"
                  onClick={addTarget}
                  className="px-3 py-1 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm"
                >
                  Add Target
                </button>
              </div>

              <div className="space-y-3">
                {targets.map((target, index) => (
                  <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <select
                      value={target.type}
                      onChange={(e) => updateTarget(index, 'type', e.target.value)}
                      className="px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      <option value="min">Min</option>
                      <option value="max">Max</option>
                    </select>

                    <select
                      value={target.key}
                      onChange={(e) => updateTarget(index, 'key', e.target.value)}
                      className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                    >
                      <option value="">Select nutrient</option>
                      {commonNutrients.map(nutrient => (
                        <option key={nutrient} value={nutrient}>{nutrient.replace('_', ' ')}</option>
                      ))}
                    </select>

                    <input
                      type="number"
                      value={target.value}
                      onChange={(e) => updateTarget(index, 'value', e.target.value)}
                      placeholder="Value"
                      className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
                      step="0.1"
                    />

                    <button
                      type="button"
                      onClick={() => removeTarget(index)}
                      className="text-red-500 hover:text-red-700 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Templates */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Warning Template (Optional)
                </label>
                <textarea
                  name="warning_template"
                  value={formData.warning_template}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Template for warning messages (use {nutrient} as placeholder)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Recommendation Template (Optional)
                </label>
                <textarea
                  name="recommendation_template"
                  value={formData.recommendation_template}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Template for recommendation messages"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading ? 'Creating...' : 'Create Health Condition'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CustomHealthConditionForm;
