"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import { ShieldCheck, Server, Lock, Activity, Sun, Moon, Volume2, VolumeX } from "lucide-react";
import { usePortalMode } from "../lib/PortalModeContext";
import { useTheme } from "../lib/ThemeContext";
import { soundFx } from "../lib/audioSoundFx";

export default function Header() {
  const { portalMode, setPortalMode } = usePortalMode();
  const { theme, toggleTheme } = useTheme();
  const [dubaiTime, setDubaiTime] = useState<string>("");
  const [isMuted, setIsMuted] = useState<boolean>(true);

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
    setPortalMode(mode);
  };

  const handleThemeToggle = () => {
    soundFx.playClick();
    toggleTheme();
  };

  const handleSoundToggle = () => {
    soundFx.toggleMute();
  };

  return (
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
        <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 shadow-inner self-start lg:self-auto">
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
            <Activity className="w-4 h-4 text-cyan-500 dark:text-cyan-400" />
            <div className="flex flex-col text-left leading-tight">
              <span>SOC Analyst Hub</span>
              <span className="text-[9px] font-normal opacity-90">لوحة العمليات والتحليل</span>
            </div>
          </button>
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
  );
}
