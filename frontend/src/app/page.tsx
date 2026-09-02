'use client';

import Link from 'next/link';
import { Shield, Camera, Users, BarChart3, FileCheck, ArrowRight, ScanLine, QrCode } from 'lucide-react';

export default function LandingPage() {
  const features = [
    { icon: Camera, title: 'Live Camera Scan', desc: 'Point your camera at any product label for real-time compliance checking with barcode auto-detection.' },
    { icon: Users, title: 'Crowdsource Scanning', desc: 'Any citizen can scan products at stores. Data feeds into enforcement dashboards with GPS & store info.' },
    { icon: QrCode, title: 'Barcode Cross-Verify', desc: 'Scan barcode to identify product, cross-verify label against database, detect counterfeits instantly.' },
    { icon: FileCheck, title: 'Compliance Reports', desc: 'Generate tamper-proof PDF reports with SHA-256 hash chain, mapped to Legal Metrology Rules 2011.' },
    { icon: BarChart3, title: 'Enforcement Dashboard', desc: 'Real-time analytics dashboard with violation heatmaps, trends, and severity breakdown for inspectors.' },
    { icon: ScanLine, title: 'AI-Powered OCR', desc: 'Advanced PaddleOCR extracts MRP, net quantity, manufacturer, dates, and all mandatory declarations.' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-blue-50">
      <nav className="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <Shield className="h-9 w-9 text-primary-600" />
          <span className="text-2xl font-bold text-gray-900">जाँच <span className="text-sm font-normal text-gray-500">Janch</span></span>
        </div>
        <Link href="/login" className="px-5 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
          Login
        </Link>
      </nav>

      <section className="max-w-7xl mx-auto px-6 pt-16 pb-20 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-100 rounded-full text-primary-700 text-sm font-medium mb-6">
          <Shield className="h-4 w-4" /> Smart India Hackathon 2024
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
          AI-Powered <span className="text-primary-600">Legal Metrology</span><br />Compliance Checker
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-10">
          Scan any packaged commodity label, extract mandatory declarations with AI,
          and verify compliance against the Legal Metrology (Packaged Commodities) Rules, 2011.
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/login" className="flex items-center gap-2 px-8 py-3 bg-primary-600 text-white rounded-xl text-lg font-medium hover:bg-primary-700 shadow-lg shadow-primary-200 transition-all hover:shadow-xl">
            Start Scanning <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-6 pb-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">What Makes Janch Unique</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div key={f.title} className="bg-white rounded-xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
              <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center mb-4">
                <f.icon className="h-6 w-6 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-gray-600 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-gray-200 py-8 text-center text-gray-500 text-sm">
        Built for Smart India Hackathon &mdash; Legal Metrology (Packaged Commodities) Rules, 2011
      </footer>
    </div>
  );
}
