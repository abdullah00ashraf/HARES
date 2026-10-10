"use client";

import React from "react";
import { LayoutDashboard, Flame, Database, ShieldAlert, Mic } from "lucide-react";

export type WorkbenchTab = "overview" | "campaigns" | "iocs" | "homographs" | "audio";

interface NavigationProps {
  activeTab: WorkbenchTab;
  onSelectTab: (tab: WorkbenchTab) => void;
}

export default function Navigation({ activeTab, onSelectTab }: NavigationProps) {
  const tabs = [
    {
      id: "overview" as WorkbenchTab,
      label: "1. Overview & Heatmap",
      icon: LayoutDashboard,
      badge: "LIVE",
      badgeColor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    },
    {
      id: "campaigns" as WorkbenchTab,
      label: "2. Active Campaign Tracker",
      icon: Flame,
      badge: "4 Active",
      badgeColor: "bg-red-500/20 text-red-400 border-red-500/30",
    },
    {
      id: "iocs" as WorkbenchTab,
      label: "3. IoC Repository & Export",
      icon: Database,
      badge: "STIX 2.1",
      badgeColor: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
    },
    {
      id: "homographs" as WorkbenchTab,
      label: "4. Domain Spoof Radar",
      icon: ShieldAlert,
      badge: "Punycode",
      badgeColor: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    },
    {
      id: "audio" as WorkbenchTab,
      label: "5. Synthetic Voice Workbench",
      icon: Mic,
      badge: "60 FPS Canvas",
      badgeColor: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    },
  ];

  return (
    <nav className="border-b border-slate-800 bg-slate-950/60 px-6 py-2">
      <div className="flex items-center space-x-2 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 whitespace-nowrap ${
                isActive
                  ? "bg-slate-800 text-white shadow-sm border border-slate-700 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
              }`}
            >
              <Icon
                className={`w-4 h-4 ${
                  isActive ? "text-sovereign-gold" : "text-slate-400"
                }`}
              />
              <span>{tab.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded border font-mono ${tab.badgeColor}`}
              >
                {tab.badge}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
