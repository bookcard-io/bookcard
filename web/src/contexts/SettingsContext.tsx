"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  fetchSettings,
  type Setting,
  saveSetting,
} from "@/services/settingsApi";

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
  /**
   * API functions for fetching and saving settings.
   * Allows dependency injection for testing.
   */
  api?: {
    fetchSettings: () => Promise<{ settings: Record<string, Setting> }>;
    saveSetting: (key: string, value: string) => Promise<Setting>;
  };
}

/**
 * Settings context provider.
 *
 * Manages user settings with debounced batching of updates.
 * Follows SRP by handling only settings state management.
 * Follows IOC by accepting configurable debounce delay and API functions.
 * Follows SOC by delegating API calls to injected service.
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     Child components that can access the settings context.
 * debounceMs : number
 *     Debounce delay in milliseconds (default: 300).
 * api : { fetchSettings, saveSetting } | undefined
 *     Optional API functions for dependency injection (default: uses settingsApi).
 */
export function SettingsProvider({
  children,
  debounceMs = 300,
  api,
}: SettingsProviderProps) {
  const apiFetchSettings = api?.fetchSettings ?? fetchSettings;
  const apiSaveSetting = api?.saveSetting ?? saveSetting;
  const [settings, setSettings] = useState<Record<string, Setting>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Queue of pending updates: key -> value
  const pendingUpdatesRef = useRef<Map<string, string>>(new Map());
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Load all settings from the backend.
   */
  const loadSettings = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await apiFetchSettings();
      setSettings(data.settings || {});
    } catch (error) {
      console.error("Failed to load settings:", error);
      // Don't throw - allow app to continue with empty settings
    } finally {
      setIsLoading(false);
    }
  }, [apiFetchSettings]);

  /**
   * Save pending updates to the backend.
   * Deduplicates by keeping only the latest value for each key.
   */
  const savePendingUpdates = useCallback(async () => {
    const updates = pendingUpdatesRef.current;
    if (updates.size === 0) {
      return;
    }

    // Create a map of key -> value (latest wins for duplicates)
    const updatesToSave = new Map(updates);
    pendingUpdatesRef.current.clear();

    setIsSaving(true);

    try {
      // Save all updates in parallel
      const promises = Array.from(updatesToSave.entries()).map(
        async ([key, value]) => {
          const setting = await apiSaveSetting(key, value);
          return { key, setting };
        },
      );

      const results = await Promise.all(promises);

      // Update local state with saved settings
      setSettings((prev) => {
        const updated = { ...prev };
        for (const { key, setting } of results) {
          updated[key] = setting;
        }
        return updated;
      });
    } catch (error) {
      console.error("Failed to save settings:", error);
      // Re-queue failed updates for retry
      for (const [key, value] of updatesToSave.entries()) {
        pendingUpdatesRef.current.set(key, value);
      }
    } finally {
      setIsSaving(false);
    }
  }, [apiSaveSetting]);

  /**
   * Schedule a debounced save of pending updates.
   */
  const scheduleSave = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      void savePendingUpdates();
    }, debounceMs);
  }, [debounceMs, savePendingUpdates]);

  /**
   * Update a setting value.
   * Queues the update and schedules a debounced save.
   */
  const updateSetting = useCallback(
    (key: string, value: string) => {
      // Update local state immediately for responsive UI
      setSettings((prev) => ({
        ...prev,
        [key]: {
          key,
          value,
          description: prev[key]?.description,
          updated_at: new Date().toISOString(),
        },
      }));

      // Queue for backend save (latest value wins for same key)
      pendingUpdatesRef.current.set(key, value);
      scheduleSave();
    },
    [scheduleSave],
  );

  /**
   * Get a setting value by key.
   */
  const getSetting = useCallback(
    (key: string): string | null => {
      return settings[key]?.value ?? null;
    },
    [settings],
  );

  // Load settings on mount
  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return (
    <SettingsContext.Provider
      value={{
        settings,
        isLoading,
        isSaving,
        updateSetting,
        getSetting,
      }}
    >
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
