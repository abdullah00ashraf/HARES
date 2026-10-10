"use client";

import React, { useEffect, useState } from "react";
import { ShieldCheck, Server, Lock, Radio, Activity } from "lucide-react";

export default function Header() {
  const [dubaiTime, setDubaiTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      // Dubai is UTC+4
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
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 py-4 sticky top-0 z-50">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Brand & Mission Title */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-sovereign-gold/10 border border-sovereign-gold/30 flex items-center justify-center text-sovereign-gold font-bold text-xl">
            ح
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white">PROJECT HARES</h1>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                مشروع حارس
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-sovereign-gold/20 text-sovereign-gold font-mono border border-sovereign-gold/40">
                v1.4.0-phase4
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Dubai Municipal Threat Intelligence & Automated WhatsApp Fraud Triage Operations
            </p>
          </div>
        </div>

        {/* Sovereign Telemetry Status Badges */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-slate-300">
            <Server className="w-3.5 h-3.5 text-sovereign-emerald" />
            <span>Sovereign Local Compute</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-slate-300">
            <Lock className="w-3.5 h-3.5 text-sovereign-cyan" />
            <span>Meta UAE Data Storage</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-sovereign-gold" />
            <span>Conformal FPR ≤ 0.1%</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700 font-mono text-slate-300">
            <Activity className="w-3.5 h-3.5 text-sovereign-emerald animate-pulse" />
            <span>GST: {dubaiTime || "10:30:00"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
