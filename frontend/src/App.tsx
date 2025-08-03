import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { HealthCondition } from './types';
import { Header, FoodScanner, ScanHistory, HealthConditionSelector } from './components';

function App() {
  const [healthConditions, setHealthConditions] = useState<HealthCondition[]>([]);

  const addHealthCondition = (condition: HealthCondition) => {
    setHealthConditions(prev => [...prev, condition]);
  };

  const removeHealthCondition = (conditionName: string) => {
    setHealthConditions(prev => prev.filter(c => c.name !== conditionName));
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route 
              path="/" 
              element={
                <FoodScanner 
                  healthConditions={healthConditions}
                  onAddHealthCondition={addHealthCondition}
                  onRemoveHealthCondition={removeHealthCondition}
                />
              } 
            />
            <Route path="/history" element={<ScanHistory />} />
            <Route 
              path="/health" 
              element={
                <div className="max-w-4xl mx-auto space-y-6">
                  <div className="text-center">
                    <h2 className="text-3xl font-bold text-gray-900 mb-2">Health Conditions</h2>
                    <p className="text-gray-600">
                      Manage your health conditions for personalized nutrition analysis
                    </p>
                  </div>
                  <HealthConditionSelector
                    selectedConditions={healthConditions}
                    onAdd={addHealthCondition}
                    onRemove={removeHealthCondition}
                  />
                </div>
              } 
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
