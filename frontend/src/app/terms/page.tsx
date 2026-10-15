import React from "react";
import Link from "next/link";
import { Scale, AlertTriangle, ArrowLeft, ExternalLink, ShieldCheck } from "lucide-react";

export const metadata = {
  title: "Terms of Service & Public Use | Project Hares",
  description: "Terms and conditions of public cybersecurity triage services for UAE citizens and residents.",
};

export default function TermsPage() {
  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 space-y-8 font-sans">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-emerald-600 transition"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Citizen Triage Portal / العودة للبوابة الرئيسية</span>
      </Link>

      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 sm:p-10 shadow-sm space-y-6">
        <div className="flex items-center gap-3 border-b border-slate-200 dark:border-slate-800 pb-5">
          <div className="p-3 rounded-2xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Terms of Service &amp; Public Usage Guidelines
            </h1>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              Public Safety Guidelines • Non-Emergency Threat Triage Notice
            </p>
          </div>
        </div>

        {/* Highlight Notice */}
        <div className="p-5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-xs sm:text-sm text-amber-900 dark:text-amber-200 space-y-2">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider font-mono">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <span>Non-Emergency Advisory Tool</span>
          </div>
          <p>
            Project Hares provides automated, probabilistic cybersecurity evaluations. It does <strong>not</strong> substitute for formal
            law enforcement reporting. If you are experiencing an active crime or financial extortion, immediately dial{" "}
            <strong>901</strong> or submit an official complaint to Dubai Police e-Crime at{" "}
            <a
              href="https://www.ecrime.ae"
              target="_blank"
              rel="noopener noreferrer"
              className="underline font-bold hover:text-amber-950 dark:hover:text-white"
            >
              https://www.ecrime.ae
            </a>.
          </p>
        </div>

        {/* Detailed Sections */}
        <div className="space-y-6 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              1. Platform Purpose &amp; Scope of Free Access
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Project Hares is an independent municipal threat triage platform engineered to assist UAE citizens, residents,
              and businesses in verifying the authenticity of suspicious SMS lures, WhatsApp communications, payment links,
              audio notes, and screenshot receipts. Access is provided free of charge for the purpose of enhancing public cyber hygiene.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              2. Algorithmic Tri-State Verdicts
            </h2>
            <div className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 space-y-1">
              <p>Triage verdicts are synthesized via deterministic allowlists and sovereign neural engines:</p>
              <ul className="list-disc list-inside space-y-1 pl-2">
                <li><strong className="text-emerald-600 dark:text-emerald-400">🟢 GREEN (Verified Safe):</strong> Validated against official authenticated UAE government and commercial registries.</li>
                <li><strong className="text-amber-600 dark:text-amber-400">🟡 AMBER (Unverified / Caution):</strong> Destination or message authenticity cannot be proven; exercise vigilance.</li>
                <li><strong className="text-red-600 dark:text-red-400">🔴 RED (High Risk / Fraud):</strong> Verified social engineering, authority impersonation, IDN lookalike spoof, or synthetic deepfake detected.</li>
              </ul>
            </div>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              3. Acceptable Use Policy &amp; Security Controls
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Users agree not to abuse, disrupt, or exploit the platform. Prohibited activities include attempting denial-of-service
              (DoS) attacks, automated bulk scraping without municipal credentials, or submitting adversarial prompt injection payloads
              designed to breach NVIDIA NeMo Guardrails. Rate limits are dynamically enforced per IP and per hashed citizen session via
              Redis token-bucket algorithms.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              4. Disclaimer of Liability
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Project Hares is an independent open-source public cybersecurity project developed for community fraud triage and is not an official government website, agency, or law enforcement division. While Project Hares employs Conformal Prediction statistical calibration to bound error rates (≤ 0.1%), automated models are advisory. Users must remain vigilant and apply sound judgment. The developers, open-source contributors, and operators of Project Hares disclaim any liability for direct, indirect, or consequential damages resulting from reliance on triage verdicts, third-party fraud, or actions taken prior to submitting content.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              5. Official Escalation Pathways
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              All identified RED indicators are automatically correlated with threat campaigns and synchronized with Dubai Police General
              Headquarters and e-Crime escalation channels.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
