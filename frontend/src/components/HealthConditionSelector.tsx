import React, { useState, useEffect } from 'react';
import { HealthCondition } from '../types';
import FoodScannerAPI from '../services/api';

interface HealthConditionSelectorProps {
  selectedConditions: HealthCondition[];
  onAdd: (condition: HealthCondition) => void;
  onRemove: (conditionName: string) => void;
}

// Fallback conditions if API fails
const FALLBACK_CONDITIONS: HealthCondition[] = [
  { name: 'Diabetes', severity: 'moderate', description: 'Blood sugar management required' },
  { name: 'Hypertension', severity: 'moderate', description: 'High blood pressure' },
  { name: 'Heart Disease', severity: 'severe', description: 'Cardiovascular health concerns' },
  { name: 'Nut Allergy', severity: 'severe', description: 'Allergic to nuts and tree nuts' },
  { name: 'Gluten Intolerance', severity: 'moderate', description: 'Cannot consume gluten' },
  { name: 'Lactose Intolerance', severity: 'mild', description: 'Cannot digest lactose' },
  { name: 'High Cholesterol', severity: 'moderate', description: 'Elevated cholesterol levels' },
  { name: 'Kidney Disease', severity: 'severe', description: 'Kidney function impairment' },
];

const HealthConditionSelector: React.FC<HealthConditionSelectorProps> = ({
  selectedConditions,
  onAdd,
  onRemove,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [customCondition, setCustomCondition] = useState('');
  const [availableConditions, setAvailableConditions] = useState<HealthCondition[]>(FALLBACK_CONDITIONS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealthConditions = async () => {
      try {
        setLoading(true);
        const response = await FoodScannerAPI.getHealthConditions();
        if (response.health_conditions && response.health_conditions.length > 0) {
          setAvailableConditions(response.health_conditions);
        }
        setError(null);
      } catch (err) {
        console.error('Failed to fetch health conditions:', err);
        setError('Failed to load health conditions from server. Using defaults.');
        // Keep fallback conditions
      } finally {
        setLoading(false);
      }
    };

    fetchHealthConditions();
  }, []);

  const handleAddCondition = (condition: HealthCondition) => {
    const exists = selectedConditions.some(c => c.name.toLowerCase() === condition.name.toLowerCase());
    if (!exists) {
      onAdd(condition);
    }
  };

  const handleAddCustomCondition = () => {
    if (customCondition.trim()) {
      const condition: HealthCondition = {
        name: customCondition.trim(),
        severity: 'moderate',
        description: 'Custom health condition'
      };
      handleAddCondition(condition);
      setCustomCondition('');
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'mild': return 'bg-green-100 text-green-800';
      case 'moderate': return 'bg-yellow-100 text-yellow-800';
      case 'severe': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Health Conditions</h3>
            <p className="text-sm text-gray-600">
              Select your health conditions for personalized nutrition analysis
            </p>
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {isExpanded ? 'Collapse' : 'Manage'}
          </button>
        </div>
      </div>

      {/* Selected Conditions Display */}
      <div className="px-6 py-4">
        {selectedConditions.length > 0 ? (
          <div className="flex flex-wrap gap-2 mb-4">
            {selectedConditions.map((condition) => (
              <div
                key={condition.name}
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(condition.severity)}`}
              >
                <span>{condition.name}</span>
                <button
                  onClick={() => onRemove(condition.name)}
                  className="ml-2 hover:bg-black hover:bg-opacity-10 rounded-full p-1"
                >
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm mb-4">
            No health conditions selected. Add conditions below for personalized analysis.
          </p>
        )}

        {/* Expanded Section */}
        {isExpanded && (
          <div className="space-y-4 border-t border-gray-200 pt-4">
            {/* Common Conditions */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Common Conditions</h4>
              {loading && (
                <div className="text-center py-4">
                  <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                  <p className="mt-2 text-sm text-gray-600">Loading health conditions...</p>
                </div>
              )}
              {error && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3 mb-4">
                  <p className="text-sm text-yellow-800">{error}</p>
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {availableConditions.map((condition) => {
                  const isSelected = selectedConditions.some(
                    c => c.name.toLowerCase() === condition.name.toLowerCase()
                  );
                  return (
                    <button
                      key={condition.name}
                      onClick={() => handleAddCondition(condition)}
                      disabled={isSelected}
                      className={`text-left p-3 rounded-lg border transition-colors ${
                        isSelected
                          ? 'bg-gray-50 border-gray-200 text-gray-400 cursor-not-allowed'
                          : 'bg-white border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-sm">{condition.name}</div>
                          <div className="text-xs text-gray-500">{condition.description}</div>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(condition.severity)}`}>
                          {condition.severity}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Custom Condition Input */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Add Custom Condition</h4>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={customCondition}
                  onChange={(e) => setCustomCondition(e.target.value)}
                  placeholder="Enter custom health condition"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleAddCustomCondition()}
                />
                <button
                  onClick={handleAddCustomCondition}
                  disabled={!customCondition.trim()}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Add
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HealthConditionSelector;
