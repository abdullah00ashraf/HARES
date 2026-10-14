"use client";

import React, { useEffect, useState } from "react";
import { TelemetryEvent } from "../lib/types";
import { fetchLiveTelemetry } from "../lib/api";
import { Activity, ShieldAlert, CheckCircle2, AlertCircle, Database, RefreshCw } from "lucide-react";

const MAX_RING_BUFFER = 100; // Strict limit per Protocol Rule 11

const INITIAL_EVENTS: TelemetryEvent[] = [
  {
    id: "evt-01",
    timestamp: "10:34:22",
    payload_type: "url",
    verdict: "RED",
    rule_triggered: "idn_homograph_punycode",
    latency_ms: 1240,
    preview: "https://xn--crm-qdd1a.ae/fines/pay",
  },
  {
    id: "evt-02",
    timestamp: "10:34:18",
    payload_type: "text",
    verdict: "RED",
    rule_triggered: "slm_traffic_fine_lure",
    latency_ms: 1820,
    preview: "Dubai Police: Pay fine AED 500 within 2 hours or vehicle impound",
  },
  {
    id: "evt-03",
    timestamp: "10:34:11",
    payload_type: "audio_voice_note",
    verdict: "RED",
    rule_triggered: "aasist_conformal_deepfake",
    latency_ms: 3410,
    preview: "Voice Note: Voice clone impersonating bank security officer (24.3s)",
  },
  {
    id: "evt-04",
    timestamp: "10:34:02",
    payload_type: "url",
    verdict: "GREEN",
    rule_triggered: "allowlist_exact_match",
    latency_ms: 480,
    preview: "https://www.dewa.gov.ae/en/consumer/billing",
  },
  {
    id: "evt-05",
    timestamp: "10:33:51",
    payload_type: "text",
    verdict: "AMBER",
    rule_triggered: "conformal_abstention_novel_template",
    latency_ms: 1980,
    preview: "Unverified delivery notice without official tracking ID",
  },
];

export default function LiveTelemetryFeed() {
  const [feed, setFeed] = useState<TelemetryEvent[]>(INITIAL_EVENTS);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<string>("Active");

  const syncTelemetryFromDb = async () => {
    try {
      setIsSyncing(true);
      const liveEvents = await fetchLiveTelemetry(MAX_RING_BUFFER);
      if (liveEvents && liveEvents.length > 0) {
        setFeed((prev) => {
          // Merge unique events preserving newest first
          const existingIds = new Set(prev.map((e) => e.id));
          const newEntries = liveEvents.filter((e) => !existingIds.has(e.id));
          const combined = [...newEntries, ...prev];
          return combined.slice(0, MAX_RING_BUFFER);
        });
        setLastSyncTime(new Date().toLocaleTimeString());
      }
    } catch {
      // Graceful fallback to local ring buffer
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    syncTelemetryFromDb();
    const interval = setInterval(syncTelemetryFromDb, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-5 shadow-sm transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-500 animate-pulse" />
          <h3 className="text-base font-bold text-slate-900 dark:text-white">Live Ingress Triage Stream</h3>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            Ring Buffer ({feed.length}/{MAX_RING_BUFFER})
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs font-mono text-emerald-600 dark:text-emerald-400">
            <Database className="w-3.5 h-3.5" />
            <span>DB Synced ({lastSyncTime})</span>
          </span>
          <button
            type="button"
            onClick={syncTelemetryFromDb}
            className="p-1 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
            title="Force Telemetry Sync"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin text-cyan-500" : ""}`} />
          </button>
          <span className="text-xs text-slate-500 dark:text-slate-400">Zero Citizen PII • Class A Stream</span>
        </div>
      </div>

      <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
        {feed.map((event) => {
          let badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/30";
          let Icon = AlertCircle;
          if (event.verdict === "RED") {
            badgeColor = "bg-red-500/10 text-red-400 border-red-500/30";
            Icon = ShieldAlert;
          } else if (event.verdict === "GREEN") {
            badgeColor = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
            Icon = CheckCircle2;
          }

          return (
            <div
              key={event.id}
              className="flex items-center justify-between p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs hover:border-slate-700 transition"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="font-mono text-[11px] text-slate-400">
                  {event.timestamp}
                </span>
                <span
                  className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono font-bold text-[10px] border ${badgeColor}`}
                >
                  <Icon className="w-3 h-3" />
                  {event.verdict}
                </span>
                <span className="font-mono text-slate-400 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px]">
                  {event.payload_type}
                </span>
                <span className="text-slate-200 truncate font-mono text-[11px] max-w-[280px] sm:max-w-[420px]">
                  {event.preview}
                </span>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="font-mono text-[10px] text-slate-400">
                  {event.latency_ms}ms
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
