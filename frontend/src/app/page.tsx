"use client";

import React, { useState } from "react";
import { usePortalMode } from "../lib/PortalModeContext";
import CitizenTriagePortal from "../components/CitizenTriagePortal";
import Navigation, { WorkbenchTab } from "../components/Navigation";
import OverviewWorkbench from "../components/OverviewWorkbench";
import CampaignWorkbench from "../components/CampaignWorkbench";
import IocWorkbench from "../components/IocWorkbench";
import HomographWorkbench from "../components/HomographWorkbench";
import AudioTriageWorkbench from "../components/AudioTriageWorkbench";

export default function DashboardPage() {
  const { portalMode } = usePortalMode();
  const [activeTab, setActiveTab] = useState<WorkbenchTab>("overview");

  return (
    <div className="space-y-6">
      {portalMode === "citizen" ? (
        /* Citizen Fraud Verification Portal (Public User View) */
        <CitizenTriagePortal />
      ) : (
        /* Municipal Threat Intelligence SOC Dashboard (Admin Section) */
        <div className="space-y-6 animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
                Municipal Threat Operations &amp; Forensics
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Sovereign Cyber Threat Intelligence Center • Real-Time Class A Indicator Telemetry &amp; Campaign Clustering
              </p>
            </div>
            <span className="self-start sm:self-auto text-xs px-2.5 py-1 rounded-full bg-cyan-100 dark:bg-cyan-950/60 border border-cyan-200 dark:border-cyan-800/40 text-cyan-800 dark:text-cyan-300 font-mono">
              STIX 2.1 Feeds Active
            </span>
          </div>

          {/* Navigation Bar for the 5 SOC Workbenches */}
          <Navigation activeTab={activeTab} onSelectTab={setActiveTab} />

          {/* Dynamic Operational Workbench Viewport */}
          <div className="mt-4 transition-all duration-200">
            {activeTab === "overview" && <OverviewWorkbench />}
            {activeTab === "campaigns" && <CampaignWorkbench />}
            {activeTab === "iocs" && <IocWorkbench />}
            {activeTab === "homographs" && <HomographWorkbench />}
            {activeTab === "audio" && <AudioTriageWorkbench />}
          </div>
        </div>
      )}
    </div>
  );
}
