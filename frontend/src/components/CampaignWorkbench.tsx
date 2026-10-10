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
  ExternalLink,
} from "lucide-react";

export default function CampaignWorkbench() {
  const [campaigns, setCampaigns] = useState<ThreatCampaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<ThreatCampaign | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      const res = await fetchCampaigns();
      setCampaigns(res);
      setLoading(false);
    }
    load();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Flame className="w-5 h-5 text-red-500" />
            Active Municipal Campaign Tracker
          </h2>
          <p className="text-xs text-slate-400">
            Clusters high-volume distributed lures into discrete adversary operations targeting UAE entities.
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400 px-3 py-1 rounded bg-slate-900 border border-slate-800">
          Clustered Operations: {campaigns.length}
        </span>
      </div>

      {/* Campaigns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {campaigns.map((camp) => {
          let statusBadge = "bg-red-500/10 text-red-400 border-red-500/30";
          if (camp.status === "monitoring") {
            statusBadge = "bg-amber-500/10 text-amber-400 border-amber-500/30";
          } else if (camp.status === "disrupted") {
            statusBadge = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
          }

          return (
            <div
              key={camp.id}
              onClick={() => setSelectedCampaign(camp)}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg hover:border-slate-700 hover:bg-slate-900/90 transition cursor-pointer flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="text-base font-bold text-white tracking-tight">
                    {camp.name}
                  </h3>
                  <span
                    className={`text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded border ${statusBadge}`}
                  >
                    {camp.status}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-400 mb-4">
                  <Target className="w-3.5 h-3.5 text-sovereign-gold" />
                  <span>Targeted Entity:</span>
                  <span className="font-semibold text-slate-200">
                    {camp.target_entity_spoofed}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Category</span>
                    <span className="font-semibold text-slate-200 uppercase">
                      {camp.lure_type}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Submissions</span>
                    <span className="font-bold text-sovereign-cyan">
                      {camp.total_submissions}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Class A IoCs</span>
                    <span className="font-bold text-sovereign-gold">
                      {camp.indicator_count}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1 font-mono text-[11px]">
                  <Clock className="w-3 h-3" />
                  Last Seen: {new Date(camp.last_detected_at).toLocaleDateString()}
                </span>
                <span className="text-sovereign-cyan flex items-center gap-1 font-medium hover:underline">
                  Inspect Drill-Down
                  <ChevronRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Drill-Down Drawer */}
      {selectedCampaign && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end animate-fadeIn">
          <div className="w-full max-w-lg bg-slate-900 border-l border-slate-800 p-6 h-full overflow-y-auto flex flex-col justify-between shadow-2xl">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
                <div>
                  <h3 className="text-lg font-bold text-white">
                    {selectedCampaign.name}
                  </h3>
                  <span className="text-xs font-mono text-slate-400">
                    ID: {selectedCampaign.id}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedCampaign(null)}
                  className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <h4 className="font-semibold text-slate-300 mb-1">Adversary TTP Summary</h4>
                  <p className="text-slate-400 leading-relaxed bg-slate-950 p-3 rounded border border-slate-800">
                    High-volume distributed SMS and WhatsApp phishing operation impersonating{" "}
                    <strong className="text-white">{selectedCampaign.target_entity_spoofed}</strong>.
                    Directs victims to fraudulent payment portals with synthetic urgency (e.g., &quot;account frozen in 2 hours&quot;).
                  </p>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-300 mb-1">Municipal Escalation Status</h4>
                  <div className="p-3 rounded bg-red-950/20 border border-red-500/30 text-red-200">
                    Automated referral sent to Dubai Police e-Crime (`ecrime.ae`) and TDRA National Domain Defense.
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-slate-300 mb-2">Associated Class A Indicators</h4>
                  <div className="space-y-2">
                    <div className="p-2.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                      <span className="text-sovereign-gold block text-[9px] uppercase">Punycode Lookalike Domain</span>
                      xn--crm-qdd1a.ae (еcrіme.ae)
                    </div>
                    <div className="p-2.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                      <span className="text-sovereign-cyan block text-[9px] uppercase">Payment Phishing URL</span>
                      https://xn--crm-qdd1a.ae/fines/pay
                    </div>
                    <div className="p-2.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300">
                      <span className="text-emerald-400 block text-[9px] uppercase">Attacker WhatsApp Origin</span>
                      +2348039281726 (Foreign Origin Scammer Number)
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-800 flex justify-end gap-3">
              <button
                onClick={() => setSelectedCampaign(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200"
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
