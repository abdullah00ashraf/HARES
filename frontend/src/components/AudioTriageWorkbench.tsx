"use client";

import React, { useState } from "react";
import SpectrogramCanvas from "./SpectrogramCanvas";
import {
  Mic,
  ShieldCheck,
  Cpu,
  Volume2,
  FileText,
  CheckCircle2,
  AlertOctagon,
  Activity,
  Layers,
  Sparkles,
  Info,
  Sliders,
  Play,
  RotateCcw,
  Scale,
  Lock,
} from "lucide-react";
import { soundFx } from "../lib/audioSoundFx";

export interface AudioSamplePreset {
  id: string;
  title: string;
  arabicTitle: string;
  sourceType: "SYNTHETIC" | "AUTHENTIC";
  generator: string;
  verdict: "RED" | "GREEN";
  anomalyScore: number;
  conformalPValue: string;
  jitter: string;
  shimmer: string;
  formants: string;
  vocoderDiscontinuity: string;
  vocoderBand: string;
  codec: string;
  duration: string;
  arabicTranscript: string;
  englishTranscript: string;
  socialCues: string;
}

const AUDIO_SAMPLES: AudioSamplePreset[] = [
  {
    id: "sample-police-clone",
    title: "Dubai Police Impersonator (F5-TTS Neural Voice Clone)",
    arabicTitle: "انتحال صوتي لضابط بشرطة دبي (استنساخ عصبي)",
    sourceType: "SYNTHETIC",
    generator: "F5-TTS DiT Diffusion Neural Model",
    verdict: "RED",
    anomalyScore: 0.942,
    conformalPValue: "< 0.0010",
    jitter: "0.038% (Critical: Flat Pitch Micro-Dynamics)",
    shimmer: "0.82% (Unnatural Amplitude Rigidity)",
    formants: "F1: 610Hz, F2: 1220Hz (Robotic Spacing)",
    vocoderDiscontinuity: "Flagged (Neural Phase Glitch)",
    vocoderBand: "4.8 kHz – 7.2 kHz band",
    codec: "WhatsApp Opus 16kbps Mono",
    duration: "24.3s (16kHz PCM)",
    arabicTranscript:
      "مرحباً، معك النقيب أحمد من شرطة دبي. تم تسجيل مخالفة مرورية حرجة على مركبتك بمبلغ ٥٠٠ درهم. يرجى الدخول فوراً على الرابط وتأكيد الدفع خلال ساعتين لتجنب حجز المركبة.",
    englishTranscript:
      "Hello, this is Captain Ahmed from Dubai Police. A critical traffic violation of AED 500 has been issued to your vehicle. Access the link immediately and confirm payment within 2 hours to avoid vehicle impoundment.",
    socialCues: "Psychological Urgency (2h deadline), Authority Pretexting, Vehicle Impoundment Threat",
  },
  {
    id: "sample-salik-elevenlabs",
    title: "Salik Toll Account Urgency (ElevenLabs Multilingual V2)",
    arabicTitle: "رسالة سالك الصوتية الاحتيالية (ElevenLabs)",
    sourceType: "SYNTHETIC",
    generator: "ElevenLabs Flash Multilingual V2",
    verdict: "RED",
    anomalyScore: 0.918,
    conformalPValue: "< 0.0010",
    jitter: "0.052% (Abnormal Pitch Uniformity)",
    shimmer: "0.94% (Synthetic Smoothness)",
    formants: "F1: 580Hz, F2: 1190Hz (Atypical Vowel Dispersion)",
    vocoderDiscontinuity: "Flagged (Diffusion Mel Discontinuity)",
    vocoderBand: "5.1 kHz – 6.9 kHz band",
    codec: "WhatsApp Opus 16kbps Mono",
    duration: "18.7s (16kHz PCM)",
    arabicTranscript:
      "تنبيه عاجل من بوابات سالك دبي. رصيد حسابك سالك أصبح سلبياً وسيتم فرض غرامة تراكمية خلال ٦٠ دقيقة. انقر على الرابط لتعبئة الرصيد.",
    englishTranscript:
      "Urgent alert from Salik Dubai Tolls. Your Salik balance is negative and a cumulative fine will be applied within 60 minutes. Click the link to recharge your balance.",
    socialCues: "Financial Penalties Coercion, 60-Minute Countdown, Phishing Gateway Redirection",
  },
  {
    id: "sample-authentic-emirati",
    title: "Authentic Emirati Citizen Voice Query (Gulf Arabic)",
    arabicTitle: "تسجيل صوتي حقيقي لمواطن إماراتي (لهجة خليجية)",
    sourceType: "AUTHENTIC",
    generator: "Genuine Human Speech (Vocal Chords)",
    verdict: "GREEN",
    anomalyScore: 0.081,
    conformalPValue: "0.9420 (Safe)",
    jitter: "0.84% (Natural Human Vocal Fold Micro-Instability)",
    shimmer: "3.42% (Normal Human Breath Modulation)",
    formants: "F1: 520Hz, F2: 1480Hz, F3: 2540Hz (Natural Vocal Tract Resonance)",
    vocoderDiscontinuity: "None (Smooth Spectral Phase Coherence)",
    vocoderBand: "Clean Full Spectrum (0 - 8 kHz)",
    codec: "WhatsApp Opus 16kbps Mono",
    duration: "15.2s (16kHz PCM)",
    arabicTranscript:
      "السلام عليكم ورحمة الله، بغيت استفسر بخصوص تجديد ملكية السيارة في تطبيق دبي درايف، هل الرسوم تشمل الفحص الفني ولا لا؟ مشكورين.",
    englishTranscript:
      "Peace be upon you, I would like to inquire about renewing vehicle registration on the Dubai Drive app, does the fee include the technical inspection or not? Thank you.",
    socialCues: "Natural Conversational Phrasing, Zero Coercion, Genuine Municipal Inquiry",
  },
  {
    id: "sample-authentic-rta",
    title: "Official RTA Customer Care Agent Follow-up (Arabic)",
    arabicTitle: "مكالمة خدمة عملاء رسمية لهيئة الطرق والمواصلات",
    sourceType: "AUTHENTIC",
    generator: "Genuine Human Speech (Official Agent)",
    verdict: "GREEN",
    anomalyScore: 0.112,
    conformalPValue: "0.8870 (Safe)",
    jitter: "0.78% (Healthy Physiological Pitch Variance)",
    shimmer: "3.15% (Dynamic Acoustic Energy)",
    formants: "F1: 490Hz, F2: 1420Hz, F3: 2610Hz (Human Articulation)",
    vocoderDiscontinuity: "None (Natural Acoustic Environment)",
    vocoderBand: "Clean Full Spectrum (0 - 8 kHz)",
    codec: "WhatsApp Opus 16kbps Mono",
    duration: "21.6s (16kHz PCM)",
    arabicTranscript:
      "مرحباً بك في هيئة الطرق والمواصلات بدبي. بخصوص طلبكم رقم ٤٨٢٩١، نفيدكم بأنه تم استلام استفساركم وسيتم التواصل معكم عبر القنوات الرسمية خلال يومي عمل.",
    englishTranscript:
      "Welcome to Dubai Roads and Transport Authority. Regarding your request number 48291, we inform you that your inquiry has been received and you will be contacted via official channels within two business days.",
    socialCues: "Standard Service Protocol, Official Reference Number, No Immediate Payment Demands",
  },
];

export default function AudioTriageWorkbench() {
  const [selectedSample, setSelectedSample] = useState<AudioSamplePreset>(AUDIO_SAMPLES[0]);
  const [canvasViewMode, setCanvasViewMode] = useState<"spectrogram" | "waveform">("spectrogram");
  const [showBaselineComparison, setShowBaselineComparison] = useState<boolean>(false);

  const handleSelectSample = (sample: AudioSamplePreset) => {
    soundFx.playClick();
    setSelectedSample(sample);
  };

  const isSynthetic = selectedSample.sourceType === "SYNTHETIC";

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Mic className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              <span>Synthetic Voice Note Forensic Workbench (FR-1.x)</span>
            </h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/40 animate-pulse">
              [ ⚠️ OFFLINE: RETRAINING ]
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Acoustic anomaly detection, AASIST deepfake classification, pitch jitter/shimmer forensics, and non-parametric conformal calibration.
            <span className="ml-1 text-slate-400 font-arabic">/ مختبر كشف التزييف الصوتي المتقدم</span>
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-900 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800 flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-amber-500" />
            <span>Forensics State: Retraining Lockdown</span>
          </span>
        </div>
      </div>

      {/* Main Content Area Wrapped with Maintenance Lockdown Overlay */}
      <div className="relative rounded-2xl overflow-hidden">
        {/* Absolute Backdrop Blur Maintenance Overlay */}
        <div className="absolute inset-0 z-20 backdrop-blur-md bg-slate-900/60 dark:bg-slate-950/75 flex items-center justify-center p-6 text-center">
          <div className="max-w-lg p-6 sm:p-8 rounded-2xl bg-white/95 dark:bg-slate-900/95 border border-amber-500/40 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-200">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto shadow-inner">
              <Lock className="w-7 h-7" />
            </div>

            <div className="space-y-2">
              <span className="inline-block px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-400 text-[11px] font-mono font-bold uppercase tracking-wider">
                ⚠️ Scheduled Model Calibration
              </span>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Acoustic Forensics Engine Offline
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                The WhisperDualHead model and Conformal Calibration matrices are currently locked for retraining to improve cross-dataset Equal Error Rates (EER). Feature extraction and playback are disabled.
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-arabic leading-relaxed pt-1">
                محرك البصمة الصوتية قيد إعادة التدريب والمعايرة حالياً لتحسين دقة كشف التزييف الصوتي عبر اللهجات المتعددة. تم إيقاف الاستخراج والتشغيل مؤقتاً.
              </p>
            </div>

            <div className="pt-2 text-[11px] font-mono text-slate-500 dark:text-slate-400 border-t border-slate-200 dark:border-slate-800">
              Sovereign Model Retraining Track • Moro Hub me-central-1
            </div>
          </div>
        </div>

        {/* Existing Workbench Content (Interaction disabled underneath overlay) */}
        <div className="space-y-6 pointer-events-none select-none opacity-40">
          {/* Audio Sample Presets Selector Bar */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur p-4 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-purple-600 dark:text-purple-400" />
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
              Forensic Voice Note Presets (Select to Inspect)
            </span>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            Active Sample: <strong className="text-purple-600 dark:text-purple-400">{selectedSample.sourceType}</strong>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {AUDIO_SAMPLES.map((sample) => {
            const isSelected = selectedSample.id === sample.id;
            const isSampleSynth = sample.sourceType === "SYNTHETIC";

            return (
              <button
                key={sample.id}
                onClick={() => handleSelectSample(sample)}
                className={`p-3 rounded-lg border text-left transition relative flex flex-col justify-between ${
                  isSelected
                    ? isSampleSynth
                      ? "bg-red-50/80 dark:bg-red-950/40 border-red-400 dark:border-red-600 shadow-sm"
                      : "bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-400 dark:border-emerald-600 shadow-sm"
                    : "bg-slate-50 dark:bg-slate-950/60 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1">
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                        isSampleSynth
                          ? "bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-300"
                          : "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300"
                      }`}
                    >
                      {sample.sourceType}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">{sample.duration.split(" ")[0]}</span>
                  </div>

                  <h4 className="text-xs font-bold text-slate-900 dark:text-white line-clamp-1">
                    {sample.title}
                  </h4>
                  <p className="text-[10px] text-slate-500 dark:text-slate-400 font-sans mt-0.5 line-clamp-1">
                    {sample.arabicTitle}
                  </p>
                </div>

                <div className="mt-2 pt-2 border-t border-slate-200/50 dark:border-slate-800 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-slate-500">Anomaly:</span>
                  <span className={`font-bold ${isSampleSynth ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                    {(sample.anomalyScore * 100).toFixed(1)}%
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Spectrogram Canvas with Live Anomaly Band Highlighting */}
      <SpectrogramCanvas
        isSyntheticSample={isSynthetic}
        sampleDuration={selectedSample.duration}
        anomalyBand={selectedSample.vocoderBand}
        viewMode={canvasViewMode}
        onToggleViewMode={() => setCanvasViewMode((m) => (m === "spectrogram" ? "waveform" : "spectrogram"))}
      />

      {/* Acoustic Metrics Header & Human Baseline Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-600 dark:text-purple-400" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Acoustic Forensic Indicators (Glottal Cycle &amp; Resonances)
          </h3>
        </div>
        <button
          type="button"
          onClick={() => {
            soundFx.playClick();
            setShowBaselineComparison((prev) => !prev);
          }}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
            showBaselineComparison
              ? "bg-purple-600 text-white border-purple-600 shadow-sm"
              : "bg-white dark:bg-slate-900 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-800 hover:bg-purple-50 dark:hover:bg-purple-950/40"
          }`}
        >
          <Scale className="w-3.5 h-3.5" />
          <span>{showBaselineComparison ? "Hide Human Baseline" : "⚖️ Compare vs. Genuine Human Baseline"}</span>
        </button>
      </div>

      {/* Genuine Emirati Human Voice Acoustic Baseline Comparison Card */}
      {showBaselineComparison && (
        <div className="p-4 sm:p-5 rounded-xl border border-purple-300 dark:border-purple-800/80 bg-purple-50/70 dark:bg-purple-950/30 backdrop-blur space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-purple-200 dark:border-purple-800/60 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-purple-950 dark:text-purple-200 uppercase tracking-wider">
                  Emirati Human Voice Physiological Baseline vs. Active Audio
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-purple-200 dark:bg-purple-900 text-purple-900 dark:text-purple-200">
                  Acoustic Normalcy Reference
                </span>
              </div>
              <p className="text-[11px] text-purple-800/80 dark:text-purple-300/80 mt-0.5">
                Calibrated against verified UAE dialect voice corpora. Natural glottal pulse vibration possesses non-deterministic micro-variations that neural vocoders mathematically flatten.
              </p>
            </div>
            <div className={`px-2.5 py-1 rounded text-xs font-mono font-bold shrink-0 ${
              isSynthetic
                ? "bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-200 border border-red-300"
                : "bg-emerald-100 text-emerald-900 dark:bg-emerald-950 dark:text-emerald-200 border border-emerald-300"
            }`}>
              {isSynthetic ? "⚠️ Vocoder Anomaly Detected" : "✓ Within Normal Human Bounds"}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
            {/* Jitter Comparison */}
            <div className="p-3 rounded-lg bg-white/90 dark:bg-slate-900/90 border border-purple-200/80 dark:border-purple-900/50">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans font-semibold">Pitch Jitter (F0 Micro-tremor)</span>
              <div className="mt-1 flex items-baseline justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block">Human Baseline:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">0.78% – 0.84%</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">Sample:</span>
                  <span className={`font-bold ${isSynthetic ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                    {selectedSample.jitter.split(" ")[0]}
                  </span>
                </div>
              </div>
              <span className="text-[10px] text-slate-500 block mt-1 font-sans">
                {isSynthetic ? "Synthesized: unnaturally flat pitch contour" : "Natural glottal frequency variation"}
              </span>
            </div>

            {/* Shimmer Comparison */}
            <div className="p-3 rounded-lg bg-white/90 dark:bg-slate-900/90 border border-purple-200/80 dark:border-purple-900/50">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans font-semibold">Acoustic Shimmer (Amplitude)</span>
              <div className="mt-1 flex items-baseline justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block">Human Baseline:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">3.4% – 3.8%</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">Sample:</span>
                  <span className={`font-bold ${isSynthetic ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                    {selectedSample.shimmer.split(" ")[0]}
                  </span>
                </div>
              </div>
              <span className="text-[10px] text-slate-500 block mt-1 font-sans">
                {isSynthetic ? "Subglottic air micro-perturbations absent" : "Valid pulmonary respiration perturbations"}
              </span>
            </div>

            {/* Formants Comparison */}
            <div className="p-3 rounded-lg bg-white/90 dark:bg-slate-900/90 border border-purple-200/80 dark:border-purple-900/50">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans font-semibold">Formant Resonances (F1–F3)</span>
              <div className="mt-1 flex items-baseline justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block">Human Baseline:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">Natural Resonances</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">Sample:</span>
                  <span className={`font-bold ${isSynthetic ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                    {selectedSample.formants.split(" (")[0]}
                  </span>
                </div>
              </div>
              <span className="text-[10px] text-slate-500 block mt-1 font-sans">
                {isSynthetic ? "Linear phase vocoder artifact in F2 transitions" : "Continuous vocal tract resonances"}
              </span>
            </div>

            {/* Vocoder Anomaly Delta */}
            <div className="p-3 rounded-lg bg-white/90 dark:bg-slate-900/90 border border-purple-200/80 dark:border-purple-900/50">
              <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans font-semibold">Vocoder Discontinuity Delta</span>
              <div className="mt-1 flex items-baseline justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block">Human Target:</span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400">&lt; 0.12 (Continuous)</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block">Anomaly:</span>
                  <span className={`font-bold ${isSynthetic ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                    {isSynthetic ? "0.89 (High)" : "0.04 (Nominal)"}
                  </span>
                </div>
              </div>
              <span className="text-[10px] text-slate-500 block mt-1 font-sans">
                {isSynthetic ? "HiFi-GAN 4.8kHz–7.2kHz vocoder artifact" : "Acoustic phase spectrum continuous"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Understandable Acoustic Forensic Indicators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Feature 1: Pitch Jitter */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-4 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-purple-500" />
              Pitch Jitter (F0 Stability)
            </span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
              isSynthetic ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300" : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
            }`}>
              {isSynthetic ? "Synthetic Artifact" : "Natural Vocal"}
            </span>
          </div>
          <div className="text-base font-extrabold font-mono text-slate-900 dark:text-white">
            {selectedSample.jitter.split(" ")[0]}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
            Human vocal folds show natural cycle-to-cycle vibration instability (0.4%–1.2%). AI neural vocoders generate unnaturally rigid pitch curves (&lt; 0.1%).
          </p>
        </div>

        {/* Feature 2: Acoustic Shimmer */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-4 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Sliders className="w-4 h-4 text-cyan-500" />
              Acoustic Shimmer
            </span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
              isSynthetic ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300" : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
            }`}>
              {isSynthetic ? "Rigid Dynamics" : "Natural Breathing"}
            </span>
          </div>
          <div className="text-base font-extrabold font-mono text-slate-900 dark:text-white">
            {selectedSample.shimmer.split(" ")[0]}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
            Measures micro-variations in vocal volume between glottal pulses. Cloned audio lacks natural pulmonary subglottic air pressure micro-fluctuations.
          </p>
        </div>

        {/* Feature 3: Formant Tracking */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-4 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Layers className="w-4 h-4 text-amber-500" />
              Formants (F1 - F3)
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 font-semibold">
              Vocal Tract Shape
            </span>
          </div>
          <div className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200">
            {selectedSample.formants.split(" (")[0]}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
            Tracks physical vocal tract resonances. Synthetic text-to-speech models often exhibit unnatural mathematical spacing between F1 and F2 vowel transitions.
          </p>
        </div>

        {/* Feature 4: Vocoder Phase Discontinuity */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-4 shadow-sm transition-colors">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-red-500" />
              Vocoder Phase Anomaly
            </span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
              isSynthetic ? "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300" : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
            }`}>
              {isSynthetic ? "Watermark Detected" : "Clean Spectrum"}
            </span>
          </div>
          <div className={`text-xs font-bold font-mono ${isSynthetic ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
            {selectedSample.vocoderBand}
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
            The telltale signature of neural speech synthesis: high-frequency phase inconsistencies in the 4.8kHz–7.2kHz band caused by HiFi-GAN / diffusion vocoder vocoding.
          </p>
        </div>
      </div>

      {/* Diagnostics Grid & Whisper ASR Bilingual Transcript */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conformal Calibration Diagnostics */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-5 shadow-sm space-y-4 transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Conformal Statistical Calibration</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              Guaranteed Bound
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase">Raw Acoustic Anomaly Score</span>
              <span className={`text-lg font-extrabold ${isSynthetic ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
                {selectedSample.anomalyScore.toFixed(4)}
              </span>
              <span className="text-[10px] text-slate-500 block mt-1">Threshold: τ = 0.8500</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase">Conformal p-value</span>
              <span className="text-lg font-extrabold text-purple-600 dark:text-purple-400">
                {selectedSample.conformalPValue}
              </span>
              <span className="text-[10px] text-slate-500 block mt-1">Significance: α = 0.001</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase">Codec Compensation Profile</span>
              <span className="text-sm font-bold text-slate-800 dark:text-slate-200">{selectedSample.codec}</span>
              <span className="text-[10px] text-slate-500 block mt-1">Spectral Band Preserved</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase">Generator Attribution</span>
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300">{selectedSample.generator.split(" ")[0]}</span>
              <span className="text-[10px] text-slate-500 block mt-1">{selectedSample.duration}</span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
            <span className="font-bold text-slate-900 dark:text-white block mb-1">Mathematical Guarantee (NFR-3.1):</span>
            Under the non-parametric conformal calibration manifold, the probability of false synthetic media alarm on genuine Gulf Arabic audio is rigorously bounded by:
            <code className="text-cyan-600 dark:text-cyan-400 ml-1 font-mono font-bold">P(Flagged | Genuine) ≤ 0.1%</code>
          </div>
        </div>

        {/* Whisper ASR Transcript & Linguistic Cues */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-5 shadow-sm space-y-4 transition-colors">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Local Whisper ASR Transcript</h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
              Sub-350ms INT8
            </span>
          </div>

          {/* Bilingual Transcript Card */}
          <div className="space-y-3">
            {/* Arabic Original */}
            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-right" dir="rtl">
              <span className="text-[10px] font-mono text-slate-500 block mb-1">النص الصوتي المفرغ (العربية):</span>
              <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
                &quot;{selectedSample.arabicTranscript}&quot;
              </p>
            </div>

            {/* English Translation */}
            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] font-mono text-slate-500 block mb-1">Bilingual Translation (English):</span>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                &quot;{selectedSample.englishTranscript}&quot;
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
            <span>Social Engineering Cues: <strong>{selectedSample.socialCues}</strong></span>
            <span className={`font-mono font-bold ${isSynthetic ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}`}>
              {selectedSample.verdict} VERDICT
            </span>
          </div>
        </div>
      </div>
        </div>
      </div>
    </div>
  );
}

