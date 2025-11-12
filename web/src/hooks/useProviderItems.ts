// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import { useMemo } from "react";
import { AVAILABLE_METADATA_PROVIDERS } from "@/components/profile/config/configurationConstants";
import type { ProviderStatus } from "@/hooks/useMetadataSearchStream";
import { normalizeProviderName } from "@/utils/metadata";

export interface ProviderItem {
  /** Provider display name. */
  name: string;
  /** Current provider status. */
  status: ProviderStatus;
  /** Whether provider is enabled (visible in modal). */
  enabled: boolean;
  /** Whether provider is preferred (sent to backend). */
  preferred: boolean;
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
  /** Set of enabled provider names (controls visibility). */
  enabledProviders: Set<string>;
  /** Set of preferred provider names (controls backend search). */
  preferredProviders: Set<string>;
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
  preferredProviders,
}: UseProviderItemsOptions): Array<ProviderItem> {
  return useMemo(() => {
    // Only show providers that are enabled
    return AVAILABLE_METADATA_PROVIDERS.filter((providerName) =>
      enabledProviders.has(providerName),
    ).map((providerName) => {
      // Find matching status by name
      const status =
        findProviderStatus(providerStatuses, providerName) ||
        createDefaultStatus(providerName);

      return {
        name: providerName,
        status,
        enabled: enabledProviders.has(providerName),
        preferred: preferredProviders.has(providerName),
      };
    });
  }, [providerStatuses, enabledProviders, preferredProviders]);
}
