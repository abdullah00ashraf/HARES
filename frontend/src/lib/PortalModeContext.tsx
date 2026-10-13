"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export type PortalMode = "citizen" | "soc";

interface PortalModeContextType {
  portalMode: PortalMode;
  setPortalMode: (mode: PortalMode) => void;
}

const PortalModeContext = createContext<PortalModeContextType>({
  portalMode: "citizen",
  setPortalMode: () => {},
});

export function PortalModeProvider({ children }: { children: ReactNode }) {
  const [portalMode, setPortalMode] = useState<PortalMode>("citizen");

  return (
    <PortalModeContext.Provider value={{ portalMode, setPortalMode }}>
      {children}
    </PortalModeContext.Provider>
  );
}

export function usePortalMode() {
  return useContext(PortalModeContext);
}
