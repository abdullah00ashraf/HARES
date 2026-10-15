import React from "react";
import Link from "next/link";
import { Shield, Lock, CheckCircle2, ArrowLeft, ExternalLink } from "lucide-react";

export const metadata = {
  title: "Citizen Privacy Policy (FR-4.1) | Project Hares",
  description: "Sovereign data protection guarantee and zero citizen PII retention compliance for UAE municipal cybersecurity.",
};

export default function PrivacyPage() {
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
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              Citizen Privacy Policy &amp; Sovereign Data Guarantee
            </h1>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              FR-4.1 Compliance • UAE Federal Decree-Law No. 45 of 2021 (PDPL)
            </p>
          </div>
        </div>

        {/* Highlight Guarantee */}
        <div className="p-5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-xs sm:text-sm text-emerald-900 dark:text-emerald-200 space-y-2">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>Zero Citizen PII Retention Guarantee</span>
          </div>
          <p>
            Project Hares does not collect, record, track, monetize, or store citizen phone numbers, submitter contact details,
            names, or residential identities. Every query submitted by a citizen is evaluated with cryptographic anonymity.
          </p>
        </div>

        {/* Detailed Sections */}
        <div className="space-y-6 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              1. Keyed HMAC-SHA256 Cryptographic Pseudonymization (Class B Data)
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              When a citizen forwards a suspicious communication via WhatsApp or the citizen web portal, the submitter identifier
              is immediately combined with an isolated secret cryptographic salt (<code>CITIZEN_HASH_SALT</code>) and hashed via
              keyed <strong>HMAC-SHA256</strong>. The plain-text identifier is completely purged from RAM within milliseconds.
              The resulting pseudonym is used exclusively by Redis token-bucket rate limiters to protect against brute-force flooding.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              2. Class A Threat Indicators vs. Class B Citizen Data
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              To defend the UAE public against cybercrime while preserving citizen privacy, our architecture strictly distinguishes:
            </p>
            <ul className="list-disc list-inside text-xs sm:text-sm text-slate-600 dark:text-slate-400 space-y-1 pl-2">
              <li>
                <strong>Class B Data (Citizen Identity):</strong> Ephemeral, zero persistence, never recorded to persistent disk.
              </li>
              <li>
                <strong>Class A Data (Scammer Indicators):</strong> Verified phishing URLs, malicious Cyrillic/Arabic punycode domains,
                fraudulent recipient IBANs, and scammer contact numbers are cataloged in our Neon PostgreSQL database and shared via
                STIX 2.1 intelligence with DESC and Dubai Police.
              </li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              3. Ephemeral Voice Notes and OCR Screenshot Processing
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Voice notes are evaluated in-memory for acoustic deepfake conversions (AASIST model calibrated via Conformal Prediction)
              and transcribed locally via Whisper ASR. Screenshot images are parsed in-memory via Optical Character Recognition (OCR).
              The binary audio and image payloads are strictly ephemeral and are permanently scrubbed from memory immediately upon verdict delivery.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              4. Sovereign Local &amp; ZeroGPU Inference (Zero Offshore SaaS Routing)
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              In accordance with UAE data sovereignty mandates, no citizen data or message text is ever routed to third-party offshore
              proprietary APIs (such as OpenAI or Anthropic). All neural classification runs exclusively on our sovereign local nodes
              or dedicated Hugging Face ZeroGPU sandboxes (NVIDIA A10G) operating under isolated execution guarantees.
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              5. Regulatory Compliance &amp; Public Safety Binding
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
              Project Hares complies with UAE Federal Decree-Law No. 45 of 2021 on Personal Data Protection (PDPL) and connects directly
              with official municipal escalation channels through Dubai Police e-Crime (<code>https://www.ecrime.ae</code>) and the
              non-emergency citizen hotline (<strong>901</strong>).
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
