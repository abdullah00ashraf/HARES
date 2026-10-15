"use client";

import React, { useState, useEffect } from "react";
import { Shield, Lock, FileText, CheckCircle2, AlertTriangle, X, Scale, ExternalLink } from "lucide-react";
import { soundFx } from "../lib/audioSoundFx";

interface LegalModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: "terms" | "privacy";
}

export default function LegalModal({
  isOpen,
  onClose,
  initialTab = "privacy",
}: LegalModalProps) {
  const [activeTab, setActiveTab] = useState<"terms" | "privacy">(initialTab);

  useEffect(() => {
    if (initialTab) setActiveTab(initialTab);
  }, [initialTab]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-3xl max-h-[85vh] flex flex-col rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden transition-colors"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
                Project Hares Legal &amp; Compliance Center
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Independent Sovereign Cyber Fraud Triage • UAE Municipal Cybersecurity
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              soundFx.playClick();
              onClose();
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-100/60 dark:bg-slate-950/40 px-5 pt-2 gap-2">
          <button
            type="button"
            onClick={() => {
              soundFx.playClick();
              setActiveTab("privacy");
            }}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition ${
              activeTab === "privacy"
                ? "border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400 bg-white dark:bg-slate-900 rounded-t-lg"
                : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Citizen Privacy Policy (سياسة الخصوصية)</span>
          </button>
          <button
            type="button"
            onClick={() => {
              soundFx.playClick();
              setActiveTab("terms");
            }}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition ${
              activeTab === "terms"
                ? "border-emerald-600 text-emerald-600 dark:border-emerald-400 dark:text-emerald-400 bg-white dark:bg-slate-900 rounded-t-lg"
                : "border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>Terms of Service (شروط وأحكام الاستخدام)</span>
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
          {activeTab === "privacy" && (
            <div className="space-y-6">
              {/* Sovereign Banner */}
              <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 space-y-2">
                <div className="flex items-center gap-2 text-emerald-900 dark:text-emerald-200 font-bold text-xs uppercase tracking-wider font-mono">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  <span>The Zero Citizen PII Retention Guarantee (FR-4.1)</span>
                </div>
                <p className="text-xs text-emerald-800 dark:text-emerald-300">
                  Project Hares is built with privacy-by-design. We <strong>never</strong> store citizen phone numbers,
                  submitter contact identities, or private identifiers in our database or server memory.
                </p>
              </div>

              {/* Section 1 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    1
                  </span>
                  <span>Cryptographic Pseudonymization (Class B Citizen Data)</span>
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">
                  Upon receiving a forwarded message or inquiry (via WhatsApp or web interface), your contact identifier
                  is immediately passed through a keyed <strong>HMAC-SHA256</strong> cryptographic hash function with a
                  high-entropy secret salt (<code>CITIZEN_HASH_SALT</code>). The raw identifier is immediately dropped from RAM.
                  Only the irreversible hash is utilized for token-bucket rate limiting and sanitized audit telemetry.
                </p>
              </section>

              {/* Section 2 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    2
                  </span>
                  <span>Class A Threat Indicators vs. Class B Citizen Data</span>
                </h4>
                <div className="text-xs text-slate-600 dark:text-slate-400 pl-8 space-y-2">
                  <p>We maintain an absolute architectural division between citizen identity and attacker threat telemetry:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>
                      <strong>Class B Data (Citizen Identity):</strong> Strictly scrubbed, pseudonymized, and never retained.
                    </li>
                    <li>
                      <strong>Class A Data (Scammer Threat IoCs):</strong> Malicious URLs, fake lookalike domains, scammer phone numbers,
                      fraudulent bank account IBANs, and crypto extortion addresses are stored in our threat repository to protect
                      the UAE community and enable municipal cybersecurity countermeasures.
                    </li>
                  </ul>
                </div>
              </section>

              {/* Section 3 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    3
                  </span>
                  <span>Ephemeral Voice Notes &amp; Screenshot OCR Processing</span>
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">
                  Uploaded audio recordings are processed in-memory solely for acoustic synthetic deepfake anomaly detection
                  (via AASIST with conformal statistical calibration) and transcribed locally via Whisper ASR. Screenshot images are
                  processed in-memory via Optical Character Recognition (OCR). Raw audio and image media files are strictly ephemeral
                  and are permanently destroyed immediately upon triage verdict delivery.
                </p>
              </section>

              {/* Section 4 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    4
                  </span>
                  <span>Sovereign Local &amp; ZeroGPU Inference (Zero Third-Party SaaS Leaks)</span>
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">
                  No citizen text or submitted content is ever routed to third-party offshore proprietary APIs (such as OpenAI or Anthropic).
                  All neural classification executes exclusively on our sovereign local nodes or dedicated Hugging Face ZeroGPU A10G
                  sandboxes operating under strict data sovereignty controls.
                </p>
              </section>

              {/* Section 5 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    5
                  </span>
                  <span>UAE Data Protection Law Alignment</span>
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">
                  Project Hares engineering principles comply with <strong>UAE Federal Decree-Law No. 45 of 2021 on Personal Data Protection (PDPL)</strong> and
                  Dubai Electronic Security Center (DESC) standards for public municipal threat intelligence systems.
                </p>
              </section>
            </div>
          )}

          {activeTab === "terms" && (
            <div className="space-y-6">
              {/* Advisory Alert Banner */}
              <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 space-y-2">
                <div className="flex items-center gap-2 text-amber-900 dark:text-amber-200 font-bold text-xs uppercase tracking-wider font-mono">
                  <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                  <span>Important Non-Emergency Advisory Notice</span>
                </div>
                <p className="text-xs text-amber-800 dark:text-amber-300">
                  Project Hares is an automated cyber fraud triage intelligence tool. It does <strong>not</strong> substitute for formal law enforcement
                  emergency reporting. For active financial theft or emergency intervention, contact Dubai Police directly at <strong>901</strong> or
                  report to Dubai Police e-Crime at{" "}
                  <a
                    href="https://www.ecrime.ae"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline font-semibold hover:text-amber-950 dark:hover:text-white"
                  >
                    https://www.ecrime.ae
                  </a>.
                </p>
              </div>

              {/* Section 1 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    1
                  </span>
                  <span>Service Purpose &amp; Scope of Use</span>
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">
                  Project Hares provides automated, sovereign triage to assist citizens, residents, and organizations within Dubai and the UAE
                  in evaluating incoming SMS, WhatsApp communications, web destinations, voice notes, and screenshots for social engineering,
                  credential harvesting, and authority impersonation lures. The service is provided free of charge for public protection.
                </p>
              </section>

              {/* Section 2 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    2
                  </span>
                  <span>Algorithmic Triage &amp; Tri-State Verdicts</span>
                </h4>
                <div className="text-xs text-slate-600 dark:text-slate-400 pl-8 space-y-1">
                  <p>Our pipeline generates automated tri-state classifications based on verified indicators:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li><strong className="text-emerald-600 dark:text-emerald-400">🟢 GREEN (Verified Safe):</strong> Confirmed match against authenticated UAE government allowlists or validated benign correspondence.</li>
                    <li><strong className="text-amber-600 dark:text-amber-400">🟡 AMBER (Unverified / Caution):</strong> Destination or content authenticity cannot be conclusively verified; exercise caution.</li>
                    <li><strong className="text-red-600 dark:text-red-400">🔴 RED (High Risk / Fraud):</strong> Verified social engineering, authority impersonation, IDN lookalike spoof, or acoustic deepfake detected.</li>
                  </ul>
                </div>
              </section>

              {/* Section 3 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    3
                  </span>
                  <span>Acceptable Use Policy &amp; Anti-Abuse Controls</span>
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">
                  Users agree to use the service in good faith. You are strictly prohibited from attempting denial-of-service (DoS) attacks,
                  submitting automated scraping queries without permission, injecting adversarial jailbreaks or prompt injections designed to
                  override system guardrails, or utilizing the platform to validate phishing payloads for offensive campaigns.
                  Rate limits are strictly enforced per IP and per hashed user session via Redis token-bucket policies.
                </p>
              </section>

              {/* Section 4 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    4
                  </span>
                  <span>Limitation of Liability &amp; Disclaimers</span>
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">
                  Project Hares is an independent open-source public cybersecurity project developed for community fraud triage and is not an official government website, agency, or law enforcement division. While Project Hares applies strict conformal statistical calibration to bound error rates (≤ 0.1%), automated models are advisory. Users must remain vigilant and apply sound judgment. The developers, open-source contributors, and operators of Project Hares disclaim any liability for direct, indirect, or consequential damages resulting from reliance on triage verdicts, third-party fraud, or actions taken prior to submitting content.
                </p>
              </section>

              {/* Section 5 */}
              <section className="space-y-2">
                <h4 className="font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 text-xs flex items-center justify-center font-mono">
                    5
                  </span>
                  <span>Official Escalation Rights</span>
                </h4>
                <p className="text-xs text-slate-600 dark:text-slate-400 pl-8">
                  All detected RED threat indicators are synchronized with public sector threat intelligence feeds and escalation pathways
                  directed to the Dubai Police General Headquarters, General Department of Criminal Investigation, and e-Crime Division.
                </p>
              </section>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/70 text-xs text-slate-500 gap-3">
          <div className="flex items-center gap-2">
            <Lock className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>FR-4.1 Cryptographic Privacy Standard Certified</span>
          </div>
          <button
            type="button"
            onClick={() => {
              soundFx.playClick();
              onClose();
            }}
            className="w-full sm:w-auto px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 font-bold transition text-xs shadow"
          >
            Acknowledge &amp; Close / تم الاطلاع والإغلاق
          </button>
        </div>
      </div>
    </div>
  );
}
