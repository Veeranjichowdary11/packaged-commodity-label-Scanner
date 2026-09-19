'use client';

import React, { useState } from 'react';
import { ShieldAlert, Copy, ExternalLink, Check, Download, MapPin, QrCode } from 'lucide-react';
import toast from 'react-hot-toast';

interface ComplaintDossierModalProps {
  scan: any;
  onClose: () => void;
}

export default function ComplaintDossierModal({ scan, onClose }: ComplaintDossierModalProps) {
  const [copied, setCopied] = useState(false);

  const prodName = scan.extracted_fields?.common_name || 'Packaged Commodity';
  const mrpVal = scan.extracted_fields?.mrp?.value ? `₹${scan.extracted_fields.mrp.value}` : 'N/A';
  const storeName = scan.store_name || 'Retail Establishment';
  const storeAddr = scan.store_address || 'Unspecified Store Location';
  const barcode = scan.barcode_detected || 'N/A';
  const violationCount = scan.violations?.length || 0;

  const violationsText = (scan.violations || [])
    .map((v: any, i: number) => `${i + 1}. [${v.rule_name}] - ${v.description} (Ref: ${v.section_reference})`)
    .join('\n');

  const complaintText = `To: National Consumer Helpline (NCH) / INGRAM Portal
Department of Consumer Affairs, Government of India

SUBJECT: Consumer Complaint Regarding Violation of Legal Metrology (Packaged Commodities) Rules, 2011

Respected Authority,

I wish to report a non-compliant packaged commodity sold in violation of the Legal Metrology (Packaged Commodities) Rules, 2011 and Consumer Protection Act, 2019.

PRODUCT & EVIDENCE DETAILS:
- Product Name: ${prodName}
- Barcode (GTIN): ${barcode}
- Scanned Declared MRP: ${mrpVal}
- Retailer / Store Name: ${storeName}
- Store Address: ${storeAddr}
${scan.latitude && scan.longitude ? `- GPS Coordinates: ${scan.latitude}, ${scan.longitude}` : ''}
- Inspection Reference ID: JANCH-SCAN-${scan.id}
- Date & Time: ${new Date(scan.created_at).toLocaleString()}

DETECTED CONTRAVENTIONS (${violationCount} items):
${violationsText || 'Missing mandatory packaging declarations and/or price discrepancy.'}

I request the Department of Consumer Affairs to kindly inspect the retail establishment and take appropriate legal action under Section 36 of the Legal Metrology Act, 2009.

Digital Evidence Archive: Generated via Janch National Compliance Portal.`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(complaintText);
    setCopied(true);
    toast.success('Complaint dossier copied to clipboard!');
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-gray-100 max-h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-red-100 text-red-700">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900 text-lg">National Consumer Helpline (NCH) Grievance Dossier</h3>
              <p className="text-xs text-gray-500">Department of Consumer Affairs &bull; INGRAM Portal Integration</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 font-bold text-xl px-2"
          >
            &times;
          </button>
        </div>

        {/* Quick summary banner */}
        <div className="my-4 p-3 bg-red-50 rounded-xl border border-red-200 text-xs text-red-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPin className="h-4 w-4 text-red-600 shrink-0" />
            <span>Store: <b>{storeName}</b> &bull; {violationCount} Violations Recorded</span>
          </div>
          <span className="font-mono font-bold bg-white px-2 py-0.5 rounded border border-red-200">
            Scan #{scan.id}
          </span>
        </div>

        {/* Formatted Complaint Text Body */}
        <div className="flex-1 overflow-y-auto bg-gray-50 rounded-xl p-4 border border-gray-200 font-mono text-xs text-gray-800 leading-relaxed whitespace-pre-wrap select-all">
          {complaintText}
        </div>

        {/* Action Footer */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3">
          <a
            href="https://consumerhelpline.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-primary-600 font-bold hover:underline"
          >
            Open NCH INGRAM Portal <ExternalLink className="h-3.5 w-3.5" />
          </a>

          <div className="flex items-center gap-2">
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-1.5 px-4 py-2 bg-gray-900 text-white rounded-lg text-xs font-bold hover:bg-black transition-colors"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? 'Copied Dossier!' : 'Copy Complaint Text'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
