import { useEffect, useMemo, useState } from "react";
import { useUser } from "@/contexts/UserContext";

const SETTING_KEY = "preferred_metadata_providers";
const DEFAULT_VALUE: string[] = [];

/**
 * Parse preferred providers from setting value.
 *
 * Parameters
 * ----------
 * settingValue : string | null | undefined
 *     Raw setting value from storage.
 *
 * Returns
 * -------
 * Set<string>
 *     Set of preferred provider names.
 */
function parsePreferredProviders(
  settingValue: string | null | undefined,
): Set<string> {
  if (!settingValue) {
    return new Set<string>();
  }
  try {
    const parsed = JSON.parse(settingValue) as string[];
    if (Array.isArray(parsed)) {
      return new Set(parsed);
    }
    return new Set<string>();
  } catch {
    return new Set<string>();
  }
}

export interface UsePreferredProvidersResult {
  /** Set of preferred provider names. */
  preferredProviders: Set<string>;
  /** Array of preferred provider names for API consumption. */
  preferredProviderNames: string[];
  /** Whether settings are currently loading. */
  isLoading: boolean;
  /** Toggle provider preferred state. */
  togglePreferred: (providerName: string) => void;
}

/**
 * Custom hook for managing preferred metadata provider settings.
 *
 * Handles loading, parsing, and persisting preferred provider preferences.
 * Follows SRP by focusing solely on preferred provider state management.
 * Follows IOC by using UserContext for persistence.
 * Follows DRY by centralizing preferred provider settings logic.
 *
 * Returns
 * -------
 * UsePreferredProvidersResult
 *     Preferred providers state, loading status, and toggle function.
 */
export function usePreferredProviders(): UsePreferredProvidersResult {
  const { getSetting, updateSetting, isLoading: isSettingsLoading } = useUser();

  // Parse preferred providers from setting
  const preferredProvidersFromSetting = useMemo(() => {
    if (isSettingsLoading) {
      return new Set<string>();
    }
    const settingValue = getSetting(SETTING_KEY);
    return parsePreferredProviders(settingValue);
  }, [getSetting, isSettingsLoading]);

  // Track preferred providers state
  const [preferredProviders, setPreferredProviders] = useState<Set<string>>(
    preferredProvidersFromSetting,
  );

  // Sync with setting when it loads or changes
  useEffect(() => {
    if (!isSettingsLoading) {
      setPreferredProviders(preferredProvidersFromSetting);
    }
  }, [preferredProvidersFromSetting, isSettingsLoading]);

  // Get preferred provider names from state
  const preferredProviderNames = useMemo(() => {
    return Array.from(preferredProviders);
  }, [preferredProviders]);

  // Toggle provider preferred state
  const togglePreferred = (providerName: string) => {
    const next = new Set(preferredProviders);
    if (next.has(providerName)) {
      next.delete(providerName);
    } else {
      next.add(providerName);
    }
    setPreferredProviders(next);
    // Update backend setting
    updateSetting(SETTING_KEY, JSON.stringify(Array.from(next)));
  };

  return {
    preferredProviders,
    preferredProviderNames,
    isLoading: isSettingsLoading,
    togglePreferred,
  };
}
