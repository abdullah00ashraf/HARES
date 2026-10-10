"use client";

import React, { useEffect, useState } from "react";
import { ThreatIndicator } from "../lib/types";
import { fetchIndicators } from "../lib/api";
import { generateCsvFeed, generateStixBundle } from "../lib/stix";
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
    loadData();
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const downloadStix = () => {
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

  const downloadCsv = () => {
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

  return (
    <div className="space-y-6">
      {/* Top Header & Export Action Buttons */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-sovereign-cyan" />
            Class A IoC Repository & Automated Defense Feeds
          </h2>
          <p className="text-xs text-slate-400">
            Persistent Indicators of Compromise harvested across Dubai triage. Zero citizen identifiers (FR-4.1).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={downloadStix}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-xs font-semibold transition"
          >
            <FileCode className="w-4 h-4" />
            <span>Export STIX 2.1</span>
          </button>

          <button
            onClick={downloadCsv}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search normalized indicator, domain, URL, or foreign phone..."
              className="w-full pl-9 pr-4 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-white font-medium border border-slate-700"
          >
            Filter
          </button>
        </form>

        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Type:</span>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none"
            >
              <option value="ALL">All Types</option>
              <option value="url">URLs</option>
              <option value="domain">Domains</option>
              <option value="phone">Foreign Numbers</option>
              <option value="bank_account">Bank Accounts</option>
              <option value="crypto_wallet">Crypto Wallets</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Verdict:</span>
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none"
            >
              <option value="ALL">All Verdicts</option>
              <option value="RED">RED (High Risk)</option>
              <option value="AMBER">AMBER (Caution)</option>
            </select>
          </div>
        </div>
      </div>

      {/* IoCs Data Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-mono text-[11px]">
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
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {indicators.map((ind) => {
                const isRed = ind.verdict === "RED";
                return (
                  <tr key={ind.id} className="hover:bg-slate-850/50 transition">
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px] uppercase">
                        {ind.indicator_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-white max-w-[340px] truncate">
                      {ind.normalized_value}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border ${
                          isRed
                            ? "bg-red-500/10 text-red-400 border-red-500/30"
                            : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                        }`}
                      >
                        {isRed ? (
                          <ShieldAlert className="w-3 h-3" />
                        ) : (
                          <HelpCircle className="w-3 h-3" />
                        )}
                        {ind.verdict}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold text-sovereign-gold">
                      {ind.risk_score.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {ind.occurrence_count}
                    </td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {new Date(ind.last_seen_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => copyToClipboard(ind.normalized_value, ind.id)}
                        className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
                        title="Copy IoC to clipboard"
                      >
                        {copiedId === ind.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
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
        <div className="p-3 bg-slate-950/60 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
          <span>Showing {indicators.length} indicators</span>
          <span>Zero Class B PII Retained</span>
        </div>
      </div>
    </div>
  );
}
