"use client";

import React, { useEffect, useState } from "react";
import { ThreatIndicator } from "../lib/types";
import { fetchIndicators, fetchServerStixExport, fetchServerCsvExport } from "../lib/api";
import { generateCsvFeed, generateStixBundle } from "../lib/stix";
import { soundFx } from "../lib/audioSoundFx";
import {
  Database,
  Download,
  Filter,
  Search,
  Copy,
  Check,
  ShieldAlert,
  HelpCircle,
  FileCode,
  FileSpreadsheet,
  Globe,
  Phone,
  Radio,
  Lock,
} from "lucide-react";

export default function IocWorkbench() {
  const [indicators, setIndicators] = useState<ThreatIndicator[]>([]);
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [verdictFilter, setVerdictFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    const data = await fetchIndicators({
      indicator_type: typeFilter,
      verdict: verdictFilter,
      search: searchQuery,
    });
    setIndicators(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [typeFilter, verdictFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    soundFx.playClick();
    loadData();
  };

  const copyToClipboard = (text: string, id: string) => {
    soundFx.playClick();
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const downloadStix = async () => {
    soundFx.playClick();
    try {
      const serverBundle = await fetchServerStixExport();
      const blob = new Blob([serverBundle], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "hares_stix21_feed.json";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      return;
    } catch {
      // Fallback to client-side STIX bundle generator
    }
    const jsonStr = generateStixBundle(indicators);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "hares_stix21_feed.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadCsv = async () => {
    soundFx.playClick();
    try {
      const serverCsv = await fetchServerCsvExport();
      const blob = new Blob([serverCsv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "hares_threat_indicators.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      return;
    } catch {
      // Fallback to client-side CSV generator
    }
    const csvStr = generateCsvFeed(indicators);
    const blob = new Blob([csvStr], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "hares_threat_indicators.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const redCount = indicators.filter((i) => i.verdict === "RED").length;
  const amberCount = indicators.filter((i) => i.verdict === "AMBER").length;
  const domainsUrlsCount = indicators.filter((i) =>
    ["domain", "url"].includes(i.indicator_type)
  ).length;

  return (
    <div className="space-y-6">
      {/* Top Header & Export Action Buttons */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
            <span>Class A IoC Repository &amp; Automated Defense Feeds</span>
            <span className="text-xs text-slate-500 font-normal">/ مستودع مؤشرات الاختراق</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Persistent Indicators of Compromise harvested across Dubai municipal triage. Zero citizen identifiers retained (FR-4.1).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={downloadStix}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-50 dark:bg-cyan-950/40 hover:bg-cyan-100 dark:hover:bg-cyan-900/50 text-cyan-800 dark:text-cyan-300 border border-cyan-300 dark:border-cyan-800 text-xs font-semibold transition"
          >
            <FileCode className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
            <span>Export STIX 2.1</span>
          </button>

          <button
            onClick={downloadCsv}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-semibold transition"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Live IoC Telemetry Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm transition-colors">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
            Total Class A Indicators
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900 dark:text-white font-mono">
              {indicators.length}
            </span>
            <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">Postgres Persisted</span>
          </div>
          <span className="text-[10px] text-slate-400 block mt-1">Zero PII / HMAC-SHA256 isolated</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm transition-colors">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
            High Risk (RED) Verdicts
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-red-600 dark:text-red-400 font-mono">
              {redCount}
            </span>
            <span className="text-xs text-red-600 dark:text-red-400 font-medium">Critical Threat</span>
          </div>
          <span className="text-[10px] text-slate-400 block mt-1">Directly pushed to Dubai e-Crime</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm transition-colors">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
            Phishing Domains &amp; URLs
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-purple-600 dark:text-purple-400 font-mono">
              {domainsUrlsCount}
            </span>
            <span className="text-xs text-purple-600 dark:text-purple-400 font-medium">Lookalikes / IDN</span>
          </div>
          <span className="text-[10px] text-slate-400 block mt-1">Active Punycode radar interception</span>
        </div>

        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm transition-colors">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
            Defense Feed Standardization
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-cyan-600 dark:text-cyan-400 font-mono">
              STIX 2.1
            </span>
            <span className="text-xs text-cyan-600 dark:text-cyan-400 font-medium">TAXII 2.1 Ready</span>
          </div>
          <span className="text-[10px] text-slate-400 block mt-1">OASIS Open CTI Compliant</span>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 transition-colors">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search normalized indicator, domain, URL, or foreign phone..."
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs text-slate-800 dark:text-white font-medium border border-slate-200 dark:border-slate-700"
          >
            Filter
          </button>
        </form>

        <div className="flex items-center gap-3 text-xs flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 dark:text-slate-400 font-medium">Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-800 dark:text-white focus:outline-none font-mono"
            >
              <option value="ALL">All Types</option>
              <option value="url">Phishing URLs</option>
              <option value="domain">Lookalike Domains</option>
              <option value="phone">Foreign Numbers</option>
              <option value="bank_account">Bank Accounts</option>
              <option value="crypto_wallet">Crypto Wallets</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-500 dark:text-slate-400 font-medium">Verdict:</span>
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-800 dark:text-white focus:outline-none font-mono"
            >
              <option value="ALL">All Verdicts</option>
              <option value="RED">RED (High Risk)</option>
              <option value="AMBER">AMBER (Caution)</option>
            </select>
          </div>
        </div>
      </div>

      {/* IoCs Data Table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 overflow-hidden shadow-sm transition-colors">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950/80 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-mono text-[11px]">
              <tr>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Normalized Class A Value</th>
                <th className="py-3 px-4">Verdict</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">Occurrences</th>
                <th className="py-3 px-4">Last Seen</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono">
              {indicators.map((ind) => {
                const isRed = ind.verdict === "RED";
                return (
                  <tr key={ind.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 text-[10px] uppercase font-bold">
                        {ind.indicator_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white max-w-[340px] truncate">
                      {ind.normalized_value}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${
                          isRed
                            ? "bg-red-50 text-red-700 border-red-300 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/30"
                            : "bg-amber-50 text-amber-700 border-amber-300 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/30"
                        }`}
                      >
                        {isRed ? (
                          <ShieldAlert className="w-3 h-3 text-red-500" />
                        ) : (
                          <HelpCircle className="w-3 h-3 text-amber-500" />
                        )}
                        {ind.verdict}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold text-amber-600 dark:text-amber-400">
                      {ind.risk_score.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-slate-600 dark:text-slate-300">
                      {ind.occurrence_count}
                    </td>
                    <td className="py-3 px-4 text-slate-500 dark:text-slate-400 text-[11px]">
                      {new Date(ind.last_seen_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => copyToClipboard(ind.normalized_value, ind.id)}
                        className="p-1.5 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition"
                        title="Copy IoC to clipboard"
                      >
                        {copiedId === ind.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-500" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="p-3 bg-slate-50 dark:bg-slate-950/60 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center text-xs text-slate-500 dark:text-slate-400">
          <span>Showing <strong>{indicators.length}</strong> verified indicators</span>
          <span className="flex items-center gap-1">
            <Lock className="w-3 h-3 text-emerald-500" />
            <span>Zero Class B Citizen PII Retained</span>
          </span>
        </div>
      </div>
    </div>
  );
}
