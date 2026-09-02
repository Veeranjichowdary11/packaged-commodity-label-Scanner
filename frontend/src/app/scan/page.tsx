'use client';

import { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, Camera, QrCode, X, Loader2, MapPin } from 'lucide-react';
import { scanAPI, productAPI } from '@/lib/api';
import toast from 'react-hot-toast';
import Webcam from 'react-webcam';
import { useAuth } from '@/hooks/useAuth';

type Tab = 'upload' | 'camera' | 'barcode';

export default function ScanPage() {
  const { user, checked } = useAuth();
  const [tab, setTab] = useState<Tab>('upload');
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [barcode, setBarcode] = useState('');
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [storeName, setStoreName] = useState('');
  const [storeAddress, setStoreAddress] = useState('');
  const webcamRef = useRef<Webcam>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const getLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          toast.success('Location captured');
        },
        () => toast.error('Location access denied')
      );
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 10 * 1024 * 1024) { toast.error('Max file size is 10MB'); return; }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const capturePhoto = useCallback(() => {
    const screenshot = webcamRef.current?.getScreenshot();
    if (screenshot) {
      fetch(screenshot)
        .then(r => r.blob())
        .then(blob => {
          const f = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
          setFile(f);
          setPreview(screenshot);
          setTab('upload');
          toast.success('Photo captured!');
        });
    }
  }, []);

  const submitScan = async (scanType: string) => {
    if (loading) return;
    if (!file) { toast.error('No image selected'); return; }
    const token = localStorage.getItem('token');
    if (!token) { toast.error('Session expired — please log in again'); router.push('/login'); return; }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('image', file);
      fd.append('scan_type', scanType);
      if (location) {
        fd.append('latitude', String(location.lat));
        fd.append('longitude', String(location.lng));
      }
      if (storeName) fd.append('store_name', storeName);
      if (storeAddress) fd.append('store_address', storeAddress);
      const res = await scanAPI.create(fd);
      toast.success('Scan complete!');
      router.push(`/scan/${res.data.id}`);
    } catch (err: any) {
      if (err.response?.status === 401) {
        toast.error('Session expired — please log in again');
        router.push('/login');
      } else if (err.response?.status === 500 || err.code === 'ERR_NETWORK') {
        const detail = err.response?.data?.detail;
        if (detail) {
          toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        } else {
          toast.error('Cannot connect to backend server. Make sure FastAPI is running on port 8000.');
        }
      } else {
        const detail = err.response?.data?.detail;
        let msg = err.response?.data?.message || err.message || 'Scan failed';
        if (typeof detail === 'string') {
          msg = detail;
        } else if (Array.isArray(detail)) {
          msg = detail.map((d: any) => (typeof d === 'string' ? d : d.msg || JSON.stringify(d))).join(', ');
        } else if (detail && typeof detail === 'object') {
          msg = detail.msg || JSON.stringify(detail);
        }
        toast.error(msg);
      }
    }
    setLoading(false);
  };

  const lookupBarcode = async () => {
    if (!barcode.trim()) { toast.error('Enter a barcode'); return; }
    setLoading(true);
    try {
      const res = await productAPI.verify(barcode.trim());
      toast.success('Product found!');
      router.push(`/scan/${res.data.scan_id || 'barcode'}?barcode=${barcode}&data=${encodeURIComponent(JSON.stringify(res.data))}`);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Product not found in database');
    }
    setLoading(false);
  };

  const tabs = [
    { id: 'upload' as Tab, label: 'Upload', icon: Upload },
    { id: 'camera' as Tab, label: 'Live Camera', icon: Camera },
    { id: 'barcode' as Tab, label: 'Barcode Lookup', icon: QrCode },
  ];

  if (!checked || !user) return <div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" /></div>;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Scan Product Label</h1>

        <div className="flex bg-white rounded-xl border border-gray-200 p-1 mb-6">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                tab === t.id ? 'bg-primary-600 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-50'
              }`}>
              <t.icon className="h-4 w-4" /> {t.label}
            </button>
          ))}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          {tab === 'upload' && (
            <div className="space-y-4">
              {!preview ? (
                <div onClick={() => fileRef.current?.click()}
                  className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center cursor-pointer hover:border-primary-400 hover:bg-primary-50/30 transition-colors">
                  <Upload className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 font-medium">Click to upload product label image</p>
                  <p className="text-gray-400 text-sm mt-1">PNG, JPG up to 10MB</p>
                  <input ref={fileRef} type="file" accept="image/*" onChange={handleFileSelect} className="hidden" />
                </div>
              ) : (
                <div className="relative">
                  <img src={preview} alt="Preview" className="w-full max-h-80 object-contain rounded-lg bg-gray-100" />
                  <button onClick={() => { setPreview(null); setFile(null); }}
                    className="absolute top-2 right-2 p-1.5 bg-white rounded-full shadow-md hover:bg-gray-100">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}

              <div className="border-t border-gray-100 pt-4">
                <button onClick={getLocation} className="flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700 mb-3">
                  <MapPin className="h-4 w-4" />
                  {location ? `Location: ${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}` : 'Add GPS Location (for crowdsource)'}
                </button>
                {location && (
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <input type="text" placeholder="Store name" value={storeName} onChange={e => setStoreName(e.target.value)}
                      className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none" />
                    <input type="text" placeholder="Store address" value={storeAddress} onChange={e => setStoreAddress(e.target.value)}
                      className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none" />
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                <button onClick={() => submitScan(location ? 'crowdsource' : 'manual')} disabled={!file || loading}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors">
                  {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Upload className="h-5 w-5" />}
                  {loading ? 'Analyzing...' : 'Scan Label'}
                </button>
              </div>
            </div>
          )}

          {tab === 'camera' && (
            <div className="space-y-4">
              <div className="rounded-xl overflow-hidden bg-black">
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  screenshotFormat="image/jpeg"
                  videoConstraints={{ facingMode: 'environment', width: 1280, height: 720 }}
                  className="w-full"
                />
              </div>
              <div className="flex items-center justify-center">
                <button onClick={capturePhoto}
                  className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center hover:bg-primary-700 shadow-lg transition-transform hover:scale-105">
                  <Camera className="h-7 w-7 text-white" />
                </button>
              </div>
              <p className="text-center text-sm text-gray-500">Point camera at the product label and tap to capture</p>
            </div>
          )}

          {tab === 'barcode' && (
            <div className="space-y-4">
              <div className="text-center py-4">
                <QrCode className="h-16 w-16 text-primary-300 mx-auto mb-3" />
                <p className="text-gray-600 font-medium">Cross-Verify by Barcode</p>
                <p className="text-gray-400 text-sm">Enter barcode number to verify product against database</p>
              </div>
              <input type="text" placeholder="Enter barcode number (e.g. 8901234567890)" value={barcode} onChange={e => setBarcode(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg text-center text-lg tracking-wider focus:ring-2 focus:ring-primary-500 outline-none" />
              <button onClick={lookupBarcode} disabled={loading}
                className="w-full flex items-center justify-center gap-2 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors">
                {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <QrCode className="h-5 w-5" />}
                {loading ? 'Searching...' : 'Verify Product'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
