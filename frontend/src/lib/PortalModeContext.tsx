"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { verifySocPasskey } from "./api";

export type PortalMode = "citizen" | "soc";

interface PortalModeContextType {
  portalMode: PortalMode;
  setPortalMode: (mode: PortalMode) => void;
  isAdminAuthenticated: boolean;
  loginAdmin: (password: string) => Promise<boolean>;
  logoutAdmin: () => void;
}

const PortalModeContext = createContext<PortalModeContextType>({
  portalMode: "citizen",
  setPortalMode: () => {},
  isAdminAuthenticated: false,
  loginAdmin: async () => false,
  logoutAdmin: () => {},
});

export function PortalModeProvider({ children }: { children: ReactNode }) {
  const [portalMode, setPortalMode] = useState<PortalMode>("citizen");
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    try {
      const savedKey = sessionStorage.getItem("soc_admin_key");
      if (savedKey && savedKey.length >= 8) {
        setIsAdminAuthenticated(true);
      }
    } catch {
      // Ignore SSR / localStorage errors
    }
  }, []);

  const loginAdmin = async (password: string): Promise<boolean> => {
    const trimmed = password.trim();
    if (!trimmed) return false;

    // Server-side authentication against /api/v1/threats/auth/verify (AUDIT-OBS-30)
    const isValid = await verifySocPasskey(trimmed);
    if (isValid) {
      try {
        sessionStorage.setItem("soc_admin_key", trimmed);
      } catch {
        // Ignore storage errors
      }
      setIsAdminAuthenticated(true);
      return true;
    }
    return false;
  };

  const logoutAdmin = () => {
    try {
      sessionStorage.removeItem("soc_admin_key");
    } catch {
      // Ignore storage errors
    }
    setIsAdminAuthenticated(false);
    setPortalMode("citizen");
  };

  return (
    <PortalModeContext.Provider
      value={{
        portalMode,
        setPortalMode,
        isAdminAuthenticated,
        loginAdmin,
        logoutAdmin,
      }}
    >
      {children}
    </PortalModeContext.Provider>
  );
}

export function usePortalMode() {
  return useContext(PortalModeContext);
}
