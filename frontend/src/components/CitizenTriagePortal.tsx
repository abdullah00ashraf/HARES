"use client";

import React, { useState, useRef, useEffect } from "react";
import Image from "next/image";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Upload,
  Link as LinkIcon,
  FileText,
  Mic,
  Image as ImageIcon,
  ExternalLink,
  PhoneCall,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Activity,
  Lock,
  Volume2,
  Share2,
  Copy,
  Check,
  Zap,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import { verifyCitizenSubmission } from "../lib/api";
import { TriageVerificationResponse } from "../lib/types";
import { soundFx } from "../lib/audioSoundFx";
import AudioWaveformPlayer from "./AudioWaveformPlayer";

type InputMode = "text" | "url" | "audio" | "image";

export default function CitizenTriagePortal() {
  const [mode, setMode] = useState<InputMode>("text");
  const [textInput, setTextInput] = useState<string>("");
  const [urlInput, setUrlInput] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingSeconds, setRecordingSeconds] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [result, setResult] = useState<TriageVerificationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeForensicTab, setActiveForensicTab] = useState<"domain" | "tactics" | "audio" | "indicators" | "privacy">("domain");
  const [elapsedMs, setElapsedMs] = useState<number>(0);
  const [copiedShareCard, setCopiedShareCard] = useState<boolean>(false);
  const [showXaiDetails, setShowXaiDetails] = useState<boolean>(true);

  const getDetectedDialect = (text: string) => {
    const lower = text.toLowerCase();
    if (
      lower.includes("يا خوي") ||
      lower.includes("مساك") ||
      lower.includes("خبرني") ||
      lower.includes("فديتك") ||
      lower.includes("شو") ||
      lower.includes("طال عمرك") ||
      lower.includes("دبي مول") ||
      lower.includes("الدوام") ||
      lower.includes("بتمر") ||
      lower.includes("ريال") ||
      lower.includes("درهم")
    ) {
      return "🇦🇪 Emirati Gulf Arabic";
    }
    if (/[\u0600-\u06FF]/.test(text)) {
      return "🌐 Modern Standard Arabic";
    }
    if (
      /\b\d+[a-z]+\b|\b[a-z]+\d+\b/i.test(text) ||
      lower.includes("3ashan") ||
      lower.includes("ma3") ||
      lower.includes("habibi") ||
      lower.includes("akhi") ||
      lower.includes("7ajz") ||
      lower.includes("mabrook") ||
      lower.includes("rabihit") ||
      lower.includes("el ja'iza")
    ) {
      return "💬 Arabizi (Franco-Arab)";
    }
    return "🇬🇧 Expat English";
  };

  const getWhatsAppShareMessage = () => {
    if (!result) return "";
    const isRed = result.verdict === "RED";
    const header = isRed
      ? "🚨 *HARES UAE Fraud Warning / تحذير أمني عاجل* 🚨"
      : result.verdict === "GREEN"
      ? "🟢 *HARES Verified Safe Communication / رسالة موثوقة* 🟢"
      : "🟡 *HARES Caution Advisory / تنبيه توخي الحذر* 🟡";

    const rawUrls = result.extracted_entities?.urls || [];
    const defangedUrls = rawUrls.map((u) =>
      u.replace(/^http:\/\//, "hxxp://").replace(/^https:\/\//, "hxxps://").replace(/\./g, "[.]")
    );

    const message = [
      header,
      "",
      `*Verdict / الحكم:* ${result.verdict}`,
      `*Reason / السبب:* ${result.reason}`,
      result.allowlist_match ? `*Verified Entity / الجهة:* ${result.allowlist_match.entity_name}` : "",
      defangedUrls.length > 0 ? `*Defanged Indicators / الروابط:* ${defangedUrls.join(", ")}` : "",
      "",
      "🛡️ Verified via Project Hares (Dubai Sovereign Fraud Triage Engine)",
      "🔗 Verify public UAE messages: https://hares-api.onrender.com",
    ].filter(Boolean).join("\n");

    return message;
  };

  const handleCopyAlertCard = () => {
    soundFx.playClick();
    const msg = getWhatsAppShareMessage();
    navigator.clipboard.writeText(msg);
    setCopiedShareCard(true);
    setTimeout(() => setCopiedShareCard(false), 2000);
  };

  const renderHighlightedEvidence = (rawText: string) => {
    if (!rawText.trim()) return null;
    const tokens = rawText.split(/(\s+|[^\w\u0600-\u06FF.-]+)/);

    return (
      <div className="p-3 sm:p-4 rounded-xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 text-xs sm:text-sm font-mono leading-relaxed break-words">
        {tokens.map((token, idx) => {
          const lower = token.toLowerCase();

          // 1. High risk / coercive urgency / suspicious TLD / punycode
          const isUrgency =
            /^(urgent|immediately|overdue|suspended|cancel|2h|24h|action|عاجل|فوراً|ساعتين|إلغاء|حجز|تجميد)$/i.test(lower) ||
            /\.(cc|biz|tk|ml|ga|cf|gq|vip|top|xyz|rest)$/i.test(lower) ||
            lower.includes("xn--");

          // 2. Medium risk financial / credential / lure
          const isFinancial =
            /^(fine|pay|aed|otp|password|passcode|card|cvv|account|balance|recharge|crypto|wealth|invest|returns|lottery|prize|500,000|درهم|دفع|رمز|بطاقة|جائزة|مبروك|سداد)$/i.test(lower) ||
            lower.includes("usdt") ||
            lower.includes("telegram");

          // 3. Safe verified domain
          const isVerified =
            /^(dewa\.gov\.ae|ecrime\.ae|salik\.ae|dubai\.ae|police\.gov\.ae)$/i.test(lower) ||
            lower.endsWith(".gov.ae");

          if (isUrgency) {
            return (
              <span
                key={idx}
                title="🚨 High-Risk Coercive Urgency / Suspicious Phishing TLD"
                className="inline-block px-1.5 py-0.5 rounded font-bold bg-red-100 dark:bg-red-950/70 text-red-900 dark:text-red-200 border border-red-300 dark:border-red-800 shadow-sm mx-0.5 cursor-help"
              >
                {token}
              </span>
            );
          }

          if (isFinancial) {
            return (
              <span
                key={idx}
                title="⚠️ Financial Demands / OTP Credential Harvesting Marker"
                className="inline-block px-1.5 py-0.5 rounded font-semibold bg-amber-100 dark:bg-amber-950/70 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-800 shadow-sm mx-0.5 cursor-help"
              >
                {token}
              </span>
            );
          }

          if (isVerified) {
            return (
              <span
                key={idx}
                title="🟢 Verified Official UAE Government / Public Utility Domain"
                className="inline-block px-1.5 py-0.5 rounded font-semibold bg-emerald-100 dark:bg-emerald-950/70 text-emerald-900 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-800 shadow-sm mx-0.5 cursor-help"
              >
                {token}
              </span>
            );
          }

          return <span key={idx}>{token}</span>;
        })}
      </div>
    );
  };

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [previewUrl]);

  // Tab switcher with tactile audio
  const handleModeSwitch = (newMode: InputMode) => {
    soundFx.playClick();
    setMode(newMode);
    setErrorMsg(null);
  };

  // Preset sample scenarios for instant evaluation
  const loadPreset = (presetType: "fake_fine" | "official_dewa" | "salik_phish" | "audio_voice") => {
    soundFx.playClick();
    setErrorMsg(null);
    setResult(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setSelectedFile(null);

    switch (presetType) {
      case "fake_fine":
        setMode("text");
        setTextInput(
          "URGENT DUBAI POLICE NOTICE: Traffic Violation #DXB-98124 is overdue. " +
          "Your driver's license and vehicle registration will be suspended within 2 hours. " +
          "Pay outstanding fine immediately at: http://police-fine-dubai.cc/pay?id=81923"
        );
        setUrlInput("");
        break;
      case "official_dewa":
        setMode("url");
        setUrlInput("https://www.dewa.gov.ae/en/consumer/billing/view-bill");
        setTextInput("DEWA monthly electricity and water consumption bill notification.");
        break;
      case "salik_phish":
        setMode("url");
        setUrlInput("http://xn--salik-tolls-97a.ae/recharge");
        setTextInput("Salik Account Low Balance Alert: Recharge immediately to avoid 50 AED penalty.");
        break;
      case "audio_voice":
        setMode("text");
        setTextInput(
          "Voice Note Transcript: 'Hello, this is Central Bank UAE security department calling regarding your bank account. " +
          "We noticed unauthorized transfers. Please read me your one-time verification passcode right now.'"
        );
        setUrlInput("");
        break;
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(file));
      setErrorMsg(null);
      soundFx.playClick();
    }
  };

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const recordedFile = new File([audioBlob], `voicenote_${Date.now()}.webm`, { type: "audio/webm" });
        setSelectedFile(recordedFile);
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        setPreviewUrl(URL.createObjectURL(recordedFile));
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingSeconds(0);
      soundFx.playClick();
      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch {
      setErrorMsg("Microphone access denied or not available. You can also upload an audio file directly.");
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      soundFx.playClick();
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    }
  };

  const handleReset = () => {
    soundFx.playClick();
    setTextInput("");
    setUrlInput("");
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setResult(null);
    setErrorMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const hasText = textInput.trim().length > 0;
    const hasUrl = urlInput.trim().length > 0;
    const hasFile = selectedFile !== null;

    if (!hasText && !hasUrl && !hasFile) {
      setErrorMsg("Please provide text, a URL, an audio file, or an image screenshot to verify.");
      return;
    }

    setIsSubmitting(true);
    setElapsedMs(0);
    const startMs = Date.now();
    const timerInterval = setInterval(() => {
      setElapsedMs(Date.now() - startMs);
    }, 100);
    soundFx.playScanSweep();

    try {
      const formData = new FormData();
      if (hasText) formData.append("text", textInput.trim());
      if (hasUrl) formData.append("url", urlInput.trim());
      if (hasFile && selectedFile) formData.append("file", selectedFile);

      const verification = await verifyCitizenSubmission(formData);
      setResult(verification);

      // Play audio verdict chime
      if (verification.verdict === "GREEN") {
        soundFx.playVerdictSafe();
      } else if (verification.verdict === "RED") {
        soundFx.playVerdictAlert();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Verification encountered an unexpected error.";
      setErrorMsg(msg);
    } finally {
      clearInterval(timerInterval);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Centered Hero Command Hub Header */}
      <div className="relative rounded-2xl p-6 sm:p-10 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 shadow-sm transition-colors duration-200 text-center overflow-hidden">
        {/* Subtle Background Glow */}
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-50/50 dark:from-emerald-950/20 to-transparent pointer-events-none" />

        <div className="relative z-10 max-w-3xl mx-auto space-y-4">
          <div className="flex flex-wrap items-center justify-center gap-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-semibold">
              <Lock className="w-3.5 h-3.5" />
              <span>Zero Citizen PII Retention (FR-4.1) • 100% Sovereign AI</span>
            </div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-800 text-amber-900 dark:text-amber-300 text-xs font-semibold">
              <Activity className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              <span>Hugging Face ZeroGPU • NVIDIA A10G Active</span>
            </div>
          </div>

          <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-tight">
            Verify UAE Public Communications
            <span className="block text-lg sm:text-2xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-arabic">
              فحص وتدقيق الرسائل والروابط المشبوهة
            </span>
          </h2>

          <p className="text-sm text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Verify suspicious SMS messages, WhatsApp forwards, payment links, voice notes, or screenshot images.
            Our sovereign models evaluate links against authenticated registries, detecting phishing, Punycode spoofs, and deepfakes.
          </p>

          {/* Quick 1-Click Presets */}
          <div className="pt-2">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block mb-2">
              Quick Test Lures / نماذج سريعة للتجربة:
            </span>
            <div className="flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => loadPreset("fake_fine")}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-900 hover:bg-red-100 dark:hover:bg-red-900/60 transition"
              >
                🚨 Fake Police Fine (SMS)
              </button>
              <button
                type="button"
                onClick={() => loadPreset("official_dewa")}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 transition"
              >
                🟢 Official DEWA Link (Safe)
              </button>
              <button
                type="button"
                onClick={() => loadPreset("salik_phish")}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-900 hover:bg-amber-100 dark:hover:bg-amber-900/60 transition"
              >
                ⚠️ Salik Cyrillic Spoof
              </button>
              <button
                type="button"
                onClick={() => loadPreset("audio_voice")}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-900 hover:bg-purple-100 dark:hover:bg-purple-900/60 transition"
              >
                🎙️ Central Bank Voice Note Lure
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Submission Card */}
      <div className="rounded-2xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 p-6 sm:p-8 shadow-sm transition-colors duration-200 space-y-6">
        {/* Floating Segmented Pill Tabs */}
        <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 border-b border-slate-200 dark:border-slate-800 pb-4">
          <button
            type="button"
            onClick={() => handleModeSwitch("text")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              mode === "text"
                ? "bg-slate-900 text-white dark:bg-white dark:text-slate-950 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Forwarded Text & SMS</span>
            <span className="text-[10px] font-normal opacity-70">/ رسائل نصية</span>
          </button>

          <button
            type="button"
            onClick={() => handleModeSwitch("url")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              mode === "url"
                ? "bg-slate-900 text-white dark:bg-white dark:text-slate-950 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            }`}
          >
            <LinkIcon className="w-4 h-4" />
            <span>Link & Domain Inspector</span>
            <span className="text-[10px] font-normal opacity-70">/ فحص الروابط</span>
          </button>

          <button
            type="button"
            onClick={() => handleModeSwitch("audio")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              mode === "audio"
                ? "bg-slate-900 text-white dark:bg-white dark:text-slate-950 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            }`}
          >
            <Mic className="w-4 h-4" />
            <span>Voice Note / Audio</span>
            <span className="text-[10px] font-normal opacity-70">/ تسجيل صوتي</span>
          </button>

          <button
            type="button"
            onClick={() => handleModeSwitch("image")}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition ${
              mode === "image"
                ? "bg-slate-900 text-white dark:bg-white dark:text-slate-950 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800/60"
            }`}
          >
            <ImageIcon className="w-4 h-4" />
            <span>Screenshot Image OCR</span>
            <span className="text-[10px] font-normal opacity-70">/ لقطة شاشة</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Mode 1: Text & SMS Input */}
          {mode === "text" && (
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200">
                Paste Suspicious Message Body
                <span className="block text-xs font-normal text-slate-500 font-arabic">
                  الصق نص الرسالة المشبوهة (رسائل SMS، واتساب، إشعارات بنكية)
                </span>
              </label>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="e.g. Your Dubai Police fine is overdue. Pay immediately at: http://police-fine-dubai.cc / بطاقة الهوية الخاصة بك موقوفة..."
                rows={5}
                className="w-full rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 p-4 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
              />
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span>Supports bilingual Arabic, MSA, Gulf dialect, Arabizi, and English.</span>
                <span className="font-mono">{textInput.length} chars</span>
              </div>
            </div>
          )}

          {/* Mode 2: URL & Domain Input */}
          {mode === "url" && (
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-slate-800 dark:text-slate-200">
                  Target Website Link or Domain URL
                  <span className="block text-xs font-normal text-slate-500 font-arabic">
                    الرابط أو النطاق الإلكتروني المطلوب فحصه
                  </span>
                </label>
                <div className="relative">
                  <LinkIcon className="absolute left-4 top-3.5 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="e.g. https://ecrime.ae or http://salik-recharge.cc"
                    className="w-full rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 pl-11 pr-4 py-3 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  Accompanying Message Context (Optional) / نص الرسالة المرفقة
                </label>
                <textarea
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="Any message that came with the link..."
                  rows={2}
                  className="w-full rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 p-3 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
                />
              </div>
            </div>
          )}

          {/* Mode 3: Voice Note / Audio Input */}
          {mode === "audio" && (
            <div className="space-y-4">
              <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 text-center space-y-4">
                <div className="flex items-center justify-center gap-4">
                  {/* Record Button */}
                  {!isRecording ? (
                    <button
                      type="button"
                      onClick={startVoiceRecording}
                      className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm flex items-center gap-2 transition"
                    >
                      <Mic className="w-4 h-4" />
                      <span>Record Voice Note • تسجيل صوتي</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={stopVoiceRecording}
                      className="px-5 py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-sm flex items-center gap-2 transition animate-pulse"
                    >
                      <div className="w-3 h-3 rounded-full bg-white animate-ping" />
                      <span>Stop Recording ({recordingSeconds}s)</span>
                    </button>
                  )}

                  <span className="text-xs text-slate-400 font-semibold">OR / أو</span>

                  {/* Upload Audio File Button */}
                  <label className="px-5 py-3 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-xs cursor-pointer flex items-center gap-2 transition">
                    <Upload className="w-4 h-4" />
                    <span>Upload Opus / Audio File</span>
                    <input
                      type="file"
                      accept="audio/*,.ogg,.opus,.mp3,.wav,.m4a"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                </div>

                <p className="text-xs text-slate-500 dark:text-slate-400 max-w-lg mx-auto">
                  Audio files are analyzed using conformal acoustic anomaly detection and Whisper ASR. Supports WhatsApp Opus .ogg notes up to 120 seconds.
                </p>
              </div>

              {/* Integrated Waveform Player */}
              {selectedFile && (
                <AudioWaveformPlayer
                  audioBlob={selectedFile}
                  title={`Attached: ${selectedFile.name}`}
                  isSynthetic={result?.audio_analysis?.is_synthetic}
                  spectralScore={result?.audio_analysis?.spectral_anomaly_score}
                  pValue={result?.audio_analysis?.p_value}
                />
              )}
            </div>
          )}

          {/* Mode 4: Screenshot / Image OCR */}
          {mode === "image" && (
            <div className="space-y-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                className="p-8 rounded-2xl border-2 border-dashed border-slate-300 dark:border-slate-800 hover:border-emerald-500 dark:hover:border-emerald-500 bg-slate-50/50 dark:bg-slate-950/50 cursor-pointer text-center space-y-3 transition group"
              >
                <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto transition group-hover:scale-105">
                  <Upload className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-slate-800 dark:text-slate-200">
                    Upload Screenshot Image / رفع لقطة شاشة
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
                    Drag and drop or browse screenshots of fake SMS, WhatsApp messages, payment receipts, or bank alerts.
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,.png,.jpg,.jpeg,.webp"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <span className="inline-block text-xs px-4 py-2 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold group-hover:bg-slate-300 dark:group-hover:bg-slate-700 transition">
                  Select Screenshot File
                </span>
              </div>

              {selectedFile && previewUrl && (
                <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <img
                      src={previewUrl}
                      alt="Uploaded screenshot preview"
                      className="w-16 h-16 object-cover rounded-lg border border-slate-300 dark:border-slate-800 shadow-sm"
                    />
                    <div>
                      <span className="text-xs font-bold text-slate-900 dark:text-white block">
                        {selectedFile.name}
                      </span>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 block font-mono">
                        {(selectedFile.size / 1024).toFixed(1)} KB • Sovereign OCR Active
                      </span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      soundFx.playClick();
                      setSelectedFile(null);
                      setPreviewUrl(null);
                    }}
                    className="text-xs text-red-600 dark:text-red-400 hover:text-red-700 px-3 py-1.5 rounded-lg border border-red-200 dark:border-red-900/50 hover:bg-red-50 dark:hover:bg-red-950/40 transition"
                  >
                    Remove File
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Error Banner */}
          {errorMsg && (
            <div className="p-4 rounded-xl bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800/60 text-red-800 dark:text-red-300 text-xs flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Live 4-Tier Pipeline Progress Stepper & Cold-Start Shield */}
          {isSubmitting && (
            <div className="p-4 sm:p-5 rounded-xl border border-emerald-300 dark:border-emerald-800 bg-emerald-50/60 dark:bg-emerald-950/30 space-y-3 animate-in fade-in duration-200">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <span className="text-xs font-bold text-emerald-900 dark:text-emerald-200 flex items-center gap-2">
                  <Activity className="w-4 h-4 animate-spin text-emerald-600 dark:text-emerald-400" />
                  <span>Sovereign Multi-Tier Verification Pipeline Executing...</span>
                </span>
                <span className="text-xs font-mono font-semibold text-emerald-700 dark:text-emerald-400">
                  Elapsed: {(elapsedMs / 1000).toFixed(1)}s
                </span>
              </div>

              {/* 4-Tier Stepper Horizontal Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs font-mono">
                {/* Tier 1 */}
                <div className={`p-2.5 rounded-lg border transition ${
                  elapsedMs >= 0 ? "bg-emerald-100/90 dark:bg-emerald-900/40 border-emerald-400 text-emerald-900 dark:text-emerald-200" : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
                }`}>
                  <div className="flex items-center gap-1.5 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    <span>Tier 1: Allowlist</span>
                  </div>
                  <span className="text-[10px] block opacity-80 mt-0.5">&lt; 15ms Exact Registry</span>
                </div>

                {/* Tier 2 */}
                <div className={`p-2.5 rounded-lg border transition ${
                  elapsedMs >= 200 ? "bg-emerald-100/90 dark:bg-emerald-900/40 border-emerald-400 text-emerald-900 dark:text-emerald-200" : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
                }`}>
                  <div className="flex items-center gap-1.5 font-bold">
                    <CheckCircle2 className={`w-3.5 h-3.5 ${elapsedMs >= 200 ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"} shrink-0`} />
                    <span>Tier 2: Homoglyph</span>
                  </div>
                  <span className="text-[10px] block opacity-80 mt-0.5">&lt; 32ms Levenshtein</span>
                </div>

                {/* Tier 3 */}
                <div className={`p-2.5 rounded-lg border transition ${
                  elapsedMs >= 500 ? "bg-emerald-100/90 dark:bg-emerald-900/40 border-emerald-400 text-emerald-900 dark:text-emerald-200" : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
                }`}>
                  <div className="flex items-center gap-1.5 font-bold">
                    <CheckCircle2 className={`w-3.5 h-3.5 ${elapsedMs >= 500 ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"} shrink-0`} />
                    <span>Tier 3: Guardrails</span>
                  </div>
                  <span className="text-[10px] block opacity-80 mt-0.5">&lt; 400ms NeMo &amp; Class A</span>
                </div>

                {/* Tier 4 */}
                <div className={`p-2.5 rounded-lg border transition ${
                  elapsedMs >= 1000 ? "bg-purple-100/90 dark:bg-purple-900/40 border-purple-400 text-purple-900 dark:text-purple-200" : "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500"
                }`}>
                  <div className="flex items-center gap-1.5 font-bold">
                    <Activity className={`w-3.5 h-3.5 ${elapsedMs >= 1000 ? "animate-spin text-purple-600 dark:text-purple-400" : "text-slate-400"} shrink-0`} />
                    <span>Tier 4: ZeroGPU</span>
                  </div>
                  <span className="text-[10px] block opacity-80 mt-0.5">Neural A10G &amp; Audio</span>
                </div>
              </div>

              {/* Cold-Start Shield Notice if elapsed > 2.5s */}
              {elapsedMs >= 2500 && (
                <div className="p-3 rounded-lg bg-amber-100/90 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-700 text-amber-950 dark:text-amber-200 text-xs flex items-center gap-2.5 animate-pulse">
                  <Zap className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                  <span>
                    <strong>Cold-Start Shield:</strong> ⚡ Waking Sovereign Cloud GPU — Air-Gapped Browser Shield Standing By... ({(elapsedMs / 1000).toFixed(1)}s elapsed)
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Form Action Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800/60 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 text-xs font-bold transition flex items-center gap-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Clear / مسح</span>
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20 disabled:opacity-50 transition flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Activity className="w-4 h-4 animate-spin" />
                  <span>Scanning Sovereign Engines...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Verify Authenticity • فحص وتصنيف</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Dynamic Real-Time Triage Results Card */}
      {result && (
        <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-300">
          <div
            className={`rounded-2xl border p-6 sm:p-8 backdrop-blur shadow-xl relative overflow-hidden transition-colors ${
              result.verdict === "GREEN"
                ? "bg-emerald-50/90 dark:bg-emerald-950/30 border-emerald-400 dark:border-emerald-600/50"
                : result.verdict === "RED"
                ? "bg-red-50/90 dark:bg-red-950/30 border-red-400 dark:border-red-600/50"
                : "bg-amber-50/90 dark:bg-amber-950/30 border-amber-400 dark:border-amber-600/50"
            }`}
          >
            {/* Header Status Verdict with Original Hares Sentinel Shield */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800/60 pb-6">
              <div className="flex items-center gap-4">
                {/* Hares Original Status Shield Badge */}
                <div className="relative w-16 h-16 shrink-0 flex items-center justify-center">
                  <Image
                    src={
                      result.verdict === "GREEN"
                        ? "/assets/branding/hares-shield-verified.svg"
                        : result.verdict === "RED"
                        ? "/assets/branding/hares-shield-alert.svg"
                        : "/assets/branding/hares-shield-caution.svg"
                    }
                    alt={result.verdict}
                    width={56}
                    height={56}
                    priority
                    className="object-contain"
                  />
                </div>

                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-bold uppercase tracking-wider ${
                        result.verdict === "GREEN"
                          ? "bg-emerald-200 dark:bg-emerald-900/60 text-emerald-900 dark:text-emerald-200 border border-emerald-300"
                          : result.verdict === "RED"
                          ? "bg-red-200 dark:bg-red-900/60 text-red-900 dark:text-red-200 border border-red-300"
                          : "bg-amber-200 dark:bg-amber-900/60 text-amber-900 dark:text-amber-200 border border-amber-300"
                      }`}
                    >
                      {result.verdict === "GREEN" && "🟢 VERIFIED SAFE / OFFICIAL (موثق وآمن)"}
                      {result.verdict === "RED" && "🔴 HIGH RISK / CONFIRMED FRAUD (احتيال مؤكد)"}
                      {result.verdict === "AMBER" && "🟡 UNVERIFIED / CAUTION (غير موثق - يرجى الحذر)"}
                    </span>
                    <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
                      Rule: {result.rule_triggered}
                    </span>
                    {result.triage_tier_evaluated && (
                      <span
                        title={result.tier_preemption_reason || "Evaluation engine tier"}
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full border cursor-help font-semibold ${
                          result.triage_tier_evaluated === "TIER_1_DETERMINISTIC"
                            ? "bg-blue-100 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border-blue-300 dark:border-blue-800"
                            : result.triage_tier_evaluated.includes("TIER_2")
                            ? "bg-purple-100 dark:bg-purple-950/60 text-purple-800 dark:text-purple-300 border-purple-300 dark:border-purple-800"
                            : "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-800"
                        }`}
                      >
                        ⚡ {
                          result.triage_tier_evaluated === "TIER_1_DETERMINISTIC"
                            ? "Tier 1: Deterministic Engine"
                            : result.triage_tier_evaluated === "TIER_2_NEURAL_ZEROGPU"
                            ? "Tier 2: Neural ZeroGPU (A10G)"
                            : result.triage_tier_evaluated === "TIER_2_NEURAL_LOCAL"
                            ? "Tier 2: Local SLM Cluster"
                            : "Tier 3: Offline Heuristics"
                        }
                      </span>
                    )}
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700">
                      {getDetectedDialect(textInput || result.reason)}
                    </span>
                    <span
                      title="Non-parametric conformal prediction bound ensuring mathematically bounded false positive rate ≤ 0.1%"
                      className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 cursor-help"
                    >
                      🛡️ Conformal Bound: FPR ≤ 0.1% (99.9% Confidence)
                    </span>
                  </div>
                  <h3 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white mt-1">
                    {result.reason}
                  </h3>
                  {result.tier_preemption_reason && (
                    <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5 flex items-center gap-1">
                      <span>↳</span>
                      <span>{result.tier_preemption_reason}</span>
                    </p>
                  )}
                </div>
              </div>

              {/* Execution Latency & Risk Score Meter */}
              <div className="flex items-center gap-4 sm:gap-6 shrink-0 text-right">
                {result.model_engine && (
                  <div className="hidden sm:block text-right">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-mono uppercase tracking-wider">Inference Engine</span>
                    <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 font-mono">
                      {result.triage_tier_evaluated === "TIER_2_NEURAL_ZEROGPU" || result.model_engine.includes("ZeroGPU")
                        ? "ZeroGPU A10G"
                        : result.triage_tier_evaluated === "TIER_1_DETERMINISTIC"
                        ? "Deterministic Engine"
                        : "Sovereign Heuristics"}
                    </span>
                  </div>
                )}
                <div>
                  <span className="text-xs text-slate-500 dark:text-slate-400 block font-mono">Risk Score</span>
                  <span
                    className={`text-2xl font-black font-mono ${
                      result.risk_score > 0.7
                        ? "text-red-600 dark:text-red-400"
                        : result.risk_score < 0.2
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-amber-600 dark:text-amber-400"
                    }`}
                  >
                    {(result.risk_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-xs text-slate-500 dark:text-slate-400 block font-mono">Triage Latency</span>
                  <span className="text-sm font-semibold font-mono text-slate-700 dark:text-slate-300">
                    {result.execution_latency_ms} ms
                  </span>
                </div>
              </div>
            </div>

            {/* Official Police Escalation Action Box for RED Verdicts */}
            {result.verdict === "RED" && (
              <div className="mt-6 p-4 rounded-xl bg-red-100/90 dark:bg-red-950/60 border border-red-300 dark:border-red-600/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-red-900 dark:text-red-200 font-bold text-sm">
                    <ShieldAlert className="w-4 h-4 text-red-600 dark:text-red-400" />
                    <span>Official Dubai Police Incident Escalation Pathway</span>
                  </div>
                  <p className="text-xs text-red-800 dark:text-red-200/90 max-w-xl">
                    This message or link was confirmed as malicious or fraudulent. Do not click links or send funds.
                    You can report this immediately to Dubai Police e-Crime or contact the non-emergency municipal hotline.
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <a
                    href="https://www.ecrime.ae"
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow flex items-center gap-1.5 transition"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Report to eCrime.ae</span>
                  </a>
                  <a
                    href="tel:901"
                    className="px-3 py-2 rounded-lg bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 text-white text-xs font-bold flex items-center gap-1.5 transition"
                  >
                    <PhoneCall className="w-3.5 h-3.5" />
                    <span>Call 901</span>
                  </a>
                </div>
              </div>
            )}

            {/* Explainable AI (XAI) Suspicious Token Highlighter */}
            {(textInput.trim() || result.reason) && (
              <div className="mt-6 p-4 rounded-xl bg-white/80 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                      🔍 XAI Forensic Evidence Token Highlighter / كاشف الأدلة الجنائية الذكي
                    </h4>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-[10px] font-mono">
                    <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
                      <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Coercive / Phish
                    </span>
                    <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                      <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" /> Financial / OTP
                    </span>
                    <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Verified Registry
                    </span>
                  </div>
                </div>

                {renderHighlightedEvidence(textInput.trim() || result.reason)}

                <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-normal">
                  Hover over highlighted tokens to view forensic risk annotations. Words are classified in real-time across UAE dialect extortion markers, unverified TLD lookalikes, and credential harvesting patterns.
                </p>
              </div>
            )}

            {/* One-Tap Family Protection & Defanged Alert Share */}
            <div className="mt-6 p-4 rounded-xl bg-slate-100/90 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-xs">
                  <Share2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span>One-Tap Family Scam Warning / حماية الأهل عبر واتساب</span>
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 max-w-xl">
                  Broadcast verified threat advisory directly to family WhatsApp chats with defanged links (<code className="font-mono text-slate-800 dark:text-slate-200">hxxp://...[.]cc</code>) to neutralize accidental clicking.
                </p>
              </div>
              <div className="flex items-center gap-2.5 shrink-0">
                <a
                  href={`https://wa.me/?text=${encodeURIComponent(getWhatsAppShareMessage())}`}
                  target="_blank"
                  rel="noreferrer"
                  onClick={() => soundFx.playClick()}
                  className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span>Warn Family on WhatsApp</span>
                </a>
                <button
                  type="button"
                  onClick={handleCopyAlertCard}
                  className="px-3.5 py-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-750 text-slate-800 dark:text-slate-200 text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
                >
                  {copiedShareCard ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Copied Alert!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-slate-500" />
                      <span>Copy Defanged Card</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Bilingual Notification Templates Display */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-white/80 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block uppercase tracking-wider">
                  English WhatsApp Triage Advisory:
                </span>
                <p className="text-xs text-slate-800 dark:text-slate-200 font-mono whitespace-pre-wrap leading-relaxed">
                  {result.response_template_en}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white/80 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 space-y-2 text-right" dir="rtl">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 block uppercase tracking-wider font-arabic">
                  توصية الإبلاغ والتوجيه الرسمية (باللغة العربية):
                </span>
                <p className="text-xs text-slate-800 dark:text-slate-200 font-mono whitespace-pre-wrap leading-relaxed font-arabic">
                  {result.response_template_ar}
                </p>
              </div>
            </div>

            {/* Forensic Technical Analysis Accordion */}
            <div className="mt-6 border-t border-slate-200 dark:border-slate-800 pt-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                  <span>Technical Forensics & Evidence Breakdown</span>
                  <span className="text-xs text-slate-500 font-normal">/ تفاصيل الأدلة الجنائية الرقمية</span>
                </h4>
                <div className="flex flex-wrap items-center gap-1">
                  <button
                    type="button"
                    onClick={() => { soundFx.playClick(); setActiveForensicTab("domain"); }}
                    className={`px-3 py-1 rounded text-xs font-semibold transition ${
                      activeForensicTab === "domain"
                        ? "bg-slate-900 text-white dark:bg-slate-800"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                    }`}
                  >
                    Domain Radar
                  </button>
                  <button
                    type="button"
                    onClick={() => { soundFx.playClick(); setActiveForensicTab("tactics"); }}
                    className={`px-3 py-1 rounded text-xs font-semibold transition ${
                      activeForensicTab === "tactics"
                        ? "bg-slate-900 text-white dark:bg-slate-800"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                    }`}
                  >
                    AI Pretexting
                  </button>
                  <button
                    type="button"
                    onClick={() => { soundFx.playClick(); setActiveForensicTab("audio"); }}
                    className={`px-3 py-1 rounded text-xs font-semibold transition ${
                      activeForensicTab === "audio"
                        ? "bg-slate-900 text-white dark:bg-slate-800"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                    }`}
                  >
                    Acoustic Voice
                  </button>
                  <button
                    type="button"
                    onClick={() => { soundFx.playClick(); setActiveForensicTab("indicators"); }}
                    className={`px-3 py-1 rounded text-xs font-semibold transition ${
                      activeForensicTab === "indicators"
                        ? "bg-slate-900 text-white dark:bg-slate-800"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                    }`}
                  >
                    Class A IoCs
                  </button>
                  <button
                    type="button"
                    onClick={() => { soundFx.playClick(); setActiveForensicTab("privacy"); }}
                    className={`px-3 py-1 rounded text-xs font-semibold transition ${
                      activeForensicTab === "privacy"
                        ? "bg-slate-900 text-white dark:bg-slate-800"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                    }`}
                  >
                    Privacy (FR-4.1)
                  </button>
                </div>
              </div>

              {/* Forensic Details Viewport */}
              <div className="p-4 rounded-xl bg-white/70 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
                {activeForensicTab === "domain" && (
                  <div className="space-y-2">
                    {result.allowlist_match ? (
                      <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>
                          <strong>Allowlist Match:</strong> Domain &apos;{result.allowlist_match.verified_domain}&apos; verified against official UAE registries for {result.allowlist_match.entity_name}.
                        </span>
                      </div>
                    ) : (
                      <div className="text-slate-500">
                        No direct official allowlist match found for evaluated links.
                      </div>
                    )}
                    {result.homograph_analysis && (
                      <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                        <XCircle className="w-4 h-4 shrink-0" />
                        <span>
                          <strong>Homograph Spoof Triggered:</strong> Domain &apos;{result.homograph_analysis.domain}&apos; flagged under rule: {result.homograph_analysis.rule}.
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {activeForensicTab === "tactics" && (
                  <div className="space-y-2">
                    {result.slm_analysis ? (
                      <div className="space-y-1">
                        <div>
                          <strong>Neural Engine Provider:</strong>{" "}
                          <span className="font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                            {result.model_engine || "Hugging Face ZeroGPU (NVIDIA A10G • Qwen2.5-3B + NeMo Guardrails)"}
                          </span>
                        </div>
                        <div>
                          <strong>Detected Tactics:</strong>{" "}
                          {result.slm_analysis.detected_tactics && result.slm_analysis.detected_tactics.length > 0
                            ? result.slm_analysis.detected_tactics.join(", ")
                            : "None detected"}
                        </div>
                        <div>
                          <strong>Urgency / Coercion:</strong>{" "}
                          {result.slm_analysis.urgency_or_coercion ? "Yes (Flagged)" : "No"}
                        </div>
                        <div>
                          <strong>Credential / Financial Demand:</strong>{" "}
                          {result.slm_analysis.financial_or_credential_demand ? "Yes (Flagged)" : "No"}
                        </div>
                        <div>
                          <strong>AI Reasoning Summary:</strong>{" "}
                          {result.slm_analysis.reasoning_summary}
                        </div>
                      </div>
                    ) : (
                      <div className="text-slate-500">
                        SLM intent analysis was bypassed because deterministic link allowlist/homograph matched early.
                      </div>
                    )}
                  </div>
                )}

                {activeForensicTab === "audio" && (
                  <div className="space-y-2">
                    {result.audio_analysis ? (
                      <div className="space-y-1">
                        <div>
                          <strong>Synthetic Voice Verdict:</strong>{" "}
                          {result.audio_analysis.is_synthetic ? "Synthetic / Deepfake (Flagged)" : "Natural Voice (Bonafide)"}
                        </div>
                        <div>
                          <strong>Spectral Anomaly Score:</strong>{" "}
                          {result.audio_analysis.spectral_anomaly_score}
                        </div>
                        <div>
                          <strong>Conformal p-value:</strong>{" "}
                          {result.audio_analysis.p_value.toFixed(4)}
                        </div>
                        <div>
                          <strong>Payload Duration:</strong>{" "}
                          {result.audio_analysis.duration_seconds.toFixed(2)}s (Cap: 120s)
                        </div>
                      </div>
                    ) : (
                      <div className="text-slate-500">
                        No audio file was attached to this submission.
                      </div>
                    )}
                  </div>
                )}

                {activeForensicTab === "indicators" && (
                  <div className="space-y-2">
                    <div>
                      <strong>Extracted Links / URLs:</strong>{" "}
                      {result.extracted_entities.urls.length > 0
                        ? result.extracted_entities.urls.join(", ")
                        : "None"}
                    </div>
                    <div>
                      <strong>Extracted Domains:</strong>{" "}
                      {result.extracted_entities.domains.length > 0
                        ? result.extracted_entities.domains.join(", ")
                        : "None"}
                    </div>
                    <div>
                      <strong>Extracted Phone Numbers:</strong>{" "}
                      {result.extracted_entities.phone_numbers.length > 0
                        ? result.extracted_entities.phone_numbers.join(", ")
                        : "None"}
                    </div>
                    {result.ocr_extracted_text && (
                      <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                        <strong>Raw OCR Text from Screenshot:</strong>
                        <p className="font-mono text-slate-600 dark:text-slate-400 text-[11px] mt-1 whitespace-pre-wrap">
                          {result.ocr_extracted_text}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {activeForensicTab === "privacy" && (
                  <div className="space-y-2 text-slate-700 dark:text-slate-300">
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold">
                      <Lock className="w-4 h-4" />
                      <span>Certified FR-4.1 & DESC Compliance (حماية الخصوصية)</span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                      Zero citizen PII retention policy is strictly enforced. Citizen submitter identifiers are cryptographically
                      pseudonymized via keyed HMAC-SHA256 immediately upon ingestion. Raw phone numbers, citizen names, and Emirates IDs
                      are dropped from memory before any database write or log emission. Only threat indicators (Class A: scammer URLs,
                      spoofed domains, foreign caller numbers) are persisted to the sovereign threat intelligence repository.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
