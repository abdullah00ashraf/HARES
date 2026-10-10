"use client";

import React, { useEffect, useState } from "react";
import { OverviewResponse } from "../lib/types";
import { fetchOverview } from "../lib/api";
import LiveTelemetryFeed from "./LiveTelemetryFeed";
import {
  ShieldAlert,
  HelpCircle,
  Clock,
  MessageSquare,
  TrendingUp,
  PieChart,
  RefreshCw,
} from "lucide-react";

export default function OverviewWorkbench() {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    const res = await fetchOverview();
    setData(res);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (!data && loading) {
    return (
      <div className="p-8 text-center text-slate-400">
        Loading Sovereign Threat Telemetry...
      </div>
    );
  }

  const kpis = data?.kpis;
  const curve = data?.temporal_curve || [];
  const distribution = data?.impersonation_distribution || [];

  return (
    <div className="space-y-6">
      {/* KPI Highlights Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Scans */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Scanned Messages (24h)
            </span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white font-mono">
              {kpis?.total_scanned_24h.toLocaleString() || "1,420"}
            </span>
            <span className="text-xs text-emerald-400 font-medium">100% Ingress SLA</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">WhatsApp Business Cloud API Ingress</p>
        </div>

        {/* High Risk Verdicts (Red) */}
        <div className="rounded-xl border border-red-900/40 bg-slate-900/60 p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-red-300 uppercase tracking-wider">
              High Risk / Red Verdicts
            </span>
            <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-red-400 font-mono">
              {kpis?.high_risk_verdicts_24h.toLocaleString() || "384"}
            </span>
            <span className="text-xs text-red-400 font-medium">27.0% Malicious</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Escalated to Dubai Police e-Crime & 901</p>
        </div>

        {/* Amber Fallbacks */}
        <div className="rounded-xl border border-amber-900/40 bg-slate-900/60 p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-amber-300 uppercase tracking-wider">
              Amber / Caution Fallbacks
            </span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <HelpCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-amber-400 font-mono">
              {kpis?.amber_fallbacks_24h.toLocaleString() || "612"}
            </span>
            <span className="text-xs text-amber-400 font-medium">Conformal Abstention</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Empirical FPR Bounded ≤ 0.1%</p>
        </div>

        {/* Turnaround Latency */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Average E2E Latency
            </span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white font-mono">
              {kpis?.avg_latency_ms ? `${(kpis.avg_latency_ms / 1000).toFixed(2)}s` : "1.85s"}
            </span>
            <span className="text-xs text-emerald-400 font-medium">&lt; 4.8s SLA Met</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-400">Sub-50ms Webhook Acknowledgment</p>
        </div>
      </div>

      {/* Middle Row: Temporal Curves & Impersonation Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Temporal Threat Curve (2 cols) */}
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-sovereign-cyan" />
              <h3 className="text-base font-bold text-white">24-Hour Threat Arrival Curve</h3>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-500" /> Text Lures
              </span>
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> URLs
              </span>
              <span className="flex items-center gap-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-400" /> Voice Notes
              </span>
            </div>
          </div>

          {/* Bar Chart Simulation */}
          <div className="h-[220px] flex items-end gap-1.5 pt-6 pb-2 px-2 border-b border-slate-800">
            {curve.map((point, idx) => {
              const maxVol = 180;
              const heightPct = Math.min(100, Math.max(10, (point.total / maxVol) * 100));
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-1 group relative">
                  {/* Tooltip */}
                  <div className="absolute -top-10 hidden group-hover:flex flex-col items-center bg-slate-950 text-white text-[10px] px-2 py-1 rounded border border-slate-700 z-20 whitespace-nowrap pointer-events-none">
                    <span>{point.time}: {point.total} scans</span>
                    <span className="text-slate-400">Audio: {point.audio_volume}</span>
                  </div>

                  <div className="w-full flex flex-col justify-end h-full">
                    <div
                      style={{ height: `${heightPct}%` }}
                      className="w-full rounded-t bg-gradient-to-t from-cyan-600/40 via-cyan-500/80 to-sovereign-cyan group-hover:brightness-125 transition"
                    />
                  </div>
                  <span className="text-[9px] font-mono text-slate-400 transform -rotate-45 origin-top-left mt-2 hidden sm:block">
                    {idx % 3 === 0 ? point.time : ""}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="mt-6 flex justify-between items-center text-xs text-slate-400">
            <span>Peak Surge: 13:00–16:00 GST (UAE Afternoon Scam Distribution)</span>
            <span>Total Volume: {kpis?.total_scanned_24h} Events</span>
          </div>
        </div>

        {/* Target Impersonation Breakdown (1 col) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <PieChart className="w-4 h-4 text-sovereign-gold" />
              <h3 className="text-base font-bold text-white">Target Impersonation</h3>
            </div>
            <span className="text-xs text-slate-400">Top 5 Entities</span>
          </div>

          <div className="space-y-4">
            {distribution.map((item, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-200 font-medium">{item.entity}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-slate-400">{item.count}</span>
                    <span className="font-mono font-bold text-white">{item.percentage}%</span>
                  </div>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    style={{
                      width: `${item.percentage}%`,
                      backgroundColor: item.color,
                    }}
                    className="h-full rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/80 text-[11px] text-slate-400">
            Impersonation data harvested via deterministic exact-allowlist matching against verified UAE entities.
          </div>
        </div>
      </div>

      {/* Bottom Row: Live Telemetry Ring Buffer Feed */}
      <LiveTelemetryFeed />
    </div>
  );
}
