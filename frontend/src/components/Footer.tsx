"use client";

import React, { useState } from "react";
import { Shield, Lock, Scale, ExternalLink } from "lucide-react";
import LegalModal from "./LegalModal";
import { soundFx } from "../lib/audioSoundFx";

export default function Footer() {
  const [legalModalOpen, setLegalModalOpen] = useState<boolean>(false);
  const [legalInitialTab, setLegalInitialTab] = useState<"terms" | "privacy">("privacy");

  const openLegalModal = (tab: "terms" | "privacy") => {
    soundFx.playClick();
    setLegalInitialTab(tab);
    setLegalModalOpen(true);
  };

  return (
    <>
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-950/90 backdrop-blur-md px-6 py-6 text-xs text-slate-500 dark:text-slate-400 font-sans transition-colors">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Left: Branding & Mission */}
          <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-3 text-center sm:text-left">
            <span className="font-mono font-bold tracking-wider text-slate-800 dark:text-slate-200">
              PROJECT HARES (مشروع حارس)
            </span>
            <span className="hidden sm:inline text-slate-300 dark:text-slate-700">•</span>
            <span className="text-[11px] text-slate-500">
              Sovereign Municipal Fraud Triage for Dubai &amp; UAE
            </span>
          </div>

          {/* Center: Zero Citizen PII Retention Shield */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-emerald-800 dark:text-emerald-300 text-[11px] font-mono font-semibold">
            <Lock className="w-3 h-3 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>ZERO CITIZEN PII RETENTION (FR-4.1)</span>
          </div>

          {/* Right: Legal & Police Escalation Links */}
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-semibold">
            <button
              type="button"
              onClick={() => openLegalModal("privacy")}
              className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition underline underline-offset-4 decoration-slate-300 dark:decoration-slate-700 hover:decoration-emerald-500"
            >
              Privacy Policy (الخصوصية)
            </button>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <button
              type="button"
              onClick={() => openLegalModal("terms")}
              className="text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition underline underline-offset-4 decoration-slate-300 dark:decoration-slate-700 hover:decoration-emerald-500"
            >
              Terms of Service (الشروط)
            </button>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <a
              href="https://www.ecrime.ae"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-slate-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition"
            >
              <span>Dubai Police e-Crime</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* Bottom Micro-Caption */}
        <div className="max-w-7xl mx-auto mt-4 pt-3 border-t border-slate-100 dark:border-slate-900 text-center text-[10px] text-slate-400 dark:text-slate-600 font-mono">
          Operates strictly under UAE Federal Decree-Law No. 45 of 2021 (PDPL) • DESC Compliant • Local Sovereign &amp; ZeroGPU Inference Only
        </div>
      </footer>

      {/* Interactive Compliance Legal Modal */}
      <LegalModal
        isOpen={legalModalOpen}
        onClose={() => setLegalModalOpen(false)}
        initialTab={legalInitialTab}
      />
    </>
  );
}
