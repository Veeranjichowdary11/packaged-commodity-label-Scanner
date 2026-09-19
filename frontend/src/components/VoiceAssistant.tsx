'use client';

import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Globe, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

interface VoiceAssistantProps {
  scan: any;
}

export default function VoiceAssistant({ scan }: VoiceAssistantProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedLang, setSelectedLang] = useState<'en' | 'hi' | 'te' | 'ta' | 'mr' | 'bn'>('en');

  const langOptions = [
    { code: 'en', label: 'English', voiceLang: 'en-IN' },
    { code: 'hi', label: 'हिन्दी (Hindi)', voiceLang: 'hi-IN' },
    { code: 'te', label: 'తెలుగు (Telugu)', voiceLang: 'te-IN' },
    { code: 'ta', label: 'தமிழ் (Tamil)', voiceLang: 'ta-IN' },
    { code: 'mr', label: 'मराठी (Marathi)', voiceLang: 'mr-IN' },
    { code: 'bn', label: 'বাংলা (Bengali)', voiceLang: 'bn-IN' },
  ];

  const generateSpeechScript = (lang: string) => {
    const isCompliant = scan.compliance_status === 'compliant';
    const isReviewReq = scan.compliance_status === 'review_required';
    const score = scan.compliance_score || 0;
    const prodName = scan.extracted_fields?.common_name || 'This product';
    const mrpObj = scan.extracted_fields?.mrp;
    const mrpVal = mrpObj?.value ? `₹${mrpObj.value}` : 'Price';

    const barcodeAudit = scan.extracted_fields?.barcode_audit;
    const isOverpriced = barcodeAudit?.status === 'MISMATCH_ALERT';

    if (lang === 'hi') {
      if (isCompliant) {
        return `जाँच रिपोर्ट: ${prodName} पूरी तरह से लीगल मेट्रोलॉजी नियमों के अनुरूप है। अनुपालन स्कोर ${score}% है। एमआरपी ${mrpVal} सही पाई गई।`;
      } else if (isOverpriced) {
        return `चेतावनी! ${prodName} पर अधिकतम खुदरा मूल्य (MRP) में गड़बड़ी पाई गई है। कृपया अधिक कीमत न दें। उपभोक्ता शिकायत दर्ज करें।`;
      } else if (isReviewReq) {
        return `ध्यान दें: ${prodName} के फॉन्ट साइज और लेबल की जांच आवश्यक है। अनुपालन स्कोर ${score}% है।`;
      } else {
        return `सतर्कता चेतावनी: ${prodName} में ${scan.violations?.length || 1} नियम उल्लंघन पाए गए हैं। पैकेजिंग पर अनिवार्य विवरण गायब हैं।`;
      }
    } else if (lang === 'te') {
      if (isCompliant) {
        return `తనిఖీ నివేదిక: ${prodName} చట్టపరమైన నిబంధనలకు అనుగుణంగా ఉంది. కంప్లైయన్స్ స్కోరు ${score} శాతం. MRP ${mrpVal} సరైనది.`;
      } else if (isOverpriced) {
        return `హెచ్చరిక! ${prodName} పై అసలు ధర కంటే ఎక్కువ MRP వసూలు చేయబడుతోంది. వినియోగదారుల ఫోరమ్‌లో ఫిర్యాదు చేయండి.`;
      } else {
        return `హెచ్చరిక: ${prodName} ప్యాకేజింగ్ పై తప్పనిసరి వివరాలు లోపించాయి. నిబంధనల ఉల్లంఘనలు గుర్తించబడ్డాయి.`;
      }
    } else if (lang === 'ta') {
      if (isCompliant) {
        return `ஆய்வு அறிக்கை: ${prodName} சட்ட அளவியல் விதிகளுக்கு முழுமையாக உட்பட்டது. இணக்க மதிப்பெண் ${score}%.`;
      } else {
        return `எச்சரிக்கை! ${prodName} தயாரிப்பில் விதிமீறல்கள் கண்டறியப்பட்டுள்ளன. கூடுதல் விலை செலுத்த வேண்டாம்.`;
      }
    } else if (lang === 'mr') {
      if (isCompliant) {
        return `तपासणी अहवाल: ${prodName} कायदेशीर मापन नियमांनुसार पूर्णपणे वैध आहे. स्कोअर ${score}% आहे.`;
      } else {
        return `सावधान! ${prodName} च्या पॅकेजिंगवर नियमभंग आढळला आहे. एमआरपी पेक्षा जास्त पैसे देऊ नका.`;
      }
    } else if (lang === 'bn') {
      if (isCompliant) {
        return `যাচাই রিপোর্ট: ${prodName} সম্পূর্ণভাবে আইনি মানদণ্ড অনুযায়ী সঠিক। স্কোর ${score}%।`;
      } else {
        return `সতর্কতা! ${prodName} এর প্যাকেজিংয়ে অসঙ্গতি পাওয়া গেছে। অতিরিক্ত মূল্য দেবেন না।`;
      }
    } else {
      // English
      if (isCompliant) {
        return `Janch Verification Report: ${prodName} is fully compliant with Legal Metrology Packaged Commodities Rules with a compliance score of ${score}%. Declared price ${mrpVal} is verified authentic.`;
      } else if (isOverpriced) {
        return `Price Gouging Alert! ${prodName} packaging indicates MRP discrepancy or price markup. Do not pay above official price. File a consumer grievance.`;
      } else if (isReviewReq) {
        return `Notice: ${prodName} has a compliance score of ${score}%. Physical font height verification under Rule 7 is pending inspection.`;
      } else {
        return `Compliance Warning: ${scan.violations?.length || 1} statutory violations detected on ${prodName}. Mandatory packaging declarations are missing or non-compliant.`;
      }
    }
  };

  const handleSpeak = () => {
    if (!('speechSynthesis' in window)) {
      toast.error('Voice synthesis not supported in this browser');
      return;
    }

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      return;
    }

    window.speechSynthesis.cancel();
    const script = generateSpeechScript(selectedLang);
    const utterance = new SpeechSynthesisUtterance(script);

    const targetOpt = langOptions.find(l => l.code === selectedLang);
    if (targetOpt) {
      utterance.lang = targetOpt.voiceLang;
    }

    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsPlaying(true);
    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = () => setIsPlaying(false);

    window.speechSynthesis.speak(utterance);
    toast.success(`Playing audio guidance (${targetOpt?.label})`);
  };

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return (
    <div className="flex flex-wrap items-center gap-2 p-2 bg-white/80 backdrop-blur-sm rounded-lg border border-gray-200 text-xs shadow-sm">
      <div className="flex items-center gap-1 text-gray-600 font-semibold pl-1">
        <Globe className="h-3.5 w-3.5 text-primary-600" />
        <span className="hidden sm:inline">Voice Assistant:</span>
      </div>

      <select
        value={selectedLang}
        onChange={(e) => {
          setSelectedLang(e.target.value as any);
          if (isPlaying) window.speechSynthesis.cancel();
          setIsPlaying(false);
        }}
        className="text-xs py-1 px-2 rounded border border-gray-300 bg-white font-medium outline-none"
      >
        {langOptions.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>

      <button
        type="button"
        onClick={handleSpeak}
        className={`flex items-center gap-1 px-3 py-1 rounded font-bold transition-colors ${
          isPlaying
            ? 'bg-red-600 text-white animate-pulse'
            : 'bg-primary-600 text-white hover:bg-primary-700'
        }`}
      >
        {isPlaying ? (
          <>
            <VolumeX className="h-3.5 w-3.5" /> Stop Audio
          </>
        ) : (
          <>
            <Volume2 className="h-3.5 w-3.5" /> Read Aloud
          </>
        )}
      </button>
    </div>
  );
}
