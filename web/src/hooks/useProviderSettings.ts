import { useEffect, useMemo, useState } from "react";
import { AVAILABLE_METADATA_PROVIDERS } from "@/components/profile/config/configurationConstants";
import { useUser } from "@/contexts/UserContext";

const SETTING_KEY = "preferred_metadata_providers";

/**
 * Parse enabled providers from setting value.
 *
 * Parameters
 * ----------
 * settingValue : string | null | undefined
 *     Raw setting value from storage.
 *
 * Returns
 * -------
 * Set<string>
 *     Set of enabled provider names.
 */
function parseEnabledProviders(
  settingValue: string | null | undefined,
): Set<string> {
  if (!settingValue) {
    // If no setting, all providers are enabled by default
    return new Set(AVAILABLE_METADATA_PROVIDERS);
  }
  try {
    const parsed = JSON.parse(settingValue) as string[];
    if (Array.isArray(parsed)) {
      if (parsed.length === 0) {
        // Empty array means user explicitly disabled all providers
        return new Set<string>();
      }
      // If setting has values, only those providers are enabled
      return new Set(parsed);
    }
    // Not an array, default to all enabled
    return new Set(AVAILABLE_METADATA_PROVIDERS);
  } catch {
    // Invalid JSON, default to all enabled
    return new Set(AVAILABLE_METADATA_PROVIDERS);
  }
}

/**
 * Determine if all providers are enabled.
 *
 * Parameters
 * ----------
 * enabledProviders : Set<string>
 *     Set of enabled provider names.
 *
 * Returns
 * -------
 * boolean
 *     True if all available providers are enabled.
 */
function areAllProvidersEnabled(enabledProviders: Set<string>): boolean {
  return (
    enabledProviders.size === AVAILABLE_METADATA_PROVIDERS.length &&
    AVAILABLE_METADATA_PROVIDERS.every((p) => enabledProviders.has(p))
  );
}

export interface UseProviderSettingsResult {
  /** Set of enabled provider names. */
  enabledProviders: Set<string>;
  /** Array of enabled provider names for API consumption. */
  enabledProviderNames: string[];
  /** Whether settings are currently loading. */
  isLoading: boolean;
  /** Toggle provider enabled state. */
  toggleProvider: (providerName: string) => void;
}

/**
 * Custom hook for managing metadata provider settings.
 *
 * Handles loading, parsing, and persisting enabled provider preferences.
 * Follows SRP by focusing solely on provider settings state management.
 * Follows IOC by using UserContext for persistence.
 * Follows DRY by centralizing provider settings logic.
 *
 * Returns
 * -------
 * UseProviderSettingsResult
 *     Enabled providers state, loading status, and toggle function.
 */
export function useProviderSettings(): UseProviderSettingsResult {
  const { getSetting, updateSetting, isLoading: isSettingsLoading } = useUser();

  // Parse enabled providers from setting
  const enabledProvidersFromSetting = useMemo(() => {
    if (isSettingsLoading) {
      return new Set<string>();
    }
    const settingValue = getSetting(SETTING_KEY);
    return parseEnabledProviders(settingValue);
  }, [getSetting, isSettingsLoading]);

  // Track enabled providers state
  const [enabledProviders, setEnabledProviders] = useState<Set<string>>(
    enabledProvidersFromSetting,
  );

  // Sync with setting when it loads or changes
  useEffect(() => {
    if (!isSettingsLoading) {
      setEnabledProviders(enabledProvidersFromSetting);
    }
  }, [enabledProvidersFromSetting, isSettingsLoading]);

  // Get enabled provider names from state
  const enabledProviderNames = useMemo(() => {
    return Array.from(enabledProviders);
  }, [enabledProviders]);

  // Toggle provider enabled state
  const toggleProvider = (providerName: string) => {
    // Calculate new state first
    const next = new Set(enabledProviders);
    if (next.has(providerName)) {
      next.delete(providerName);
    } else {
      next.add(providerName);
    }

    // Update local state
    setEnabledProviders(next);

    // Update backend setting
    // Store the array of enabled provider names
    // Empty array means user explicitly disabled all providers
    // Non-empty array means only those providers are enabled
    // (We don't store a special value for "all enabled" - that's the default when setting doesn't exist)
    const enabledArray = Array.from(next);
    const allEnabled = areAllProvidersEnabled(next);

    if (allEnabled) {
      // All providers enabled, store all provider names
      updateSetting(
        SETTING_KEY,
        JSON.stringify(Array.from(AVAILABLE_METADATA_PROVIDERS)),
      );
    } else {
      // Store the enabled providers array (can be empty if none enabled)
      updateSetting(SETTING_KEY, JSON.stringify(enabledArray));
    }
  };

  return {
    enabledProviders,
    enabledProviderNames,
    isLoading: isSettingsLoading,
    toggleProvider,
  };
}
