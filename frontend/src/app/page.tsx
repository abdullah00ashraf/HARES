"use client";

import React, { useState } from "react";
import Navigation, { WorkbenchTab } from "../components/Navigation";
import OverviewWorkbench from "../components/OverviewWorkbench";
import CampaignWorkbench from "../components/CampaignWorkbench";
import IocWorkbench from "../components/IocWorkbench";
import HomographWorkbench from "../components/HomographWorkbench";
import AudioTriageWorkbench from "../components/AudioTriageWorkbench";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<WorkbenchTab>("overview");

  return (
    <div className="space-y-6">
      {/* Navigation Bar */}
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
  );
}
