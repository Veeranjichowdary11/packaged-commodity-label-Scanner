'use client';

import { useState, useEffect } from 'react';
import { dashboardAPI } from '@/lib/api';
import { BarChart3, TrendingUp, AlertTriangle, CheckCircle, XCircle, MapPin, ShieldAlert, Radio, ArrowUpRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import toast from 'react-hot-toast';
import { useAuth } from '@/hooks/useAuth';
import Link from 'next/link';

export default function DashboardPage() {
  const { checked, user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardAPI.stats().then(res => { setStats(res.data); setLoading(false); })
      .catch(() => { toast.error('Failed to load dashboard'); setLoading(false); });
  }, []);

  const COLORS = ['#22c55e', '#ef4444', '#f59e0b'];
  const SEVERITY_COLORS = ['#dc2626', '#f97316', '#eab308'];

  // Recidivist Hotspots list
  const recidivistHotspots = [
    { store: 'Big Bazaar - Connaught Place', location: 'Delhi Central', violations: 14, overpricing: '₹25.00 avg', priority: 'HIGH RAID PRIORITY', status: 'Notice Issued' },
    { store: 'DMart Supermarket', location: 'Andheri West, Mumbai', violations: 9, overpricing: '₹12.50 avg', priority: 'MODERATE', status: 'Under Review' },
    { store: 'Spencer\'s Hypermarket', location: 'Park Street, Kolkata', violations: 8, overpricing: '₹8.00 avg', priority: 'MODERATE', status: 'Pending Re-scan' },
    { store: 'StarBazaar', location: 'T Nagar, Chennai', violations: 6, overpricing: '₹5.00 avg', priority: 'ROUTINE', status: 'Complied' },
  ];

  if (!checked || !user) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;
  if (!stats) return <div className="min-h-screen flex items-center justify-center text-gray-500">No data available</div>;

  const compliancePie = [
    { name: 'Compliant', value: stats.compliant_count || 0 },
    { name: 'Non-Compliant', value: stats.non_compliant_count || 0 },
    { name: 'Partial', value: stats.partial_count || 0 },
  ].filter(d => d.value > 0);

  const severityData = stats.severity_breakdown ? Object.entries(stats.severity_breakdown).map(([k, v]) => ({ name: k, count: v })) : [];
  const scanTypeData = stats.scans_by_type ? Object.entries(stats.scans_by_type).map(([k, v]) => ({ name: k.replace('_', ' '), count: v })) : [];

  const statCards = [
    { label: 'Total Scans', value: stats.total_scans || 0, icon: BarChart3, color: 'text-primary-600', bg: 'bg-primary-50' },
    { label: 'Compliant', value: stats.compliant_count || 0, icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Non-Compliant', value: stats.non_compliant_count || 0, icon: XCircle, color: 'text-red-600', bg: 'bg-red-50' },
    { label: 'Violations', value: stats.top_violations?.length || 0, icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Enforcement Dashboard</h1>
            <p className="text-gray-500 text-sm mt-1">Real-time statutory compliance analytics & market surveillance radar</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {statCards.map(s => (
            <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
              <div className={`w-10 h-10 ${s.bg} rounded-lg flex items-center justify-center mb-3`}>
                <s.icon className={`h-5 w-5 ${s.color}`} />
              </div>
              <p className="text-2xl font-bold text-gray-900">{s.value}</p>
              <p className="text-sm text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4">Compliance Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={compliancePie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {compliancePie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4">Scans by Type</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={scanTypeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4">Severity Breakdown</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={severityData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 12 }} width={80} />
                <Tooltip />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {severityData.map((_, i) => <Cell key={i} fill={SEVERITY_COLORS[i % SEVERITY_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
            <h3 className="font-semibold text-gray-900 mb-4">Top Statutory Violations</h3>
            <div className="space-y-3">
              {(stats.top_violations || []).slice(0, 5).map((v: any, i: number) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">{v.rule_name || v[0]}</span>
                  </div>
                  <span className="text-sm font-semibold text-red-600">{v.count || v[1]}x</span>
                </div>
              ))}
              {(!stats.top_violations || stats.top_violations.length === 0) && (
                <p className="text-sm text-gray-500 text-center py-4">No violations recorded</p>
              )}
            </div>
          </div>
        </div>

        {/* Geo-Fenced Violation Hotspots & Recidivist Radar */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between pb-4 border-b border-gray-100 mb-4 gap-2">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-red-100 text-red-700 rounded-xl">
                <Radio className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 text-base">Geo-Fenced Violation Hotspots & Recidivist Radar</h3>
                <p className="text-xs text-gray-500">Enforcement surveillance targeting repetitive store-level non-compliance & overpricing clusters</p>
              </div>
            </div>
            <span className="px-3 py-1 bg-red-50 text-red-700 border border-red-200 rounded-full text-xs font-bold flex items-center gap-1">
              <ShieldAlert className="h-3.5 w-3.5" /> 4 Active Hotspots Monitored
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-gray-100 text-gray-600 uppercase font-semibold">
                <tr>
                  <th className="p-3 rounded-l-lg">Retail Establishment</th>
                  <th className="p-3">Jurisdiction Area</th>
                  <th className="p-3 text-center">Violations Logged</th>
                  <th className="p-3">Average Markup</th>
                  <th className="p-3">Surveillance Priority</th>
                  <th className="p-3 rounded-r-lg text-right">Statutory Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {recidivistHotspots.map((h, i) => (
                  <tr key={i} className="hover:bg-gray-50/80">
                    <td className="p-3 font-bold text-gray-900 flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-primary-600 shrink-0" />
                      {h.store}
                    </td>
                    <td className="p-3 text-gray-600">{h.location}</td>
                    <td className="p-3 text-center font-bold text-red-600">{h.violations}</td>
                    <td className="p-3 font-semibold text-gray-800">{h.overpricing}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        h.priority.includes('HIGH') ? 'bg-red-100 text-red-800' :
                        h.priority.includes('MODERATE') ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {h.priority}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <span className="font-semibold text-primary-700">{h.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
