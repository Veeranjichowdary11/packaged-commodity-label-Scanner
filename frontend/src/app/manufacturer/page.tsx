'use client';

import { useState, useRef } from 'react';
import { Upload, Loader2, CheckCircle, XCircle, AlertTriangle, Factory } from 'lucide-react';
import { manufacturerAPI } from '@/lib/api';
import toast from 'react-hot-toast';
import { useAuth } from '@/hooks/useAuth';

export default function ManufacturerPage() {
  const { checked, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [productName, setProductName] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setPreview(URL.createObjectURL(f));
  };

  const handleSubmit = async () => {
    const f = fileRef.current?.files?.[0];
    if (!f) { toast.error('Select a label image'); return; }
    if (!productName.trim()) { toast.error('Enter product name'); return; }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('image', f);
      fd.append('product_name', productName);
      const res = await manufacturerAPI.checkLabel(fd);
      setResult(res.data);
      toast.success('Label analysis complete');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Check failed');
    }
    setLoading(false);
  };

  const statusConfig: Record<string, { icon: any; color: string; bg: string; label: string }> = {
    compliant: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50 border-green-200', label: 'Compliant' },
    non_compliant: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50 border-red-200', label: 'Non-Compliant' },
    partially_compliant: { icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200', label: 'Partially Compliant' },
  };

  if (!checked || !user) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
            <Factory className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Pre-Print Label Check</h1>
            <p className="text-sm text-gray-500">Verify label compliance before printing</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Product Name</label>
              <input type="text" placeholder="e.g. Premium Basmati Rice 1kg" value={productName} onChange={e => setProductName(e.target.value)}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Label Image</label>
              {!preview ? (
                <div onClick={() => fileRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-primary-400 transition-colors">
                  <Upload className="h-10 w-10 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600 text-sm font-medium">Upload label design</p>
                  <p className="text-gray-400 text-xs mt-1">PNG, JPG up to 10MB</p>
                </div>
              ) : (
                <div className="relative">
                  <img src={preview} alt="Label" className="w-full max-h-60 object-contain rounded-lg bg-gray-100" />
                  <button onClick={() => { setPreview(null); if (fileRef.current) fileRef.current.value = ''; }}
                    className="absolute top-2 right-2 p-1.5 bg-white rounded-full shadow-md hover:bg-gray-100 text-xs">Clear</button>
                </div>
              )}
              <input ref={fileRef} type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
            </div>

            <button onClick={handleSubmit} disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors">
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <CheckCircle className="h-5 w-5" />}
              {loading ? 'Analyzing...' : 'Check Compliance'}
            </button>
          </div>
        </div>

        {result && (() => {
          const cr = result.compliance_result || result;
          const status = statusConfig[cr.compliance_status || result.compliance_status] || statusConfig.non_compliant;
          const StatusIcon = status.icon;
          return (
            <div className="space-y-4">
              <div className={`rounded-xl border p-5 ${status.bg}`}>
                <div className="flex items-center gap-3">
                  <StatusIcon className={`h-10 w-10 ${status.color}`} />
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">{status.label}</h3>
                    <p className="text-gray-600 text-sm">Score: {cr.compliance_score || cr.score}% | {cr.passed_checks || 0}/{cr.total_checks || 0} checks passed</p>
                  </div>
                </div>
              </div>

              {(cr.violations || []).length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <h3 className="font-semibold text-gray-900 mb-3">Issues to Fix Before Printing</h3>
                  <div className="space-y-2">
                    {cr.violations.map((v: any, i: number) => (
                      <div key={i} className="flex items-start gap-2 p-3 bg-red-50 rounded-lg">
                        <XCircle className="h-4 w-4 text-red-500 mt-0.5 shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{v.rule_name}</p>
                          <p className="text-xs text-gray-600">{v.description}</p>
                          <p className="text-xs text-gray-400 mt-1">Section: {v.section_reference}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(cr.passed_rules || []).length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <h3 className="font-semibold text-gray-900 mb-3">Passed Checks</h3>
                  <div className="space-y-1">
                    {cr.passed_rules.map((r: string, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm text-green-700">
                        <CheckCircle className="h-4 w-4" /> {r}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })()}
      </div>
    </div>
  );
}
