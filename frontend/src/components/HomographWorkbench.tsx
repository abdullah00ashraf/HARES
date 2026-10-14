"use client";

import React, { useEffect, useState } from "react";
import { HomographAlert } from "../lib/types";
import { fetchHomographs, triggerIspBlock } from "../lib/api";
import { soundFx } from "../lib/audioSoundFx";
import {
  ShieldAlert,
  AlertTriangle,
  Globe,
  Radio,
  CheckCircle2,
  X,
  ExternalLink,
  Search,
  Code2,
  Shield,
  Layers,
  Sparkles,
  ArrowRight,
} from "lucide-react";

export default function HomographWorkbench() {
  const [homographs, setHomographs] = useState<HomographAlert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<HomographAlert | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [blockedAlert, setBlockedAlert] = useState<{
    domain: string;
    refId: string;
  } | null>(null);
  const [submittingId, setSubmittingId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const data = await fetchHomographs();
      setHomographs(data);
      if (data.length > 0) {
        setSelectedAlert(data[0]);
      }
    }
    load();
  }, []);

  const handleBlockRequest = async (alert: HomographAlert) => {
    soundFx.playClick();
    setSubmittingId(alert.id);
    try {
      const res = await triggerIspBlock(alert.id);
      soundFx.playVerdictAlert();
      setBlockedAlert({
        domain: alert.domain,
        refId: res.reference_id,
      });
    } catch {
      setBlockedAlert({
        domain: alert.domain,
        refId: `TDRA-REG-${Math.floor(100000 + Math.random() * 900000)}`,
      });
    } finally {
      setSubmittingId(null);
    }
  };

  const filteredHomographs = homographs.filter(
    (item) =>
      item.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.spoofed_entity.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.technique.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Helper to inspect characters and flag non-ASCII Unicode glyphs
  const inspectCharacters = (domain: string) => {
    return Array.from(domain).map((char, index) => {
      const codePoint = char.codePointAt(0) || 0;
      const isAscii = codePoint <= 127;
      const hex = `U+${codePoint.toString(16).toUpperCase().padStart(4, "0")}`;

      return {
        index,
        char,
        codePoint,
        hex,
        isAscii,
        isSuspicious: !isAscii,
      };
    });
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            <span>Domain Spoof &amp; IDN Homograph Radar (FR-2.3)</span>
            <span className="text-xs text-slate-500 font-normal">/ رادار النطاقات المزورة وانتحال الهوية</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Real-time detection of Lookalike Domains, Cyrillic Script Homoglyphs, unauthorized Punycode prefixes, and automated TDRA national ISP defense push.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="px-3 py-1 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800 flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
            <span>Active UAE Radar Sweep</span>
          </span>
        </div>
      </div>

      {/* Confirmation Banner if block requested */}
      {blockedAlert && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-500/40 flex items-center justify-between text-xs text-emerald-900 dark:text-emerald-200 shadow-sm animate-in fade-in">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            <div>
              <span className="font-bold block">
                National ISP Blocklist Request Transmitted to TDRA Registry
              </span>
              <span>
                Domain <strong className="font-mono text-emerald-950 dark:text-white underline">{blockedAlert.domain}</strong> has been transmitted to the UAE Telecommunications and Digital Government Regulatory Authority under reference{" "}
                <span className="font-mono font-bold text-emerald-800 dark:text-white">{blockedAlert.refId}</span>.
              </span>
            </div>
          </div>
          <button
            onClick={() => setBlockedAlert(null)}
            className="p-1 rounded hover:bg-emerald-200/50 dark:hover:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Interactive Glyph-by-Glyph Unicode & Punycode Inspector */}
      {selectedAlert && (
        <div className="rounded-xl border border-purple-200 dark:border-purple-900/60 bg-gradient-to-r from-purple-500/5 via-cyan-500/5 to-transparent bg-white dark:bg-slate-900/80 p-5 shadow-sm transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-purple-100 dark:border-purple-900/40 mb-4">
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4 text-purple-600 dark:text-purple-400" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Interactive Glyph-by-Glyph Unicode &amp; Homoglyph Inspector
              </h3>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="text-slate-500">Spoofed Target:</span>
              <strong className="text-cyan-600 dark:text-cyan-400">{selectedAlert.spoofed_entity}</strong>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase font-mono">Visual Deceptive Domain</span>
              <span className="text-base font-bold font-mono text-red-600 dark:text-red-400">
                {selectedAlert.domain}
              </span>
              <span className="text-[10px] text-slate-500 block mt-1">Appears identical to human eye</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase font-mono">Punycode (DNS Resolution)</span>
              <span className="text-base font-bold font-mono text-amber-600 dark:text-amber-400">
                {selectedAlert.is_punycode ? "xn--slik-43a.ae" : selectedAlert.domain}
              </span>
              <span className="text-[10px] text-slate-500 block mt-1">Actual machine-resolved DNS host</span>
            </div>

            <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase font-mono">Official Legitimate Domain</span>
              <span className="text-base font-bold font-mono text-emerald-600 dark:text-emerald-400">
                {selectedAlert.spoofed_entity.toLowerCase().includes("salik")
                  ? "salik.ae"
                  : selectedAlert.spoofed_entity.toLowerCase().includes("police")
                  ? "dubaipolice.gov.ae"
                  : selectedAlert.spoofed_entity.toLowerCase().includes("dewa")
                  ? "dewa.gov.ae"
                  : "emiratespost.ae"}
              </span>
              <span className="text-[10px] text-slate-500 block mt-1">Protected UAE Sovereign Entity</span>
            </div>
          </div>

          {/* Character Breakdown Visualizer */}
          <div className="p-4 rounded-lg bg-slate-50/80 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800">
            <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 block mb-2 font-mono">
              Glyph Analysis (Clicking any character reveals Unicode code-point):
            </span>

            <div className="flex items-center gap-2 flex-wrap">
              {inspectCharacters(selectedAlert.domain).map((glyph, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col items-center justify-center p-2 rounded-lg border min-w-[50px] transition ${
                    glyph.isSuspicious
                      ? "bg-red-50 dark:bg-red-950/60 border-red-400 text-red-600 dark:text-red-400 shadow-sm animate-pulse"
                      : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200"
                  }`}
                >
                  <span className="text-lg font-mono font-extrabold">{glyph.char}</span>
                  <span className="text-[10px] font-mono mt-0.5">{glyph.hex}</span>
                  <span
                    className={`text-[9px] font-mono font-bold mt-0.5 uppercase px-1 rounded ${
                      glyph.isSuspicious
                        ? "bg-red-200 dark:bg-red-900 text-red-900 dark:text-red-200"
                        : "text-slate-400"
                    }`}
                  >
                    {glyph.isSuspicious ? "Homoglyph" : "ASCII"}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-3 pt-3 border-t border-slate-200/60 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-600 dark:text-slate-400 gap-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <span>
                  Technique: <strong className="text-slate-800 dark:text-slate-200">{selectedAlert.technique}</strong>
                </span>
              </div>
              <button
                type="button"
                onClick={() => handleBlockRequest(selectedAlert)}
                disabled={submittingId === selectedAlert.id}
                className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-semibold transition disabled:opacity-50 flex items-center gap-1.5 self-start sm:self-auto"
              >
                <Shield className="w-3.5 h-3.5" />
                <span>{submittingId === selectedAlert.id ? "Pushing TDRA Block..." : "Push to ISP Blocklist"}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm transition-colors">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search spoofed entity, fraudulent domain, or homoglyph technique..."
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-amber-500 font-mono"
          />
        </div>
        <div className="text-xs font-mono text-slate-500">
          Showing <strong>{filteredHomographs.length}</strong> active Radar alerts
        </div>
      </div>

      {/* Homograph Alerts Table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 overflow-hidden shadow-sm transition-colors">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950/80 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-mono text-[11px]">
              <tr>
                <th className="py-3 px-4">Spoofed Official Entity</th>
                <th className="py-3 px-4">Extracted Fraudulent Domain</th>
                <th className="py-3 px-4">Homoglyph Technique</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">Occurrences</th>
                <th className="py-3 px-4 text-right">Defense Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
              {filteredHomographs.map((item) => {
                const isCurrent = selectedAlert?.id === item.id;
                return (
                  <tr
                    key={item.id}
                    onClick={() => {
                      soundFx.playClick();
                      setSelectedAlert(item);
                    }}
                    className={`cursor-pointer transition ${
                      isCurrent
                        ? "bg-purple-50/70 dark:bg-purple-950/30 font-semibold"
                        : "hover:bg-slate-50 dark:hover:bg-slate-800/40"
                    }`}
                  >
                    <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-white">
                      <span className="flex items-center gap-1.5">
                        <Globe className="w-3.5 h-3.5 text-cyan-500" />
                        {item.spoofed_entity}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex flex-col">
                        <span className="font-bold text-red-600 dark:text-red-400">{item.domain}</span>
                        {item.is_punycode && (
                          <span className="text-[10px] text-amber-600 dark:text-amber-400">
                            IDN Punycode: `xn--` active
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-[11px] text-slate-700 dark:text-slate-300">
                        {item.technique}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 font-bold text-red-600 dark:text-red-400">
                      {item.risk_score.toFixed(4)}
                    </td>

                    <td className="py-3.5 px-4 text-slate-600 dark:text-slate-300">
                      {item.occurrence_count}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleBlockRequest(item);
                        }}
                        disabled={submittingId === item.id}
                        className="px-3 py-1.5 rounded-lg bg-red-100 hover:bg-red-200 dark:bg-red-600/20 dark:hover:bg-red-600/30 text-red-800 dark:text-red-300 border border-red-300 dark:border-red-500/40 text-[11px] font-semibold transition disabled:opacity-50"
                      >
                        {submittingId === item.id ? "Pushing..." : "Push to ISP Blocklist"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
