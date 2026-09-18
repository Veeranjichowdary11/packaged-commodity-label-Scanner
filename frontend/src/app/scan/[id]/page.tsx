'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { scanAPI } from '@/lib/api';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Download, 
  ArrowLeft, 
  FileText, 
  Shield, 
  ImageIcon, 
  Layers,
  QrCode
} from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { useAuth } from '@/hooks/useAuth';

export default function ScanResultPage() {
  const { checked, user } = useAuth();
  const { id } = useParams();
  const [scan, setScan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  useEffect(() => {
    if (id && !isNaN(Number(id))) {
      scanAPI.get(Number(id)).then(res => { setScan(res.data); setLoading(false); })
        .catch(() => { toast.error('Scan not found'); setLoading(false); });
    }
  }, [id]);

  const downloadReport = async () => {
    try {
      const res = await scanAPI.report(Number(id));
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `janch-report-${id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch { toast.error('Report not available'); }
  };

  const statusConfig: Record<string, { icon: any; color: string; bg: string; label: string }> = {
    compliant: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50 border-green-200', label: 'Compliant' },
    non_compliant: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-50 border-red-200', label: 'Non-Compliant' },
    partially_compliant: { icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200', label: 'Partially Compliant' },
  };

  const severityColor: Record<string, string> = { critical: 'bg-red-100 text-red-800', major: 'bg-orange-100 text-orange-800', minor: 'bg-yellow-100 text-yellow-800' };

  if (!checked || !user) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  if (!scan) return <div className="min-h-screen flex items-center justify-center text-gray-500">Scan not found</div>;

  const status = statusConfig[scan.compliance_status] || statusConfig.non_compliant;
  const StatusIcon = status.icon;

  const backendBase = process.env.NEXT_PUBLIC_API_URL 
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/?$/, '') 
    : 'http://127.0.0.1:8000';

  const getImageUrl = (rawPath: string) => {
    if (!rawPath) return '';
    if (rawPath.startsWith('http://') || rawPath.startsWith('https://')) return rawPath;
    const cleanPath = rawPath.replace(/^[/\\]+/, '').replace(/\\/g, '/');
    return `${backendBase}/${cleanPath}`;
  };

  // Compile image list from image_paths or image_path
  const imageList: Array<{ label: string; path: string }> = [];
  if (Array.isArray(scan.image_paths) && scan.image_paths.length > 0) {
    scan.image_paths.forEach((img: any, idx: number) => {
      imageList.push({
        label: img.label || `Angle ${idx + 1}`,
        path: img.path || img.url || '',
      });
    });
  } else if (scan.image_path) {
    imageList.push({
      label: 'Primary Panel',
      path: scan.image_path,
    });
  }

  const activeImage = imageList[selectedImageIndex] || imageList[0];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link href="/history" className="flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm"><ArrowLeft className="h-4 w-4" /> Back</Link>
          <button onClick={downloadReport} className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
            <Download className="h-4 w-4" /> Download PDF
          </button>
        </div>

        <div className={`rounded-xl border p-6 mb-6 ${status.bg}`}>
          <div className="flex items-center gap-4">
            <StatusIcon className={`h-12 w-12 ${status.color}`} />
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{status.label}</h2>
              <p className="text-gray-600">Compliance Score: <span className="font-semibold">{scan.compliance_score}%</span></p>
              <p className="text-sm text-gray-500">{scan.passed_checks}/{scan.total_checks} checks passed</p>
            </div>
          </div>
        </div>

        {/* Scanned Images Gallery */}
        {imageList.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2 text-sm">
                <Layers className="h-4 w-4 text-primary-600" /> Scanned Product Panels ({imageList.length})
              </h3>
              {imageList.length > 1 && (
                <span className="text-xs text-gray-400">Click angle to inspect</span>
              )}
            </div>

            {/* Angle Selector Tabs */}
            {imageList.length > 1 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {imageList.map((img, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setSelectedImageIndex(idx)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                      selectedImageIndex === idx 
                        ? 'bg-primary-600 text-white shadow-sm' 
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {img.label}
                  </button>
                ))}
              </div>
            )}

            {/* Main Preview Container */}
            {activeImage && (
              <div className="rounded-lg bg-gray-100 border border-gray-200 overflow-hidden flex flex-col items-center justify-center p-2">
                <img 
                  src={getImageUrl(activeImage.path)} 
                  alt={activeImage.label}
                  className="max-h-80 w-auto object-contain rounded"
                  onError={(e) => {
                    // Fallback placeholder if image not found on disk
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
                <p className="text-xs text-gray-500 mt-2 font-medium">{activeImage.label}</p>
              </div>
            )}
          </div>
        )}

        {/* Barcode Cross-Verification Audit Card */}
        {scan.extracted_fields?.barcode_audit && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-4">
              <h3 className="font-bold text-gray-900 flex items-center gap-2 text-base">
                <QrCode className="h-5 w-5 text-primary-600" /> Barcode Cross-Verification Audit
              </h3>
              <span className={`px-2.5 py-1 rounded-full text-xs font-bold tracking-wide uppercase ${
                scan.extracted_fields.barcode_audit.status === 'MATCHED'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {scan.extracted_fields.barcode_audit.status === 'MATCHED' ? 'Authentic & Verified' : 'Mismatch / Discrepancy Alert'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4 text-sm">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 font-medium">GTIN / Barcode</p>
                <p className="font-mono text-sm font-semibold text-gray-900 mt-0.5">{scan.extracted_fields.barcode_audit.barcode || scan.barcode_detected}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 font-medium">Registered Database Master</p>
                <p className="font-semibold text-gray-900 mt-0.5">{scan.extracted_fields.barcode_audit.master_name} {scan.extracted_fields.barcode_audit.master_brand ? `(${scan.extracted_fields.barcode_audit.master_brand})` : ''}</p>
              </div>
              {scan.extracted_fields.barcode_audit.master_net_quantity && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 font-medium">Registered Volume</p>
                  <p className="font-semibold text-gray-900 mt-0.5">{scan.extracted_fields.barcode_audit.master_net_quantity}</p>
                </div>
              )}
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 font-medium">Data Registry</p>
                <p className="font-semibold text-gray-700 mt-0.5">{scan.extracted_fields.barcode_audit.source || 'Central Legal Metrology Database'}</p>
              </div>
            </div>

            {/* Checks Table */}
            {Array.isArray(scan.extracted_fields.barcode_audit.checks) && scan.extracted_fields.barcode_audit.checks.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-gray-100 text-gray-600 uppercase font-semibold">
                    <tr>
                      <th className="p-2.5 rounded-l-lg">Check</th>
                      <th className="p-2.5">Registered Spec</th>
                      <th className="p-2.5">Found on Label</th>
                      <th className="p-2.5 rounded-r-lg text-right">Result</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {scan.extracted_fields.barcode_audit.checks.map((c: any, i: number) => {
                      const isOk = c.status === 'MATCHED';
                      return (
                        <tr key={i} className="hover:bg-gray-50/80">
                          <td className="p-2.5 font-medium text-gray-900">{c.field}</td>
                          <td className="p-2.5 text-gray-600">{String(c.expected || '-')}</td>
                          <td className="p-2.5 text-gray-600 font-medium">{String(c.found || '-')}</td>
                          <td className="p-2.5 text-right">
                            <span className={`inline-flex items-center gap-1 font-semibold ${isOk ? 'text-green-700' : 'text-red-600'}`}>
                              {isOk ? <CheckCircle className="h-3.5 w-3.5 inline" /> : <AlertTriangle className="h-3.5 w-3.5 inline" />}
                              {c.status}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {Array.isArray(scan.extracted_fields.barcode_audit.mismatches) && scan.extracted_fields.barcode_audit.mismatches.length > 0 && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 space-y-1">
                <p className="font-bold flex items-center gap-1"><AlertTriangle className="h-3.5 w-3.5" /> Discrepancies Noted:</p>
                {scan.extracted_fields.barcode_audit.mismatches.map((m: string, i: number) => (
                  <p key={i} className="pl-4">• {m}</p>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><Shield className="h-4 w-4 text-primary-600" /> Scan Info</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-gray-500">Type</dt><dd className="font-medium capitalize">{scan.scan_type?.replace('_', ' ')}</dd></div>
              <div className="flex justify-between"><dt className="text-gray-500">Date</dt><dd className="font-medium">{new Date(scan.created_at).toLocaleString()}</dd></div>
              {scan.barcode_detected && <div className="flex justify-between"><dt className="text-gray-500">Barcode</dt><dd className="font-mono text-xs font-bold">{scan.barcode_detected}</dd></div>}
              {scan.store_name && <div className="flex justify-between"><dt className="text-gray-500">Store</dt><dd className="font-medium">{scan.store_name}</dd></div>}
            </dl>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><FileText className="h-4 w-4 text-primary-600" /> Extracted Declarations</h3>
            <dl className="space-y-2.5 text-sm">
              {scan.extracted_fields && Object.entries(scan.extracted_fields)
                .filter(([key]) => key !== 'barcode_audit')
                .map(([key, val]: [string, any]) => {
                  let displayVal = 'Not Found';
                  if (val !== null && val !== undefined) {
                    if (key === 'mrp' && typeof val === 'object') {
                      displayVal = val.value !== undefined ? `₹${val.value}${val.has_tax_note ? ' (incl. of taxes)' : ''}` : String(val.raw || val);
                    } else if (key === 'net_quantity' && typeof val === 'object') {
                      displayVal = `${val.value ?? ''} ${val.unit ?? ''}`.trim() || String(val.raw || val);
                    } else if (key === 'dates' && typeof val === 'object') {
                      const mfg = val.manufacture_date?.value || val.manufacture_date;
                      displayVal = mfg ? `Mfg: ${mfg}` : String(val.raw || val.value || val);
                    } else if (typeof val === 'object') {
                      displayVal = val.value || val.raw || JSON.stringify(val);
                    } else {
                      displayVal = String(val);
                    }
                  }
                  return (
                    <div key={key} className="flex justify-between items-start gap-2">
                      <dt className="text-gray-500 capitalize">{key.replace(/_/g, ' ')}</dt>
                      <dd className="font-medium text-right max-w-[65%] text-gray-900 break-words">{displayVal}</dd>
                    </div>
                  );
                })}
            </dl>
          </div>
        </div>

        {scan.violations && scan.violations.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4">Violations & Discrepancies ({scan.violations.length})</h3>
            <div className="space-y-3">
              {scan.violations.map((v: any, i: number) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                  <XCircle className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm text-gray-900">{v.rule_name}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${severityColor[v.severity] || 'bg-gray-100 text-gray-800'}`}>{v.severity}</span>
                    </div>
                    <p className="text-sm text-gray-600">{v.description}</p>
                    {v.expected_value && <p className="text-xs text-gray-500 mt-1"><b>Expected:</b> {v.expected_value}</p>}
                    {v.actual_value && <p className="text-xs text-gray-500"><b>Found:</b> {v.actual_value}</p>}
                    <p className="text-xs text-gray-400 mt-1">Ref: {v.section_reference} | Code: {v.rule_code}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
