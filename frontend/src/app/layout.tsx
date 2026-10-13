import type { Metadata } from "next";
import "./globals.css";
import Header from "../components/Header";
import { PortalModeProvider } from "../lib/PortalModeContext";
import { ThemeProvider } from "../lib/ThemeContext";

export const metadata: Metadata = {
  title: "Project Hares (مشروع حارس) | Sovereign Threat Intelligence & Citizen Fraud Triage",
  description:
    "Independent sovereign fraud triage and threat intelligence platform for UAE municipal cybersecurity.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light" suppressHydrationWarning>
      <body className="bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-h-screen flex flex-col antialiased transition-colors duration-200">
        <ThemeProvider>
          <PortalModeProvider>
            <Header />
            <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
              {children}
            </main>
            <footer className="border-t border-slate-200 dark:border-slate-900 bg-white/80 dark:bg-slate-950/80 px-6 py-4 text-center text-xs text-slate-500 dark:text-slate-500 font-mono transition-colors">
              <div className="flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-4">
                <span>PROJECT HARES (مشروع حارس) • INDEPENDENT SOVEREIGN FRAUD TRIAGE</span>
                <span className="hidden sm:inline">•</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-semibold">ZERO CITIZEN PII RETENTION (FR-4.1)</span>
              </div>
            </footer>
          </PortalModeProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
