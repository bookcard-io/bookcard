import { useMemo } from "react";
import { AVAILABLE_METADATA_PROVIDERS } from "@/components/profile/config/configurationConstants";
import type { ProviderStatus } from "@/hooks/useMetadataSearchStream";
import { normalizeProviderName } from "@/utils/metadata";

export interface ProviderItem {
  /** Provider display name. */
  name: string;
  /** Current provider status. */
  status: ProviderStatus;
  /** Whether provider is enabled. */
  enabled: boolean;
}

/**
 * Create default pending status for a provider.
 *
 * Parameters
 * ----------
 * providerName : string
 *     Provider display name.
 *
 * Returns
 * -------
 * ProviderStatus
 *     Default pending status object.
 */
function createDefaultStatus(providerName: string): ProviderStatus {
  return {
    id: normalizeProviderName(providerName),
    name: providerName,
    status: "pending",
    resultCount: 0,
    discovered: 0,
  };
}

/**
 * Find provider status by name.
 *
 * Parameters
 * ----------
 * providerStatuses : Map<string, ProviderStatus>
 *     Map of provider statuses indexed by ID.
 * providerName : string
 *     Provider display name to find.
 *
 * Returns
 * -------
 * ProviderStatus | undefined
 *     Matching provider status or undefined if not found.
 */
function findProviderStatus(
  providerStatuses: Map<string, ProviderStatus>,
  providerName: string,
): ProviderStatus | undefined {
  for (const providerStatus of providerStatuses.values()) {
    if (providerStatus.name === providerName) {
      return providerStatus;
    }
  }
  return undefined;
}

export interface UseProviderItemsOptions {
  /** Map of provider statuses from search stream. */
  providerStatuses: Map<string, ProviderStatus>;
  /** Set of enabled provider names. */
  enabledProviders: Set<string>;
}

/**
 * Custom hook for creating provider items from statuses and enabled state.
 *
 * Combines provider status information with enabled state to create
 * display-ready provider items. Follows SRP by focusing solely on
 * provider item creation logic. Follows DRY by centralizing provider
 * item construction.
 *
 * Parameters
 * ----------
 * options : UseProviderItemsOptions
 *     Provider statuses and enabled providers set.
 *
 * Returns
 * -------
 * Array<ProviderItem>
 *     Array of provider items ready for display.
 */
export function useProviderItems({
  providerStatuses,
  enabledProviders,
}: UseProviderItemsOptions): Array<ProviderItem> {
  return useMemo(() => {
    return AVAILABLE_METADATA_PROVIDERS.map((providerName) => {
      // Find matching status by name
      const status =
        findProviderStatus(providerStatuses, providerName) ||
        createDefaultStatus(providerName);

      return {
        name: providerName,
        status,
        enabled: enabledProviders.has(providerName),
      };
    });
  }, [providerStatuses, enabledProviders]);
}
