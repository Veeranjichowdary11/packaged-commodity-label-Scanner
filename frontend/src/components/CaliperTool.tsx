'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Ruler, Check, RotateCcw, Crosshair, HelpCircle, ShieldCheck } from 'lucide-react';

interface CaliperToolProps {
  imageUrl: string;
  onApplyMeasurement?: (mm: number, notes: string) => void;
  onClose?: () => void;
  statutoryMinMm?: number;
}

export default function CaliperTool({
  imageUrl,
  onApplyMeasurement,
  onClose,
  statutoryMinMm = 2.0,
}: CaliperToolProps) {
  // Mode: 'measure' or 'calibrate'
  const [mode, setMode] = useState<'measure' | 'calibrate'>('measure');

  // Calibration state: pixels per millimeter
  const [pixelsPerMm, setPixelsPerMm] = useState<number>(11.8); // Default ~300 DPI (300/25.4)
  const [calibrationPreset, setCalibrationPreset] = useState<'default' | 'coin' | 'card' | 'custom'>('default');
  const [customRefMm, setCustomRefMm] = useState<number>(25);

  // Caliper Pin Coordinates (relative percentage 0 - 100 within container)
  const [pin1, setPin1] = useState<{ x: number; y: number }>({ x: 45, y: 40 });
  const [pin2, setPin2] = useState<{ x: number; y: number }>({ x: 45, y: 55 });
  const [activePin, setActivePin] = useState<'pin1' | 'pin2' | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const [containerDim, setContainerDim] = useState<{ width: number; height: number }>({ width: 500, height: 400 });

  useEffect(() => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setContainerDim({ width: rect.width, height: rect.height });
    }
  }, []);

  // Calculate pixel distance and converted millimeter distance
  const p1_px = { x: (pin1.x / 100) * containerDim.width, y: (pin1.y / 100) * containerDim.height };
  const p2_px = { x: (pin2.x / 100) * containerDim.width, y: (pin2.y / 100) * containerDim.height };
  
  const distancePx = Math.sqrt(Math.pow(p2_px.x - p1_px.x, 2) + Math.pow(p2_px.y - p1_px.y, 2));
  const measuredMm = Math.max(0.2, parseFloat((distancePx / pixelsPerMm).toFixed(2)));

  const handlePointerDown = (pin: 'pin1' | 'pin2') => (e: React.PointerEvent) => {
    e.stopPropagation();
    setActivePin(pin);
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!activePin || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.min(98, Math.max(2, ((e.clientX - rect.left) / rect.width) * 100));
    const y = Math.min(98, Math.max(2, ((e.clientY - rect.top) / rect.height) * 100));

    if (activePin === 'pin1') {
      setPin1({ x, y });
    } else {
      setPin2({ x, y });
    }
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (activePin) {
      try {
        (e.target as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {}
      setActivePin(null);
    }
  };

  const calibrateWithCurrentSpan = (targetMm: number) => {
    if (distancePx > 5) {
      const newPpm = distancePx / targetMm;
      setPixelsPerMm(newPpm);
      setMode('measure');
    }
  };

  const isCompliant = measuredMm >= statutoryMinMm;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-lg animate-fadeIn">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between pb-3 border-b border-gray-100 mb-3 gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-primary-100 text-primary-700">
            <Ruler className="h-4 w-4" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-gray-900">Interactive Visual Caliper & Scale Tool</h4>
            <p className="text-[11px] text-gray-500">Drag crosshairs over text numerals to measure physical font height</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setMode(mode === 'measure' ? 'calibrate' : 'measure')}
            className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
              mode === 'calibrate'
                ? 'bg-amber-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {mode === 'calibrate' ? 'Exit Calibration' : 'Calibrate Scale'}
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="text-xs text-gray-400 hover:text-gray-600 font-bold px-2 py-1"
            >
              &times;
            </button>
          )}
        </div>
      </div>

      {/* Calibration Controls if in Calibrate mode */}
      {mode === 'calibrate' && (
        <div className="mb-3 p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900">
          <p className="font-bold flex items-center gap-1 mb-1">
            <Crosshair className="h-3.5 w-3.5 text-amber-700" /> Reference Target Scale Calibration:
          </p>
          <p className="text-[11px] text-amber-800 mb-2">
            Align Pin 1 & Pin 2 across a reference object in the photo (e.g. ₹5 coin = 25mm, Standard Card = 85.6mm) and click calibrate:
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => calibrateWithCurrentSpan(25)}
              className="px-2.5 py-1 bg-amber-700 text-white font-bold rounded text-[11px] hover:bg-amber-800"
            >
              Set to ₹5 Coin (25 mm)
            </button>
            <button
              type="button"
              onClick={() => calibrateWithCurrentSpan(85.6)}
              className="px-2.5 py-1 bg-amber-700 text-white font-bold rounded text-[11px] hover:bg-amber-800"
            >
              Set to Card (85.6 mm)
            </button>
            <div className="flex items-center gap-1">
              <input
                type="number"
                value={customRefMm}
                onChange={(e) => setCustomRefMm(parseFloat(e.target.value) || 10)}
                className="w-16 p-1 border rounded text-xs bg-white"
              />
              <button
                type="button"
                onClick={() => calibrateWithCurrentSpan(customRefMm)}
                className="px-2 py-1 bg-gray-800 text-white font-bold rounded text-[11px]"
              >
                Set mm
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Interactive Caliper Workspace */}
      <div
        ref={containerRef}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        className="relative w-full h-80 sm:h-96 rounded-lg bg-gray-900 overflow-hidden border border-gray-300 select-none cursor-crosshair touch-none"
      >
        <img
          src={imageUrl}
          alt="Product Panel for Caliper"
          className="w-full h-full object-contain pointer-events-none"
        />

        {/* SVG Connecting Caliper Line */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          <line
            x1={`${pin1.x}%`}
            y1={`${pin1.y}%`}
            x2={`${pin2.x}%`}
            y2={`${pin2.y}%`}
            stroke={isCompliant ? '#10B981' : '#F59E0B'}
            strokeWidth="2.5"
            strokeDasharray="4 2"
          />
          {/* Caliper Jaw Ticks */}
          <circle cx={`${pin1.x}%`} cy={`${pin1.y}%`} r="4" fill="#3B82F6" />
          <circle cx={`${pin2.x}%`} cy={`${pin2.y}%`} r="4" fill="#EF4444" />
        </svg>

        {/* Pin 1 Draggable Crosshair */}
        <div
          style={{ left: `${pin1.x}%`, top: `${pin1.y}%` }}
          onPointerDown={handlePointerDown('pin1')}
          className="absolute -translate-x-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center cursor-grab active:cursor-grabbing z-20"
        >
          <div className="w-5 h-5 rounded-full bg-blue-600 border-2 border-white shadow-lg flex items-center justify-center text-[9px] text-white font-bold">
            1
          </div>
        </div>

        {/* Pin 2 Draggable Crosshair */}
        <div
          style={{ left: `${pin2.x}%`, top: `${pin2.y}%` }}
          onPointerDown={handlePointerDown('pin2')}
          className="absolute -translate-x-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center cursor-grab active:cursor-grabbing z-20"
        >
          <div className="w-5 h-5 rounded-full bg-red-600 border-2 border-white shadow-lg flex items-center justify-center text-[9px] text-white font-bold">
            2
          </div>
        </div>

        {/* Live Measurement Floating Pill */}
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-gray-950/90 backdrop-blur-md px-4 py-2 rounded-full border border-white/20 text-white shadow-2xl flex items-center gap-3 z-30">
          <div className="text-center">
            <span className="text-[10px] text-gray-400 block font-medium">MEASURED HEIGHT</span>
            <span className="text-base font-extrabold text-white font-mono tracking-tight">{measuredMm} mm</span>
          </div>
          <div className="h-6 w-[1px] bg-white/20" />
          <div className="text-left">
            <span className="text-[10px] text-gray-400 block font-medium">STATUTORY MIN</span>
            <span className={`text-xs font-bold ${isCompliant ? 'text-emerald-400' : 'text-amber-400'}`}>
              &ge; {statutoryMinMm} mm ({isCompliant ? 'PASS' : 'REVIEW'})
            </span>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex flex-wrap items-center justify-between mt-3 pt-3 border-t border-gray-100 gap-2">
        <p className="text-xs text-gray-500">
          Scale: <span className="font-mono font-semibold">{pixelsPerMm.toFixed(1)} px/mm</span> ({Math.round(distancePx)} px spanned)
        </p>

        {onApplyMeasurement && (
          <button
            type="button"
            onClick={() => onApplyMeasurement(measuredMm, `Measured with On-Screen Caliper (${measuredMm} mm vs statutory min ${statutoryMinMm} mm)`)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary-600 text-white rounded-lg text-xs font-bold hover:bg-primary-700 transition-colors shadow-sm"
          >
            <Check className="h-3.5 w-3.5" /> Apply Measurement to Review
          </button>
        )}
      </div>
    </div>
  );
}
