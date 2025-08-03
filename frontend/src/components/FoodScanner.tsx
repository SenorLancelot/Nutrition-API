import React, { useState, useRef, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import Webcam from 'react-webcam';
import { FoodScannerAPI, handleApiError, validateImageFile } from '../services/api';
import { FoodScannerProps, ScanState, CameraState, NutritionAnalysisResponse } from '../types';
import NutritionResults from './NutritionResults';
import HealthConditionSelector from './HealthConditionSelector';
import BarcodeScanner from './BarcodeScanner';

const FoodScanner: React.FC<FoodScannerProps> = ({
  healthConditions,
  onAddHealthCondition,
  onRemoveHealthCondition,
}) => {
  const [scanState, setScanState] = useState<ScanState>({
    isScanning: false,
    scanType: null,
    result: null,
    error: null,
    loading: false,
  });

  const [cameraState, setCameraState] = useState<CameraState>({
    isOpen: false,
    facingMode: 'environment',
    hasPermission: false,
  });

  const [textInput, setTextInput] = useState('');
  const [barcodeInput, setBarcodeInput] = useState('');
  const [servingSize, setServingSize] = useState('100g');
  const [showBarcodeScanner, setShowBarcodeScanner] = useState(false);
  const webcamRef = useRef<Webcam>(null);

  // Handle file upload via drag & drop or file picker
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    const validation = validateImageFile(file);
    
    if (!validation.valid) {
      setScanState(prev => ({ ...prev, error: validation.error || 'Invalid file' }));
      return;
    }

    await handleImageScan(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    multiple: false,
    maxSize: 5 * 1024 * 1024, // 5MB
  });

  // Handle image scanning
  const handleImageScan = async (file: File) => {
    setScanState(prev => ({ 
      ...prev, 
      loading: true, 
      error: null, 
      scanType: 'image' 
    }));

    try {
      const result = await FoodScannerAPI.scanAnalyze({
        image: file,
        image_type: 'food',
        health_conditions: healthConditions.map(c => c.name),
        serving_size: servingSize,
      });

      setScanState(prev => ({
        ...prev,
        loading: false,
        result,
        isScanning: true,
      }));
    } catch (error) {
      setScanState(prev => ({
        ...prev,
        loading: false,
        error: handleApiError(error),
      }));
    }
  };

  // Handle camera capture
  const handleCameraCapture = useCallback(async () => {
    if (!webcamRef.current) return;

    const imageSrc = webcamRef.current.getScreenshot();
    if (!imageSrc) return;

    // Convert base64 to blob
    const response = await fetch(imageSrc);
    const blob = await response.blob();
    const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });

    setCameraState(prev => ({ ...prev, isOpen: false }));
    await handleImageScan(file);
  }, []);

  // Handle text input scanning
  const handleTextScan = async () => {
    if (!textInput.trim()) return;

    setScanState(prev => ({ 
      ...prev, 
      loading: true, 
      error: null, 
      scanType: 'text' 
    }));

    try {
      const result = await FoodScannerAPI.scanAnalyze({
        food_name: textInput.trim(),
        health_conditions: healthConditions.map(c => c.name),
        serving_size: servingSize,
      });

      setScanState(prev => ({
        ...prev,
        loading: false,
        result,
        isScanning: true,
      }));
    } catch (error) {
      setScanState(prev => ({
        ...prev,
        loading: false,
        error: handleApiError(error),
      }));
    }
  };

  // Handle barcode scanning
  const handleBarcodeScan = async () => {
    if (!barcodeInput.trim()) return;

    setScanState(prev => ({ 
      ...prev, 
      loading: true, 
      error: null, 
      scanType: 'barcode' 
    }));

    try {
      const result = await FoodScannerAPI.scanAnalyze({
        barcode_id: barcodeInput.trim(),
        health_conditions: healthConditions.map(c => c.name),
        serving_size: servingSize,
      });

      setScanState(prev => ({
        ...prev,
        loading: false,
        result,
        isScanning: true,
      }));
    } catch (error) {
      setScanState(prev => ({
        ...prev,
        loading: false,
        error: handleApiError(error),
      }));
    }
  };

  // Handle camera barcode detection
  const handleBarcodeDetected = async (barcode: string) => {
    setBarcodeInput(barcode);
    setShowBarcodeScanner(false);
    
    // Automatically scan the detected barcode
    setScanState(prev => ({ 
      ...prev, 
      loading: true, 
      error: null, 
      scanType: 'barcode' 
    }));

    try {
      const result = await FoodScannerAPI.scanAnalyze({
        barcode_id: barcode,
        health_conditions: healthConditions.map(c => c.name),
        serving_size: servingSize,
      });

      setScanState(prev => ({
        ...prev,
        loading: false,
        result,
        isScanning: true,
      }));
    } catch (error) {
      setScanState(prev => ({
        ...prev,
        loading: false,
        error: handleApiError(error),
      }));
    }
  };

  // Reset scan state
  const resetScan = () => {
    setScanState({
      isScanning: false,
      scanType: null,
      result: null,
      error: null,
      loading: false,
    });
    setTextInput('');
    setBarcodeInput('');
  };

  // Toggle camera
  const toggleCamera = () => {
    setCameraState(prev => ({ ...prev, isOpen: !prev.isOpen }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Food Scanner</h2>
        <p className="text-gray-600">
          Upload an image, scan a barcode, or enter food name to get nutritional analysis
        </p>
      </div>

      {/* Health Conditions Selector */}
      <HealthConditionSelector
        selectedConditions={healthConditions}
        onAdd={onAddHealthCondition}
        onRemove={onRemoveHealthCondition}
      />

      {/* Serving Size Input */}
      <div className="card">
        <div className="card-body">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Serving Size
          </label>
          <select
            value={servingSize}
            onChange={(e) => setServingSize(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="100g">100g</option>
            <option value="1 cup">1 cup</option>
            <option value="1 serving">1 serving</option>
            <option value="1 piece">1 piece</option>
            <option value="1 slice">1 slice</option>
          </select>
        </div>
      </div>

      {/* Scanning Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Image Upload */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Upload Image</h3>
          </div>
          <div className="card-body">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <div className="space-y-2">
                <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                  <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <p className="text-sm text-gray-600">
                  {isDragActive ? 'Drop the image here' : 'Drag & drop an image, or click to select'}
                </p>
                <p className="text-xs text-gray-500">PNG, JPG, WebP up to 5MB</p>
              </div>
            </div>
          </div>
        </div>

        {/* Camera Capture */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Camera</h3>
          </div>
          <div className="card-body">
            {!cameraState.isOpen ? (
              <button
                onClick={toggleCamera}
                className="w-full btn-primary"
                disabled={scanState.loading}
              >
                Open Camera
              </button>
            ) : (
              <div className="space-y-4">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  videoConstraints={{
                    facingMode: cameraState.facingMode
                  }}
                  className="w-full rounded-lg"
                />
                <div className="flex space-x-2">
                  <button
                    onClick={handleCameraCapture}
                    className="flex-1 btn-primary"
                    disabled={scanState.loading}
                  >
                    Capture
                  </button>
                  <button
                    onClick={toggleCamera}
                    className="flex-1 btn-secondary"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Text Input */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Enter Food Name</h3>
          </div>
          <div className="card-body space-y-4">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="e.g., Apple, Chicken breast, etc."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && handleTextScan()}
            />
            <button
              onClick={handleTextScan}
              disabled={!textInput.trim() || scanState.loading}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Analyze Food
            </button>
          </div>
        </div>
      </div>

      {/* Barcode Input */}
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-semibold">Barcode Scanner</h3>
        </div>
        <div className="card-body space-y-4">
          {/* Camera Barcode Scanning */}
          <div className="flex space-x-2">
            <button
              onClick={() => setShowBarcodeScanner(true)}
              disabled={scanState.loading}
              className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Scan with Camera</span>
            </button>
          </div>
          
          {/* Manual Barcode Input */}
          <div className="border-t pt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Or enter barcode manually:
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={barcodeInput}
                onChange={(e) => setBarcodeInput(e.target.value)}
                placeholder="Enter barcode number (e.g., 1234567890123)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onKeyPress={(e) => e.key === 'Enter' && handleBarcodeScan()}
              />
              <button
                onClick={handleBarcodeScan}
                disabled={!barcodeInput.trim() || scanState.loading}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Analyze
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {scanState.loading && (
        <div className="card">
          <div className="card-body text-center py-8">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-gray-600">Analyzing food...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {scanState.error && (
        <div className="card border-red-200 bg-red-50">
          <div className="card-body">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-700 font-medium">Error</span>
            </div>
            <p className="text-red-600 mt-2">{scanState.error}</p>
            <button
              onClick={resetScan}
              className="mt-3 btn-secondary"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {scanState.result && (
        <NutritionResults
          result={scanState.result}
          onReset={resetScan}
        />
      )}

      {/* Barcode Scanner Modal */}
      <BarcodeScanner
        isOpen={showBarcodeScanner}
        onBarcodeDetected={handleBarcodeDetected}
        onClose={() => setShowBarcodeScanner(false)}
      />
    </div>
  );
};

export default FoodScanner;
