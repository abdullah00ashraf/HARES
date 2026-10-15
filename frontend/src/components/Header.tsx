"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import {
  ShieldCheck,
  Server,
  Lock,
  Unlock,
  KeyRound,
  Eye,
  EyeOff,
  AlertCircle,
  X,
  Activity,
  Sun,
  Moon,
  Volume2,
  VolumeX,
} from "lucide-react";
import { usePortalMode } from "../lib/PortalModeContext";
import { useTheme } from "../lib/ThemeContext";
import { soundFx } from "../lib/audioSoundFx";

export default function Header() {
  const { portalMode, setPortalMode, isAdminAuthenticated, loginAdmin, logoutAdmin } = usePortalMode();
  const { theme, toggleTheme } = useTheme();
  const [dubaiTime, setDubaiTime] = useState<string>("");
  const [isMuted, setIsMuted] = useState<boolean>(true);

  // Authentication Modal State
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [adminPassword, setAdminPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    // Sound FX state
    setIsMuted(soundFx.isMuted);
    const unsub = soundFx.subscribe((muted) => setIsMuted(muted));

    // Dubai Time (GST UTC+4)
    const updateTime = () => {
      const now = new Date();
      const options: Intl.DateTimeFormatOptions = {
        timeZone: "Asia/Dubai",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      };
      setDubaiTime(new Intl.DateTimeFormat("en-GB", options).format(now));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);

    return () => {
      unsub();
      clearInterval(interval);
    };
  }, []);

  const handlePortalSwitch = (mode: "citizen" | "soc") => {
    soundFx.playClick();
    if (mode === "soc") {
      if (isAdminAuthenticated) {
        setPortalMode("soc");
      } else {
        setAuthError(null);
        setAdminPassword("");
        setIsAuthModalOpen(true);
      }
    } else {
      setPortalMode("citizen");
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminPassword.trim()) {
      setAuthError("Please enter the master admin passkey.");
      return;
    }
    const success = await loginAdmin(adminPassword);
    if (success) {
      soundFx.playVerdictSafe();
      setIsAuthModalOpen(false);
      setAdminPassword("");
      setAuthError(null);
      setPortalMode("soc");
    } else {
      soundFx.playVerdictAlert();
      setAuthError("Access Denied: Invalid Security Clearance Passkey (DESC / Dubai Police NFR-1.3).");
    }
  };

  const handleThemeToggle = () => {
    soundFx.playClick();
    toggleTheme();
  };

  const handleSoundToggle = () => {
    soundFx.toggleMute();
  };

  return (
    <>
      {/* Independent Open-Source Advisory Ribbon Banner */}
      <aside
        aria-label="Independent Open Source Public Advisory"
        className="bg-amber-500/10 dark:bg-amber-500/15 border-b border-amber-500/20 text-amber-950 dark:text-amber-200 text-[11px] sm:text-xs px-4 py-1.5 transition-colors"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-center flex-wrap">
          <span className="inline-flex items-center gap-1 font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/20 dark:bg-amber-500/30 text-amber-950 dark:text-amber-200 text-[10px] font-mono border border-amber-500/30">
            <AlertCircle className="w-3 h-3 text-amber-600 dark:text-amber-400" />
            Independent Open Source
          </span>
          <span className="font-medium text-slate-800 dark:text-slate-200">
            Project Hares is an independent open-source cybersecurity project — not an official government agency or official state website.
          </span>
          <span className="hidden md:inline text-amber-800/80 dark:text-amber-300/80 font-arabic text-xs">
            (مشروع بحثي مستقل ومفتوح المصدر لمكافحة الاحتيال، وليس جهة أو موقعاً حكومياً رسمياً)
          </span>
        </div>
      </aside>

      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md px-4 sm:px-6 py-3.5 sticky top-0 z-50 transition-colors duration-200 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 sm:gap-4">
          {/* Project Hares Sovereign Branding */}
          <div className="flex items-center gap-3">
            <div className="relative w-10 h-10 shrink-0 rounded-lg p-1 bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-center">
              {/* Original Project Hares Falcon Sentinel Logo */}
              <Image
                src="/assets/branding/hares-logo.svg"
                alt="Project Hares Sentinel"
                width={34}
                height={34}
                priority
                className="object-contain"
              />
            </div>

            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                  PROJECT HARES
                </h1>
                <span className="text-xs px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 font-bold border border-amber-300 dark:border-amber-800 font-arabic">
                  مشروع حارس
                </span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-mono border border-emerald-300 dark:border-emerald-800">
                  SOVEREIGN
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                UAE Independent Cyber Threat Triage & Public Fraud Intelligence Platform
              </p>
            </div>
          </div>

          {/* Portal Switcher Buttons (Citizen vs SOC Admin) */}
          <div className="flex items-center gap-2 flex-wrap self-start lg:self-auto">
            <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 shadow-inner">
              <button
                type="button"
                onClick={() => handlePortalSwitch("citizen")}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all duration-150 ${
                  portalMode === "citizen"
                    ? "bg-emerald-600 dark:bg-emerald-600 text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-white dark:hover:bg-slate-900/60"
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <div className="flex flex-col text-left leading-tight">
                  <span>Citizen Verification</span>
                  <span className="text-[9px] font-normal opacity-90">بوابة فحص البلاغات</span>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handlePortalSwitch("soc")}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all duration-150 ${
                  portalMode === "soc"
                    ? "bg-slate-800 dark:bg-slate-800 text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-white dark:hover:bg-slate-900/60"
                }`}
              >
                {isAdminAuthenticated ? (
                  <Activity className="w-4 h-4 text-cyan-400" />
                ) : (
                  <Lock className="w-4 h-4 text-amber-500 dark:text-amber-400" />
                )}
                <div className="flex flex-col text-left leading-tight">
                  <span className="flex items-center gap-1.5">
                    SOC Analyst Hub
                    {!isAdminAuthenticated && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-amber-500/20 text-amber-600 dark:text-amber-300 font-mono">
                        LOCKED
                      </span>
                    )}
                  </span>
                  <span className="text-[9px] font-normal opacity-90">لوحة العمليات والتحليل</span>
                </div>
              </button>
            </div>

            {/* Lock SOC Hub Action (Visible when in SOC mode) */}
            {portalMode === "soc" && (
              <button
                type="button"
                onClick={() => {
                  soundFx.playClick();
                  logoutAdmin();
                }}
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800/60 text-xs font-bold transition hover:bg-rose-100 dark:hover:bg-rose-900/40 shadow-sm"
                title="Lock SOC Analyst Hub and return to Citizen Verification"
              >
                <Lock className="w-3.5 h-3.5 text-rose-500" />
                <span>Lock SOC</span>
              </button>
            )}
          </div>

          {/* Actions & Telemetry Bar: Theme, Audio, Status */}
          <div className="flex items-center gap-2 text-xs flex-wrap">
            {/* Theme Toggle (Light / Dark) */}
            <button
              type="button"
              onClick={handleThemeToggle}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 transition"
              title={`Switch to ${theme === "light" ? "Dark" : "Light"} Mode`}
            >
              {theme === "light" ? (
                <>
                  <Moon className="w-3.5 h-3.5 text-indigo-600" />
                  <span className="font-medium text-[11px]">Dark Mode</span>
                </>
              ) : (
                <>
                  <Sun className="w-3.5 h-3.5 text-amber-400" />
                  <span className="font-medium text-[11px]">Light Mode</span>
                </>
              )}
            </button>

            {/* Sound FX Toggle */}
            <button
              type="button"
              onClick={handleSoundToggle}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border transition text-[11px] font-medium ${
                isMuted
                  ? "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:text-slate-800"
                  : "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800 shadow-sm"
              }`}
              title={isMuted ? "Unmute UI Audio SFX" : "Mute UI Audio SFX"}
            >
              {isMuted ? (
                <>
                  <VolumeX className="w-3.5 h-3.5" />
                  <span>Audio Muted</span>
                </>
              ) : (
                <>
                  <Volume2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Audio Active</span>
                </>
              )}
            </button>

            {/* Sovereign Local Telemetry Clock */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 font-mono text-[11px] text-slate-700 dark:text-slate-300">
              <Activity className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 animate-pulse" />
              <span>GST: {dubaiTime || "12:00:00"}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Municipal Security Clearance Modal */}
      {isAuthModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 sm:p-8 space-y-6 overflow-hidden">
            {/* Top Close Button */}
            <button
              type="button"
              onClick={() => {
                soundFx.playClick();
                setIsAuthModalOpen(false);
                setAuthError(null);
                setAdminPassword("");
              }}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Modal Header */}
            <div className="text-center space-y-2">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-950/60 border border-amber-300 dark:border-amber-800 text-amber-700 dark:text-amber-300 mb-1">
                <Lock className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-extrabold text-slate-900 dark:text-white tracking-tight">
                Municipal Security Clearance Required
                <span className="block text-sm font-bold text-amber-600 dark:text-amber-400 font-arabic mt-0.5">
                  تصريح أمني مطلوب للدخول
                </span>
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
                Restricted to Dubai Cyber Security Council (DESC), Dubai Police, and authorized incident response personnel.
              </p>
            </div>

            {/* Authentication Form */}
            <form onSubmit={handleAuthSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Master SOC Admin Passkey
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={adminPassword}
                    onChange={(e) => {
                      setAdminPassword(e.target.value);
                      if (authError) setAuthError(null);
                    }}
                    placeholder="Enter admin security passkey..."
                    autoFocus
                    className="w-full pl-9 pr-10 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 transition font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Error Banner */}
              {authError && (
                <div className="flex items-start gap-2 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>{authError}</span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    soundFx.playClick();
                    setIsAuthModalOpen(false);
                    setAuthError(null);
                    setAdminPassword("");
                  }}
                  className="w-1/3 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-2/3 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition shadow-sm flex items-center justify-center gap-1.5"
                >
                  <Unlock className="w-4 h-4" />
                  <span>Authenticate & Enter</span>
                </button>
              </div>
            </form>

            {/* Compliance Footer Note */}
            <p className="text-[10px] text-center text-slate-400 dark:text-slate-500 font-mono">
              Protected under DESC &amp; Project Hares Sovereign Access Control
            </p>
          </div>
        </div>
      )}
    </>
  );
}
