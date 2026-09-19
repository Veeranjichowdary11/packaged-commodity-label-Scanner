'use client';

import React, { useState } from 'react';
import { Calculator, TrendingUp, TrendingDown, AlertTriangle, ShieldCheck, Tag } from 'lucide-react';

interface UspCalculatorProps {
  extractedFields: any;
}

export default function UspCalculator({ extractedFields }: UspCalculatorProps) {
  const mrpObj = extractedFields?.mrp;
  const netQtyObj = extractedFields?.net_quantity;

  const mrp = typeof mrpObj === 'object' ? mrpObj?.value : parseFloat(mrpObj) || 0;
  const qty = typeof netQtyObj === 'object' ? netQtyObj?.value : parseFloat(netQtyObj) || 0;
  const unit = (typeof netQtyObj === 'object' ? netQtyObj?.unit : 'g') || 'g';

  if (!mrp || !qty) return null;

  // Compute unit sale price (USP) per standard base unit (per gram, per ml, per kg, per L)
  let baseUnit = 'g';
  let perUnitCost = 0;
  let standardUnitName = '100g';
  let costPer100 = 0;

  const unitLower = String(unit).toLowerCase();
  if (unitLower.includes('kg') || unitLower.includes('kilo')) {
    const totalGrams = qty * 1000;
    perUnitCost = mrp / totalGrams;
    costPer100 = perUnitCost * 100;
    standardUnitName = '100 g';
  } else if (unitLower.includes('l') || unitLower.includes('litre') || unitLower.includes('liter')) {
    const totalMl = qty * 1000;
    perUnitCost = mrp / totalMl;
    costPer100 = perUnitCost * 100;
    standardUnitName = '100 ml';
  } else if (unitLower.includes('ml')) {
    perUnitCost = mrp / qty;
    costPer100 = perUnitCost * 100;
    standardUnitName = '100 ml';
  } else {
    // grams
    perUnitCost = mrp / qty;
    costPer100 = perUnitCost * 100;
    standardUnitName = '100 g';
  }

  // Estimated average category benchmark (indicative for FMCG)
  const isHighValue = costPer100 > 120;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-4">
        <div className="flex items-center gap-2">
          <Calculator className="h-5 w-5 text-primary-600" />
          <div>
            <h3 className="font-bold text-gray-900 text-base">Unit Sale Price (USP) & Shrinkflation Radar</h3>
            <p className="text-xs text-gray-500">Statutory Unit Sale Price mandate under Legal Metrology Rule 6(1)(e)</p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 flex items-center gap-1">
          <Tag className="h-3 w-3" /> Mandatory USP
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3 text-xs">
        <div className="bg-gray-50 rounded-lg p-3">
          <span className="text-gray-500 font-medium block">Declared Pack Details</span>
          <p className="font-bold text-gray-900 text-sm mt-0.5">₹{mrp.toFixed(2)} for {qty} {unit}</p>
          <span className="text-[10px] text-gray-400 mt-0.5 block">Total Net Volume</span>
        </div>

        <div className="bg-primary-50 rounded-lg p-3 border border-primary-100">
          <span className="text-primary-700 font-medium block">Calculated Unit Sale Price</span>
          <p className="font-extrabold text-primary-900 text-base mt-0.5">₹{costPer100.toFixed(2)} <span className="text-xs font-normal text-primary-700">/ {standardUnitName}</span></p>
          <span className="text-[10px] text-primary-600 mt-0.5 block">₹{perUnitCost.toFixed(3)} per {unitLower.includes('l') || unitLower.includes('ml') ? 'ml' : 'g'}</span>
        </div>

        <div className="bg-gray-50 rounded-lg p-3">
          <span className="text-gray-500 font-medium block">Value Assessment</span>
          <p className="font-bold text-emerald-700 text-sm mt-0.5 flex items-center gap-1">
            <ShieldCheck className="h-4 w-4" /> Standard Retail Tier
          </p>
          <span className="text-[10px] text-gray-400 mt-0.5 block">Transparent Unit Pricing</span>
        </div>
      </div>

      <div className="p-2.5 bg-gray-50 rounded-lg text-xs text-gray-600 flex items-center justify-between">
        <span><b>Consumer Tip:</b> Always check Unit Sale Price (₹/100g) across package sizes to avoid hidden pack downsizing (shrinkflation).</span>
      </div>
    </div>
  );
}
