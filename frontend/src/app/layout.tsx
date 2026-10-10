import type { Metadata } from "next";
import "./globals.css";
import Header from "../components/Header";

export const metadata: Metadata = {
  title: "Project Hares | Dubai Municipal Threat Intelligence Portal",
  description:
    "Automated WhatsApp Fraud Triage & Sovereign Threat Intelligence Platform for Dubai and UAE Municipal Authorities.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased">
        <Header />
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
          {children}
        </main>
        <footer className="border-t border-slate-900 bg-slate-950/80 px-6 py-4 text-center text-xs text-slate-500 font-mono">
          <span>PROJECT HARES (مشروع حارس) • UAE SOVEREIGN THREAT INTELLIGENCE • ZERO CITIZEN PII RETENTION (FR-4.1)</span>
        </footer>
      </body>
    </html>
  );
}
