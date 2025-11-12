"use client";

import { createContext, type ReactNode, useContext, useMemo } from "react";
import { useUser } from "@/contexts/UserContext";
import type { Setting } from "@/services/settingsApi";

// Re-export Setting type for backward compatibility
export type { Setting };

export interface SettingsContextType {
  settings: Record<string, Setting>;
  isLoading: boolean;
  isSaving: boolean;
  updateSetting: (key: string, value: string) => void;
  getSetting: (key: string) => string | null;
}

const SettingsContext = createContext<SettingsContextType | undefined>(
  undefined,
);

export interface SettingsProviderProps {
  children: ReactNode;
  debounceMs?: number;
}

/**
 * Settings context provider.
 *
 * Thin facade over UserContext SSOT for settings.
 * Avoids duplicate fetching and keeps settings state centralized.
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     Child components that can access the settings context.
 * debounceMs : number
 *     Ignored; debouncing is handled in UserContext.
 */
export function SettingsProvider({ children }: SettingsProviderProps) {
  const { settings, isLoading, isSaving, getSetting, updateSetting } =
    useUser();

  const value = useMemo(
    () => ({
      settings,
      isLoading,
      isSaving,
      updateSetting,
      getSetting,
    }),
    [settings, isLoading, isSaving, updateSetting, getSetting],
  );

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

/**
 * Hook to access settings context.
 *
 * Returns
 * -------
 * SettingsContextType
 *     Settings context containing settings data, loading state, and update function.
 *
 * Raises
 * ------
 * Error
 *     If used outside of SettingsProvider.
 */
export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
