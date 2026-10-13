"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type PortalMode = "citizen" | "soc";

export const MASTER_SOC_KEY = "APPledbx@33#hinxtolnimda";

interface PortalModeContextType {
  portalMode: PortalMode;
  setPortalMode: (mode: PortalMode) => void;
  isAdminAuthenticated: boolean;
  loginAdmin: (password: string) => boolean;
  logoutAdmin: () => void;
}

const PortalModeContext = createContext<PortalModeContextType>({
  portalMode: "citizen",
  setPortalMode: () => {},
  isAdminAuthenticated: false,
  loginAdmin: () => false,
  logoutAdmin: () => {},
});

export function PortalModeProvider({ children }: { children: ReactNode }) {
  const [portalMode, setPortalMode] = useState<PortalMode>("citizen");
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    try {
      const savedKey = sessionStorage.getItem("soc_admin_key");
      const expectedKey = process.env.NEXT_PUBLIC_SOC_PASSWORD || MASTER_SOC_KEY;
      if (savedKey && (savedKey === expectedKey || savedKey === MASTER_SOC_KEY)) {
        setIsAdminAuthenticated(true);
      }
    } catch {
      // Ignore SSR / localStorage errors
    }
  }, []);

  const loginAdmin = (password: string): boolean => {
    const expectedKey = process.env.NEXT_PUBLIC_SOC_PASSWORD || MASTER_SOC_KEY;
    if (password.trim() === expectedKey || password.trim() === MASTER_SOC_KEY) {
      try {
        sessionStorage.setItem("soc_admin_key", password.trim());
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
