"use client";

import React from "react";
import SpectrogramCanvas from "./SpectrogramCanvas";
import { Mic, ShieldCheck, Cpu, Volume2, FileText, CheckCircle2, AlertOctagon } from "lucide-react";

export default function AudioTriageWorkbench() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Mic className="w-5 h-5 text-purple-400" />
            Synthetic Voice Note Forensic Workbench (FR-1.x)
          </h2>
          <p className="text-xs text-slate-400">
            Acoustic anomaly detection, AASIST deepfake classification, and conformal risk calibration.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300">
            Inference: Local PyTorch (Zero Offshore)
          </span>
        </div>
      </div>

      {/* Spectrogram Canvas (Decoupled 60 FPS HTML5 Canvas) */}
      <SpectrogramCanvas />

      {/* Diagnostics Grid & Whisper ASR Transcript */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conformal Calibration Diagnostics */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-sovereign-gold" />
              <h3 className="text-sm font-bold text-white">Conformal Statistical Calibration</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Guaranteed Bound
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase">Raw Acoustic Anomaly Score</span>
              <span className="text-lg font-bold text-red-400">0.9420</span>
              <span className="text-[10px] text-slate-500 block mt-1">Threshold: τ = 0.8500</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase">Conformal p-value</span>
              <span className="text-lg font-bold text-purple-400">&lt; 0.0010</span>
              <span className="text-[10px] text-slate-500 block mt-1">Significance: α = 0.001</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase">Codec Compensation Profile</span>
              <span className="text-sm font-bold text-slate-200">WhatsApp Opus 16kbps</span>
              <span className="text-[10px] text-slate-500 block mt-1">Spectral Band Preserved</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase">Payload Duration</span>
              <span className="text-sm font-bold text-emerald-400">24.3s (≤ 120s Cap)</span>
              <span className="text-[10px] text-slate-500 block mt-1">16kHz Mono PCM Normalized</span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-300">
            <span className="font-bold text-white block mb-1">Mathematical Guarantee (NFR-3.1):</span>
            Under the non-parametric conformal calibration manifold, the probability of false synthetic media alarm on genuine Gulf Arabic audio is rigorously bounded by:
            <code className="text-sovereign-cyan ml-1 font-mono">P(Flagged | Genuine) ≤ 0.1%</code>
          </div>
        </div>

        {/* Whisper ASR Transcript & Linguistic Cues */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-sovereign-cyan" />
              <h3 className="text-sm font-bold text-white">Local Whisper ASR Transcript</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
              Sub-350ms INT8
            </span>
          </div>

          {/* Bilingual Transcript Card */}
          <div className="space-y-3">
            {/* Arabic Original */}
            <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-right" dir="rtl">
              <span className="text-[10px] font-mono text-slate-500 block mb-1">النص الصوتي المفرغ (العربية):</span>
              <p className="text-sm text-slate-200 leading-relaxed font-sans">
                &quot;مرحباً، معك النقيب أحمد من شرطة دبي. تم تسجيل مخالفة مرورية حرجة على مركبتك بمبلغ <span className="text-red-400 font-bold underline">٥٠٠ درهم</span>. يرجى الدخول فوراً على الرابط وتأكيد الدفع خلال <span className="text-red-400 font-bold underline">ساعتين</span> لتجنب حجز المركبة.&quot;
              </p>
            </div>

            {/* English Translation */}
            <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800">
              <span className="text-[10px] font-mono text-slate-500 block mb-1">Bilingual Translation (English):</span>
              <p className="text-xs text-slate-300 leading-relaxed">
                &quot;Hello, this is Captain Ahmed from Dubai Police. A critical traffic violation of <span className="text-red-400 font-bold underline">AED 500</span> has been issued to your vehicle. Access the link immediately and confirm payment within <span className="text-red-400 font-bold underline">2 hours</span> to avoid vehicle impoundment.&quot;
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800">
            <span>Social Engineering Cues: <strong>Artificial Urgency (2h), Imposter Pretexting</strong></span>
            <span className="text-red-400 font-mono font-bold">RED VERDICT</span>
          </div>
        </div>
      </div>
    </div>
  );
}
