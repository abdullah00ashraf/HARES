import type { Metadata } from "next";
import "./globals.css";
import Header from "../components/Header";
import Footer from "../components/Footer";
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
            <Footer />
          </PortalModeProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
