"use client";

import React from "react";
import { LayoutDashboard, Flame, Database, ShieldAlert, Mic, Cpu } from "lucide-react";
import { soundFx } from "../lib/audioSoundFx";

export type WorkbenchTab = "overview" | "campaigns" | "iocs" | "homographs" | "audio" | "telemetry";

interface NavigationProps {
  activeTab: WorkbenchTab;
  onSelectTab: (tab: WorkbenchTab) => void;
}

export default function Navigation({ activeTab, onSelectTab }: NavigationProps) {
  const tabs = [
    {
      id: "overview" as WorkbenchTab,
      label: "1. Overview & Heatmap",
      sublabel: "نظرة عامة وخريطة التهديدات",
      icon: LayoutDashboard,
      badge: "LIVE",
      badgeColor: "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-400 dark:border-emerald-800",
    },
    {
      id: "campaigns" as WorkbenchTab,
      label: "2. Active Campaigns",
      sublabel: "رصد الحملات النشطة",
      icon: Flame,
      badge: "4 Active",
      badgeColor: "bg-red-100 text-red-800 border-red-300 dark:bg-red-950/60 dark:text-red-400 dark:border-red-800",
    },
    {
      id: "iocs" as WorkbenchTab,
      label: "3. IoC Repository",
      sublabel: "قاعدة مؤشرات الاختراق STIX",
      icon: Database,
      badge: "STIX 2.1",
      badgeColor: "bg-cyan-100 text-cyan-800 border-cyan-300 dark:bg-cyan-950/60 dark:text-cyan-400 dark:border-cyan-800",
    },
    {
      id: "homographs" as WorkbenchTab,
      label: "4. Domain Spoof Radar",
      sublabel: "رادار النطاقات المزورة",
      icon: ShieldAlert,
      badge: "Punycode",
      badgeColor: "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/60 dark:text-amber-400 dark:border-amber-800",
    },
    {
      id: "audio" as WorkbenchTab,
      label: "5. Synthetic Audio Lab",
      sublabel: "مختبر كشف التزييف الصوتي",
      icon: Mic,
      badge: "60 FPS Canvas",
      badgeColor: "bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-950/60 dark:text-purple-400 dark:border-purple-800",
    },
    {
      id: "telemetry" as WorkbenchTab,
      label: "6. Model & Engine Telemetry",
      sublabel: "مؤشرات النماذج وقاعدة البيانات",
      icon: Cpu,
      badge: "Postgres Sync",
      badgeColor: "bg-indigo-100 text-indigo-800 border-indigo-300 dark:bg-indigo-950/60 dark:text-indigo-400 dark:border-indigo-800",
    },
  ];

  const handleTabClick = (id: WorkbenchTab) => {
    soundFx.playClick();
    onSelectTab(id);
  };

  return (
    <nav className="border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-950/60 px-4 sm:px-6 py-2 transition-colors">
      <div className="flex items-center space-x-2 overflow-x-auto no-scrollbar py-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`flex items-center gap-2.5 px-3.5 py-2 rounded-lg text-xs font-medium transition-all duration-150 whitespace-nowrap ${
                isActive
                  ? "bg-slate-900 text-white dark:bg-slate-800 dark:text-white shadow-sm border border-slate-700 font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-900/60"
              }`}
            >
              <Icon
                className={`w-4 h-4 ${
                  isActive ? "text-amber-400" : "text-slate-400"
                }`}
              />
              <div className="flex flex-col text-left leading-tight">
                <span>{tab.label}</span>
                <span className="text-[9px] font-normal opacity-75">{tab.sublabel}</span>
              </div>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded border font-mono ${tab.badgeColor}`}
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
