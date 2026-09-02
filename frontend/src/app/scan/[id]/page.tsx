'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { scanAPI } from '@/lib/api';
import { CheckCircle, XCircle, AlertTriangle, Download, ArrowLeft, FileText, Shield } from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { useAuth } from '@/hooks/useAuth';

export default function ScanResultPage() {
  const { checked, user } = useAuth();
  const { id } = useParams();
  const [scan, setScan] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
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

        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><Shield className="h-4 w-4 text-primary-600" /> Scan Info</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-gray-500">Type</dt><dd className="font-medium capitalize">{scan.scan_type?.replace('_', ' ')}</dd></div>
              <div className="flex justify-between"><dt className="text-gray-500">Date</dt><dd className="font-medium">{new Date(scan.created_at).toLocaleString()}</dd></div>
              {scan.barcode_detected && <div className="flex justify-between"><dt className="text-gray-500">Barcode</dt><dd className="font-mono text-xs">{scan.barcode_detected}</dd></div>}
              {scan.store_name && <div className="flex justify-between"><dt className="text-gray-500">Store</dt><dd className="font-medium">{scan.store_name}</dd></div>}
            </dl>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2"><FileText className="h-4 w-4 text-primary-600" /> Extracted Fields</h3>
            <dl className="space-y-2 text-sm">
              {scan.extracted_fields && Object.entries(scan.extracted_fields).map(([key, val]: [string, any]) => (
                <div key={key} className="flex justify-between">
                  <dt className="text-gray-500 capitalize">{key.replace(/_/g, ' ')}</dt>
                  <dd className="font-medium text-right max-w-[60%] truncate">{typeof val === 'object' ? val?.value || JSON.stringify(val) : String(val)}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>

        {scan.violations && scan.violations.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-4">Violations ({scan.violations.length})</h3>
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
