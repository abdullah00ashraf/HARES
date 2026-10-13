"use client";

import React, { useState } from "react";
import Image from "next/image";
import { AlertTriangle, ArrowRight, Shield, Globe, Radio, ExternalLink } from "lucide-react";

interface GraphNode {
  id: string;
  type: "campaign" | "target" | "lure" | "indicator" | "sink";
  label: string;
  sublabel: string;
  iconSrc: string;
  x: number;
  y: number;
  color: string;
  details: {
    stixId: string;
    confidence: number;
    firstSeen: string;
    tactic: string;
    indicators: string[];
  };
}

interface GraphLink {
  source: string;
  target: string;
  label: string;
}

export default function StixCampaignGraph() {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Nodes for Operation Salik Mirage
  const nodes: GraphNode[] = [
    {
      id: "node-campaign",
      type: "campaign",
      label: "Campaign: Salik Mirage",
      sublabel: "حملة انتحال سالك",
      iconSrc: "/assets/stix/stix-campaign.svg",
      x: 80,
      y: 140,
      color: "#8B5CF6",
      details: {
        stixId: "campaign--8f20a4b1-9124-4f01",
        confidence: 0.98,
        firstSeen: "2026-10-09 14:22 UTC",
        tactic: "T1566.002 Spearphishing Link",
        indicators: ["sаlik.ae", "salik-portal.net"],
      },
    },
    {
      id: "node-target",
      type: "target",
      label: "Target: Salik Dubai Tolls",
      sublabel: "الجهة المستهدفة: سالك",
      iconSrc: "/assets/stix/stix-threat-actor.svg",
      x: 280,
      y: 60,
      color: "#F59E0B",
      details: {
        stixId: "identity--salik-gov-ae",
        confidence: 0.99,
        firstSeen: "2026-10-09 14:22 UTC",
        tactic: "Brand & Authority Impersonation",
        indicators: ["Salik Brand Assets", "Fake Recharge Form"],
      },
    },
    {
      id: "node-lure",
      type: "lure",
      label: "Lure: SMS Urgency + OTP",
      sublabel: "طعم رسائل SMS الاحتيالية",
      iconSrc: "/assets/stix/stix-malware.svg",
      x: 280,
      y: 220,
      color: "#EF4444",
      details: {
        stixId: "attack-pattern--smishing-urgency",
        confidence: 0.96,
        firstSeen: "2026-10-09 14:25 UTC",
        tactic: "Urgent toll expiration coercion",
        indicators: ["+447812938472", "Arabizi Text Payload"],
      },
    },
    {
      id: "node-indicator",
      type: "indicator",
      label: "IoC: sаlik.ae (IDN Spoof)",
      sublabel: "نطاق مزور بحرف سيريلي",
      iconSrc: "/assets/stix/stix-indicator.svg",
      x: 500,
      y: 100,
      color: "#06B6D4",
      details: {
        stixId: "indicator--idn-homograph-salik",
        confidence: 0.99,
        firstSeen: "2026-10-09 14:30 UTC",
        tactic: "IDN Homograph Substitution (U+0430)",
        indicators: ["xn--slik-43a.ae", "185.193.125.44"],
      },
    },
    {
      id: "node-sink",
      type: "sink",
      label: "Exfil: Foreign Payment Trap",
      sublabel: "بوابة دفع أجنبية مسروقة",
      iconSrc: "/assets/stix/stix-infrastructure.svg",
      x: 500,
      y: 240,
      color: "#DC2626",
      details: {
        stixId: "infrastructure--c2-payment-drain",
        confidence: 0.97,
        firstSeen: "2026-10-09 14:38 UTC",
        tactic: "Credit Card & OTP Harvesting",
        indicators: ["Fake 3DS Form", "POST /api/collect-otp"],
      },
    },
  ];

  const links: GraphLink[] = [
    { source: "node-campaign", target: "node-target", label: "Impersonates" },
    { source: "node-campaign", target: "node-lure", label: "Dispatches" },
    { source: "node-target", target: "node-indicator", label: "Spoofed As" },
    { source: "node-lure", target: "node-sink", label: "Drains To" },
    { source: "node-indicator", target: "node-sink", label: "Resolves" },
  ];

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur p-4 sm:p-6 shadow-sm transition-colors">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Radio className="w-4 h-4 text-purple-600 dark:text-purple-400 animate-pulse-subtle" />
            <span>Interactive STIX 2.1 Attack Flow Graph</span>
            <span className="text-xs text-slate-500 font-normal">/ مخطط مسار الهجوم السيبراني</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Real-time visual node correlation mapping threat kill-chains, targets, lure channels, and exfiltration sinks.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-500 dark:text-slate-400">
          <span className="inline-block w-2 h-2 rounded-full bg-purple-500"></span>
          <span>STIX 2.1 Compliant</span>
        </div>
      </div>

      {/* SVG Canvas Workspace */}
      <div className="relative w-full overflow-x-auto bg-slate-50 dark:bg-slate-950/60 rounded-lg border border-slate-200/60 dark:border-slate-800/60 p-2">
        <svg viewBox="0 0 620 320" className="w-full min-w-[580px] h-72 block">
          <defs>
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="6"
              refX="7"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 8 3, 0 6" fill="#94A3B8" />
            </marker>
          </defs>

          {/* Links / Attack Edges */}
          {links.map((link, idx) => {
            const src = nodes.find((n) => n.id === link.source);
            const tgt = nodes.find((n) => n.id === link.target);
            if (!src || !tgt) return null;

            return (
              <g key={idx}>
                <line
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke="#94A3B8"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                  markerEnd="url(#arrowhead)"
                  className="opacity-60 dark:opacity-40"
                />
                <text
                  x={(src.x + tgt.x) / 2}
                  y={(src.y + tgt.y) / 2 - 6}
                  fill="#64748B"
                  fontSize="9"
                  fontFamily="monospace"
                  textAnchor="middle"
                  className="select-none"
                >
                  {link.label}
                </text>
              </g>
            );
          })}

          {/* Graph Nodes */}
          {nodes.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => setSelectedNode(node)}
                className="cursor-pointer transition-transform hover:scale-105"
              >
                <circle
                  r="24"
                  fill={node.color}
                  fillOpacity="0.15"
                  stroke={node.color}
                  strokeWidth={isSelected ? "3" : "1.5"}
                  className="transition-all"
                />
                {/* STIX Icon */}
                <image
                  href={node.iconSrc}
                  x="-12"
                  y="-12"
                  width="24"
                  height="24"
                />
                {/* Node Label */}
                <text
                  x="0"
                  y="34"
                  fill="currentColor"
                  fontSize="10"
                  fontWeight="600"
                  textAnchor="middle"
                  className="select-none text-slate-800 dark:text-slate-200"
                >
                  {node.label}
                </text>
                <text
                  x="0"
                  y="46"
                  fill="#94A3B8"
                  fontSize="8"
                  textAnchor="middle"
                  className="select-none"
                >
                  {node.sublabel}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode ? (
        <div className="mt-4 p-3 rounded-lg border border-purple-200 dark:border-purple-900/60 bg-purple-50/50 dark:bg-purple-950/20 text-xs transition-all">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-purple-900 dark:text-purple-300">
                {selectedNode.label}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300">
                {selectedNode.details.stixId}
              </span>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 font-mono text-[10px]"
            >
              Close [✕]
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 font-mono text-[11px] text-slate-700 dark:text-slate-300">
            <div>
              <span className="text-slate-400">Tactic:</span> {selectedNode.details.tactic}
            </div>
            <div>
              <span className="text-slate-400">Confidence:</span> {(selectedNode.details.confidence * 100).toFixed(0)}%
            </div>
            <div>
              <span className="text-slate-400">First Seen:</span> {selectedNode.details.firstSeen}
            </div>
          </div>

          <div className="mt-2 text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-1.5 flex-wrap">
            <span className="text-slate-400 font-mono">Linked IoCs:</span>
            {selectedNode.details.indicators.map((ioc, i) => (
              <span key={i} className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px]">
                {ioc}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <p className="mt-3 text-center text-xs text-slate-400 dark:text-slate-500 italic">
          Click any node above to inspect forensic STIX 2.1 attributes and IoC relationship data.
        </p>
      )}
    </div>
  );
}
