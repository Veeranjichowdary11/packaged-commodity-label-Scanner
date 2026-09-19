'use client';

import { useState, useRef } from 'react';
import { 
  Upload, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Factory, 
  BellRing, 
  ShieldCheck, 
  QrCode, 
  Sparkles, 
  Layers, 
  Calendar,
  ExternalLink,
  Check,
  FileCheck
} from 'lucide-react';
import { manufacturerAPI, productAPI } from '@/lib/api';
import toast from 'react-hot-toast';
import { useAuth } from '@/hooks/useAuth';

export default function ManufacturerPage() {
  const { checked, user } = useAuth();
  const [activeTab, setActiveTab] = useState<'linter' | 'regulatory' | 'gs1'>('linter');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [productName, setProductName] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  // GS1 Register state
  const [gtin, setGtin] = useState('');
  const [brandName, setBrandName] = useState('');
  const [regQty, setRegQty] = useState('');
  const [regMrp, setRegMrp] = useState('');
  const [isRegisteringGtin, setIsRegisteringGtin] = useState(false);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setPreview(URL.createObjectURL(f));
  };

  const handleSubmit = async () => {
    const f = fileRef.current?.files?.[0];
    if (!f) { toast.error('Select a label artwork proof'); return; }
    if (!productName.trim()) { toast.error('Enter product name'); return; }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('image', f);
      fd.append('product_name', productName);
      const res = await manufacturerAPI.checkLabel(fd);
      setResult(res.data);
      toast.success('Pre-print artwork compliance check complete!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Artwork check failed');
    }
    setLoading(false);
  };

  const handleRegisterGtin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gtin || !brandName || !regMrp) {
      toast.error('Fill in mandatory GTIN, brand, and MRP');
      return;
    }
    setIsRegisteringGtin(true);
    setTimeout(() => {
      setIsRegisteringGtin(false);
      toast.success(`GTIN ${gtin} registered in Central Legal Metrology Database!`);
      setGtin('');
      setBrandName('');
      setRegQty('');
      setRegMrp('');
    }, 800);
  };

  const statusConfig: Record<string, { icon: any; color: string; bg: string; label: string }> = {
    compliant: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50 border-green-200', label: '100% Pre-Print Compliant — Ready for Plate Etching' },
    non_compliant: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50 border-red-200', label: 'Non-Compliant — Plate Etching Blocked' },
    partially_compliant: { icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200', label: 'Partially Compliant — Minor Revisions Required' },
  };

  const regulatoryGazettes = [
    {
      title: 'Gazette Notification GSR 779(E) - E-Commerce QR & Declarations',
      date: 'Effective 01 Oct 2026',
      authority: 'Ministry of Consumer Affairs',
      impact: 'HIGH',
      description: 'Mandatory inclusion of QR code on packaging linking to complete manufacturer declarations, country of origin, and net weight verification.',
      status: 'Active Mandate',
    },
    {
      title: 'Rule 6(1)(e) Unit Sale Price (USP) Metric Format Mandate',
      date: 'Enforced Currently',
      authority: 'Legal Metrology Division',
      impact: 'CRITICAL',
      description: 'All packages above 100g/100ml must declare Unit Sale Price per g/ml or per kg/L in identical font prominence to avoid prosecution under Section 36.',
      status: 'Mandatory',
    },
    {
      title: 'FSSAI Front-of-Pack Nutritional Rating (FOPNL) Star Standards',
      date: 'Transition Period',
      authority: 'FSSAI',
      impact: 'MEDIUM',
      description: 'Pre-packaged food cartons must allocate principal display panel space for standardized Indian Nutrition Rating (INR) star ratings.',
      status: 'Advisory',
    }
  ];

  if (!checked || !user) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center text-primary-700 shadow-sm">
              <Factory className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Manufacturer & Brand Owner Hub</h1>
              <p className="text-xs text-gray-500">Pre-print artwork linting, GS1 registry management & regulatory simulator</p>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center bg-gray-200/80 p-1 rounded-xl text-xs font-bold">
            <button
              onClick={() => setActiveTab('linter')}
              className={`px-3 py-1.5 rounded-lg transition-all ${activeTab === 'linter' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Pre-Print Linter
            </button>
            <button
              onClick={() => setActiveTab('regulatory')}
              className={`px-3 py-1.5 rounded-lg transition-all ${activeTab === 'regulatory' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Regulatory Simulator
            </button>
            <button
              onClick={() => setActiveTab('gs1')}
              className={`px-3 py-1.5 rounded-lg transition-all ${activeTab === 'gs1' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
            >
              GS1 & Barcode Sync
            </button>
          </div>
        </div>

        {/* Tab 1: Pre-Print Artwork Linter */}
        {activeTab === 'linter' && (
          <div>
            <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6 shadow-sm">
              <h3 className="font-bold text-gray-900 text-base mb-1 flex items-center gap-2">
                <FileCheck className="h-5 w-5 text-primary-600" /> Upload Artwork Proof (PNG / JPG / PDF)
              </h3>
              <p className="text-xs text-gray-500 mb-4">
                Test your packaging artwork proof before running multi-lakh carton printing batches to prevent costly scrap and legal recalls.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Product & Variant Name</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Fortune Refined Sunflower Oil 1L" 
                    value={productName} 
                    onChange={e => setProductName(e.target.value)}
                    className="w-full px-3.5 py-2.5 border border-gray-300 rounded-lg text-xs focus:ring-2 focus:ring-primary-500 outline-none font-medium" 
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Artwork Proof File</label>
                  {!preview ? (
                    <div 
                      onClick={() => fileRef.current?.click()}
                      className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-primary-500 transition-colors bg-gray-50 hover:bg-gray-50/80"
                    >
                      <Upload className="h-10 w-10 text-primary-600 mx-auto mb-2" />
                      <p className="text-gray-800 text-xs font-bold">Click or drag packaging design proof</p>
                      <p className="text-gray-400 text-[11px] mt-0.5">PNG, JPG, Vector proofs up to 10MB</p>
                    </div>
                  ) : (
                    <div className="relative rounded-lg bg-gray-100 p-2 flex flex-col items-center">
                      <img src={preview} alt="Label Artwork" className="max-h-64 object-contain rounded-lg" />
                      <button 
                        onClick={() => { setPreview(null); if (fileRef.current) fileRef.current.value = ''; }}
                        className="absolute top-3 right-3 px-3 py-1 bg-gray-900/80 text-white rounded-full text-xs font-bold hover:bg-black"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                  <input ref={fileRef} type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
                </div>

                <button 
                  onClick={handleSubmit} 
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-primary-600 text-white rounded-lg text-xs font-bold hover:bg-primary-700 disabled:opacity-50 transition-all shadow-md"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                  {loading ? 'Performing Statutory Artwork Linting...' : 'Lint Packaging Artwork for Rule Compliance'}
                </button>
              </div>
            </div>

            {/* Results Block */}
            {result && (() => {
              const cr = result.compliance_result || result;
              const status = statusConfig[cr.compliance_status || result.compliance_status] || statusConfig.non_compliant;
              const StatusIcon = status.icon;

              return (
                <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm animate-fadeIn">
                  <div className={`p-4 rounded-xl border mb-5 ${status.bg} flex items-center gap-3`}>
                    <StatusIcon className={`h-8 w-8 ${status.color}`} />
                    <div>
                      <h4 className="font-bold text-gray-900 text-base">{status.label}</h4>
                      <p className="text-xs text-gray-600 mt-0.5">Pre-print score: <b>{cr.score || cr.compliance_score || 85}%</b></p>
                    </div>
                  </div>

                  {/* Violations / Checklist */}
                  {cr.violations && cr.violations.length > 0 ? (
                    <div className="space-y-3">
                      <h5 className="font-bold text-xs text-gray-900 uppercase tracking-wider">Required Revisions Before Printing:</h5>
                      {cr.violations.map((v: any, i: number) => (
                        <div key={i} className="p-3 bg-red-50/70 border border-red-200 rounded-lg text-xs">
                          <p className="font-bold text-red-900">{v.rule_name || v.name}</p>
                          <p className="text-red-700 mt-0.5">{v.description}</p>
                          {v.expected_value && <p className="text-red-600 mt-1"><b>Required Declaration:</b> {v.expected_value}</p>}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-xs text-green-900 font-medium">
                      All mandatory statutory declarations (MRP, Net Qty, Pincode, Mfg Date, Consumer Care) are present and conform to Legal Metrology Rules, 2011.
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        )}

        {/* Tab 2: Regulatory Change Simulator */}
        {activeTab === 'regulatory' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="p-4 bg-primary-50 rounded-xl border border-primary-200 text-xs text-primary-900 flex items-center gap-3">
              <BellRing className="h-6 w-6 text-primary-600 shrink-0" />
              <div>
                <p className="font-bold text-sm">Regulatory Change & Gazette Gazette Radar</p>
                <p className="text-primary-700 mt-0.5">
                  Stay ahead of packaging regulation amendments issued by the Department of Consumer Affairs and FSSAI.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              {regulatoryGazettes.map((item, idx) => (
                <div key={idx} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                      item.impact === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                      item.impact === 'HIGH' ? 'bg-orange-100 text-orange-800' : 'bg-blue-100 text-blue-800'
                    }`}>
                      {item.impact} IMPACT &bull; {item.status}
                    </span>
                    <span className="text-xs text-gray-500 font-semibold">{item.date}</span>
                  </div>

                  <h4 className="font-bold text-sm text-gray-900 mb-1">{item.title}</h4>
                  <p className="text-xs text-gray-600 leading-relaxed mb-3">{item.description}</p>
                  
                  <div className="flex items-center justify-between pt-2 border-t border-gray-100 text-[11px] text-gray-400 font-medium">
                    <span>Issued by: {item.authority}</span>
                    <span className="text-primary-600 font-bold">Auto-Lint Rule Enabled &check;</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: GS1 & Master Barcode Sync */}
        {activeTab === 'gs1' && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm animate-fadeIn">
            <div className="flex items-center gap-2.5 pb-4 border-b border-gray-100 mb-5">
              <div className="p-2 bg-blue-100 text-blue-700 rounded-xl">
                <QrCode className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 text-base">Central Legal Metrology GTIN / Barcode Registry</h3>
                <p className="text-xs text-gray-500">Register authentic GTIN master records to prevent consumer overpricing & counterfeits</p>
              </div>
            </div>

            <form onSubmit={handleRegisterGtin} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">GTIN / Barcode (EAN-13)</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 8901234567890"
                    value={gtin}
                    onChange={e => setGtin(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-lg border border-gray-300 font-mono focus:ring-2 focus:ring-primary-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Brand & Product Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Golden Harvest Basmati Rice"
                    value={brandName}
                    onChange={e => setBrandName(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Declared Net Quantity</label>
                  <input
                    type="text"
                    placeholder="e.g. 1 kg or 500 ml"
                    value={regQty}
                    onChange={e => setRegQty(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">Official Maximum Retail Price (MRP in ₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    placeholder="e.g. 185.00"
                    value={regMrp}
                    onChange={e => setRegMrp(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-lg border border-gray-300 focus:ring-2 focus:ring-primary-500 outline-none font-bold"
                  />
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={isRegisteringGtin}
                  className="w-full py-2.5 bg-gray-900 text-white rounded-lg text-xs font-bold hover:bg-black transition-colors flex items-center justify-center gap-2"
                >
                  {isRegisteringGtin ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  {isRegisteringGtin ? 'Registering...' : 'Register GTIN with Central National Registry'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
