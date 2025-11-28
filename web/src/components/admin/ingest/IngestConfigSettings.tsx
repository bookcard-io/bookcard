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

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  AVAILABLE_METADATA_PROVIDERS,
  PROVIDER_NAME_TO_ID,
} from "@/components/profile/config/configurationConstants";
import { ToggleButtonGroup } from "@/components/profile/ToggleButtonGroup";
import { useIngestConfig } from "@/hooks/useIngestConfig";
import { useMultiSelect } from "@/hooks/useMultiSelect";
import { cn } from "@/libs/utils";
import { PathInputWithSuggestions } from "../library/PathInputWithSuggestions";

/**
 * Convert provider IDs to display names.
 *
 * Parameters
 * ----------
 * providerIds : string[]
 *     List of provider IDs.
 *
 * Returns
 * -------
 * string[]
 *     List of provider display names.
 */
function convertProviderIdsToNames(providerIds: string[]): string[] {
  const idToName = Object.fromEntries(
    Object.entries(PROVIDER_NAME_TO_ID).map(([name, id]) => [id, name]),
  );
  return providerIds
    .map((id) => idToName[id])
    .filter((name): name is string => name !== undefined);
}

/**
 * Convert provider display names to IDs.
 *
 * Parameters
 * ----------
 * providerNames : string[]
 *     List of provider display names.
 *
 * Returns
 * -------
 * string[]
 *     List of provider IDs.
 */
function convertProviderNamesToIds(providerNames: string[]): string[] {
  return providerNames
    .map((name) => PROVIDER_NAME_TO_ID[name])
    .filter((id): id is string => id !== undefined);
}

export function IngestConfigSettings() {
  const {
    config,
    isLoading: isConfigLoading,
    updateField: updateConfigField,
    error,
  } = useIngestConfig();

  // Local state for ingest_dir to prevent debounced auto-save
  const [ingestDirValue, setIngestDirValue] = useState<string>("");
  // Track if the ingest_dir input is focused
  const [isIngestDirFocused, setIsIngestDirFocused] = useState(false);
  const ingestDirContainerRef = useRef<HTMLDivElement>(null);

  // Sync local state when config changes externally
  useEffect(() => {
    if (config?.ingest_dir !== undefined) {
      setIngestDirValue(config.ingest_dir);
    }
  }, [config?.ingest_dir]);

  // Monitor focus changes
  useEffect(() => {
    const handleFocusIn = (e: FocusEvent) => {
      if (
        ingestDirContainerRef.current?.contains(e.target as Node) &&
        (e.target as HTMLElement).tagName === "INPUT"
      ) {
        setIsIngestDirFocused(true);
      }
    };

    const handleFocusOut = (e: FocusEvent) => {
      if (
        ingestDirContainerRef.current &&
        !ingestDirContainerRef.current.contains(e.relatedTarget as Node)
      ) {
        setIsIngestDirFocused(false);
      }
    };

    document.addEventListener("focusin", handleFocusIn);
    document.addEventListener("focusout", handleFocusOut);

    return () => {
      document.removeEventListener("focusin", handleFocusIn);
      document.removeEventListener("focusout", handleFocusOut);
    };
  }, []);

  // Convert provider IDs from config to display names for UI
  const selectedProviderNames = useMemo(() => {
    if (!config?.metadata_providers) {
      return [];
    }
    return convertProviderIdsToNames(config.metadata_providers);
  }, [config?.metadata_providers]);

  // Track if update is from user action to prevent circular updates
  const isUserActionRef = useRef(false);

  // Manage multi-select state for provider names
  const { selected, toggle, setSelected } = useMultiSelect<string>({
    initialSelected: selectedProviderNames,
    onSelectionChange: (newSelected) => {
      // Only update config if this is a user action
      if (isUserActionRef.current) {
        // Convert display names back to IDs and update config
        const providerIds = convertProviderNamesToIds(newSelected);
        updateConfigField("metadata_providers", providerIds);
        isUserActionRef.current = false;
      }
    },
  });

  // Create stable string representation for dependency comparison
  const selectedProviderNamesStr = useMemo(
    () => [...selectedProviderNames].sort().join(","),
    [selectedProviderNames],
  );
  const selectedStr = useMemo(() => [...selected].sort().join(","), [selected]);

  // Sync selected state when config changes externally
  useEffect(() => {
    // Only update if values are different
    if (selectedStr !== selectedProviderNamesStr) {
      isUserActionRef.current = false;
      setSelected(selectedProviderNames);
    }
  }, [
    selectedProviderNamesStr,
    selectedStr,
    selectedProviderNames,
    setSelected,
  ]);

  // Wrap toggle to mark as user action
  const handleToggle = (providerName: string) => {
    isUserActionRef.current = true;
    toggle(providerName);
  };

  if (isConfigLoading) {
    return (
      <div className="py-6 text-center text-sm text-text-a30">
        Loading configuration...
      </div>
    );
  }

  if (!config) {
    return (
      <div className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
        Failed to load configuration
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error}
        </div>
      )}

      <div className="flex flex-col gap-6">
        {/* Basic Settings */}
        <div className="flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-text-a0">Basic Settings</h3>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {/* Watch Directory */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="ingest_dir"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Watch Directory
              </label>
              <div ref={ingestDirContainerRef} className="flex gap-2">
                <PathInputWithSuggestions
                  value={ingestDirValue}
                  onChange={(value) => {
                    setIngestDirValue(value);
                  }}
                  onSubmit={() => {
                    // No-op: changes are saved via Okay button
                  }}
                />
                {isIngestDirFocused && (
                  <>
                    <button
                      type="button"
                      onClick={() => {
                        updateConfigField("ingest_dir", ingestDirValue);
                      }}
                      disabled={ingestDirValue === config?.ingest_dir}
                      className={cn(
                        "flex items-center justify-center px-4 py-2",
                        "rounded-md border border-primary-a20 bg-primary-a0",
                        "font-medium text-[var(--color-text-primary-a0)] text-sm",
                        "transition-[background-color_0.2s,opacity_0.2s]",
                        "hover:bg-primary-a10",
                        "disabled:cursor-not-allowed disabled:opacity-50",
                        "focus:outline-none focus:ring-2 focus:ring-primary-a0 focus:ring-offset-2",
                      )}
                    >
                      Okay
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        // Revert to the latest config value (source of truth)
                        if (config?.ingest_dir !== undefined) {
                          setIngestDirValue(config.ingest_dir);
                        }
                      }}
                      disabled={ingestDirValue === config?.ingest_dir}
                      className={cn(
                        "flex items-center justify-center px-4 py-2",
                        "rounded-md border border-surface-a30 bg-surface-a10",
                        "font-medium text-sm text-text-a0",
                        "transition-[background-color_0.2s,opacity_0.2s]",
                        "hover:bg-surface-a20",
                        "disabled:cursor-not-allowed disabled:opacity-50",
                        "focus:outline-none focus:ring-2 focus:ring-primary-a0 focus:ring-offset-2",
                      )}
                      aria-label="Cancel"
                    >
                      <i className="pi pi-times" aria-hidden="true" />
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Enabled Toggle */}
            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                checked={config.enabled}
                onChange={(e) => {
                  updateConfigField("enabled", e.target.checked);
                }}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Enable Ingest
                </span>
                <span className="text-text-a30 text-xs">
                  Automatically process books from the watch directory.
                </span>
              </div>
            </label>
          </div>
        </div>

        {/* Metadata Settings */}
        <div className="flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-text-a0">
            Metadata Settings
          </h3>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {/* Metadata Merge Strategy */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="metadata_merge_strategy"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Merge Strategy
              </label>
              <select
                id="metadata_merge_strategy"
                value={config.metadata_merge_strategy}
                onChange={(e) => {
                  updateConfigField("metadata_merge_strategy", e.target.value);
                }}
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              >
                <option value="merge_best">Merge Best</option>
                <option value="first_wins">First Wins</option>
                <option value="last_wins">Last Wins</option>
                <option value="merge_all">Merge All</option>
              </select>
            </div>
          </div>

          {/* Metadata Providers */}
          <ToggleButtonGroup
            label="Metadata Providers"
            options={[...AVAILABLE_METADATA_PROVIDERS]}
            selected={selected}
            onToggle={handleToggle}
          />
        </div>

        {/* Retry Settings */}
        <div className="flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-text-a0">Retry Settings</h3>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {/* Max Attempts */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="retry_max_attempts"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Max Retry Attempts
              </label>
              <input
                type="number"
                id="retry_max_attempts"
                min="1"
                value={config.retry_max_attempts}
                onChange={(e) => {
                  const value = parseInt(e.target.value, 10);
                  if (!Number.isNaN(value) && value >= 1) {
                    updateConfigField("retry_max_attempts", value);
                  }
                }}
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              />
            </div>

            {/* Backoff Seconds */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="retry_backoff_seconds"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Backoff Seconds
              </label>
              <input
                type="number"
                id="retry_backoff_seconds"
                min="1"
                value={config.retry_backoff_seconds}
                onChange={(e) => {
                  const value = parseInt(e.target.value, 10);
                  if (!Number.isNaN(value) && value >= 1) {
                    updateConfigField("retry_backoff_seconds", value);
                  }
                }}
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              />
            </div>

            {/* Process Timeout */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="process_timeout_seconds"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Process Timeout (seconds)
              </label>
              <input
                type="number"
                id="process_timeout_seconds"
                min="1"
                value={config.process_timeout_seconds}
                onChange={(e) => {
                  const value = parseInt(e.target.value, 10);
                  if (!Number.isNaN(value) && value >= 1) {
                    updateConfigField("process_timeout_seconds", value);
                  }
                }}
                className="w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
