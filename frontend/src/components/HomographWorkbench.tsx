"use client";

import React, { useEffect, useState } from "react";
import { HomographAlert } from "../lib/types";
import { fetchHomographs, triggerIspBlock } from "../lib/api";
import {
  ShieldAlert,
  AlertTriangle,
  Globe,
  Radio,
  CheckCircle2,
  X,
  ExternalLink,
} from "lucide-react";

export default function HomographWorkbench() {
  const [homographs, setHomographs] = useState<HomographAlert[]>([]);
  const [blockedAlert, setBlockedAlert] = useState<{
    domain: string;
    refId: string;
  } | null>(null);
  const [submittingId, setSubmittingId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const data = await fetchHomographs();
      setHomographs(data);
    }
    load();
  }, []);

  const handleBlockRequest = async (alert: HomographAlert) => {
    setSubmittingId(alert.id);
    const res = await triggerIspBlock(alert.id);
    setSubmittingId(null);
    setBlockedAlert({
      domain: alert.domain,
      refId: res.reference_id,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-sovereign-gold" />
            Domain Spoof & IDN Homograph Radar (FR-2.3)
          </h2>
          <p className="text-xs text-slate-400">
            Automated detection of Lookalike Domains, Cyrillic Script Homoglyphs, and unauthorized Punycode prefixes.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <Radio className="w-3.5 h-3.5 text-sovereign-gold animate-pulse" />
          <span>Active UAE Radar Sweep</span>
        </div>
      </div>

      {/* Confirmation Banner if block requested */}
      {blockedAlert && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 flex items-center justify-between text-xs text-emerald-200 shadow-lg">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <div>
              <span className="font-bold block">
                National ISP Blocklist Request Transmitted
              </span>
              <span>
                Domain <strong className="text-white font-mono">{blockedAlert.domain}</strong> has been pushed to the TDRA & National ISP Defense Registry under reference{" "}
                <span className="font-mono underline font-bold text-white">{blockedAlert.refId}</span>.
              </span>
            </div>
          </div>
          <button
            onClick={() => setBlockedAlert(null)}
            className="p-1 rounded hover:bg-emerald-900/40 text-emerald-400"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Homograph Alerts Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-mono text-[11px]">
              <tr>
                <th className="py-3 px-4">Spoofed Official Entity</th>
                <th className="py-3 px-4">Extracted Fraudulent Domain</th>
                <th className="py-3 px-4">Homoglyph Technique</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">Occurrences</th>
                <th className="py-3 px-4 text-right">Defense Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {homographs.map((item) => (
                <tr key={item.id} className="hover:bg-slate-850/50 transition">
                  <td className="py-3.5 px-4 font-semibold text-white">
                    <span className="flex items-center gap-1.5">
                      <Globe className="w-3.5 h-3.5 text-sovereign-cyan" />
                      {item.spoofed_entity}
                    </span>
                  </td>

                  <td className="py-3.5 px-4">
                    <div className="flex flex-col">
                      <span className="font-bold text-red-400">{item.domain}</span>
                      {item.is_punycode && (
                        <span className="text-[10px] text-amber-400">
                          IDN Punycode: `xn--` active
                        </span>
                      )}
                    </div>
                  </td>

                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300">
                      {item.technique}
                    </span>
                  </td>

                  <td className="py-3.5 px-4 font-bold text-red-400">
                    {item.risk_score.toFixed(4)}
                  </td>

                  <td className="py-3.5 px-4 text-slate-300">
                    {item.occurrence_count}
                  </td>

                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => handleBlockRequest(item)}
                      disabled={submittingId === item.id}
                      className="px-3 py-1.5 rounded-lg bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-500/40 text-[11px] font-semibold transition disabled:opacity-50"
                    >
                      {submittingId === item.id ? "Pushing..." : "Push to ISP Blocklist"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
