"use client";

import React, { useEffect, useState } from "react";
import { ThreatCampaign } from "../lib/types";
import { fetchCampaigns } from "../lib/api";
import {
  Flame,
  ShieldAlert,
  ChevronRight,
  X,
  Target,
  Clock,
  Layers,
  LayoutGrid,
  Radio,
} from "lucide-react";
import StixCampaignGraph from "./StixCampaignGraph";
import { soundFx } from "../lib/audioSoundFx";

export default function CampaignWorkbench() {
  const [campaigns, setCampaigns] = useState<ThreatCampaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<ThreatCampaign | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [viewMode, setViewMode] = useState<"table" | "graph">("table");

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await fetchCampaigns();
      setCampaigns(res);
      setLoading(false);
    }
    load();
  }, []);

  const handleSwitchView = (mode: "table" | "graph") => {
    soundFx.playClick();
    setViewMode(mode);
  };

  return (
    <div className="space-y-6">
      {/* Workbench Header & Hybrid View Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-red-500" />
            <span>Active Municipal Campaign Tracker</span>
            <span className="text-xs text-slate-500 font-normal">/ متتبع الحملات السيبرانية النشطة</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Clusters high-volume distributed lures into discrete adversary operations targeting UAE entities.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Mode Toggle Switch */}
          <div className="flex items-center p-1 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-inner">
            <button
              type="button"
              onClick={() => handleSwitchView("table")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                viewMode === "table"
                  ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Table View</span>
            </button>

            <button
              type="button"
              onClick={() => handleSwitchView("graph")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                viewMode === "graph"
                  ? "bg-purple-600 text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              }`}
            >
              <Radio className="w-3.5 h-3.5 text-purple-300" />
              <span>Attack Graph View</span>
            </button>
          </div>

          <span className="text-xs font-mono text-slate-600 dark:text-slate-400 px-3 py-1 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            Clustered Operations: {campaigns.length}
          </span>
        </div>
      </div>

      {/* View 1: Interactive Attack Graph */}
      {viewMode === "graph" && <StixCampaignGraph />}

      {/* View 2: Tactical Campaigns Table & Grid */}
      {viewMode === "table" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {campaigns.map((camp) => {
            let statusBadge = "bg-red-100 text-red-800 border-red-300 dark:bg-red-950/40 dark:text-red-400 dark:border-red-800";
            if (camp.status === "monitoring") {
              statusBadge = "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800";
            } else if (camp.status === "disrupted") {
              statusBadge = "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800";
            }

            return (
              <div
                key={camp.id}
                onClick={() => {
                  soundFx.playClick();
                  setSelectedCampaign(camp);
                }}
                className="rounded-xl p-5 border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-emerald-500 dark:hover:border-emerald-500 cursor-pointer transition shadow-sm hover:shadow group"
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <span className="text-[10px] font-mono text-slate-400 block uppercase tracking-wider">
                      {camp.id}
                    </span>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition flex items-center gap-1.5">
                      <span>{camp.name}</span>
                      <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </h3>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold uppercase border ${statusBadge}`}>
                    {camp.status}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <Target className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>Target: <strong>{camp.target_entity_spoofed}</strong></span>
                  </div>

                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <Layers className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>Lure Vector: <strong>{camp.lure_type}</strong></span>
                  </div>

                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>First Detected: {new Date(camp.first_detected_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-500">
                    IoC Count: <strong className="text-slate-800 dark:text-slate-200">{camp.indicator_count}</strong>
                  </span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-semibold group-hover:underline">
                    View STIX Graph &amp; Forensics →
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Drill-Down Drawer */}
      {selectedCampaign && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 p-6 h-full overflow-y-auto flex flex-col justify-between shadow-2xl">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800 mb-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    {selectedCampaign.name}
                  </h3>
                  <span className="text-xs font-mono text-slate-500">
                    ID: {selectedCampaign.id}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedCampaign(null)}
                  className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 hover:text-slate-800 dark:hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <h4 className="font-semibold text-slate-800 dark:text-slate-200 mb-1">Adversary TTP Summary</h4>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed bg-slate-50 dark:bg-slate-950 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                    High-volume distributed SMS and WhatsApp phishing operation impersonating{" "}
                    <strong className="text-slate-900 dark:text-white">{selectedCampaign.target_entity_spoofed}</strong>.
                    Directs victims to fraudulent payment portals with synthetic urgency (e.g., &quot;account frozen in 2 hours&quot;).
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-800 dark:text-slate-200 mb-1">Municipal Escalation Status</h4>
                  <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-500/30 text-red-800 dark:text-red-200">
                    Automated referral sent to Dubai Police e-Crime (`ecrime.ae`) and TDRA National Domain Defense.
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">Associated Class A Indicators</h4>
                  <div className="space-y-2">
                    <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-[11px] text-slate-800 dark:text-slate-300">
                      <span className="text-amber-600 dark:text-amber-400 block text-[9px] uppercase font-bold">Punycode Lookalike Domain</span>
                      xn--crm-qdd1a.ae (еcrіme.ae)
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-[11px] text-slate-800 dark:text-slate-300">
                      <span className="text-cyan-600 dark:text-cyan-400 block text-[9px] uppercase font-bold">Payment Phishing URL</span>
                      https://xn--crm-qdd1a.ae/fines/pay
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-[11px] text-slate-800 dark:text-slate-300">
                      <span className="text-emerald-600 dark:text-emerald-400 block text-[9px] uppercase font-bold">Attacker WhatsApp Origin</span>
                      +2348039281726 (Foreign Origin Scammer Number)
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-3">
              <button
                onClick={() => setSelectedCampaign(null)}
                className="px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 transition"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
