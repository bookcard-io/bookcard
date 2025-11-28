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

import { useIngestConfig } from "@/hooks/useIngestConfig";
import { useBlurAfterClick } from "@/components/profile/BlurAfterClickContext";
import { PathInputWithSuggestions } from "../library/PathInputWithSuggestions";

/**
 * Ingest configuration settings component.
 *
 * Manages ingest service configuration including watch directory, metadata
 * providers, retry settings, and processing options.
 *
 * Follows SOLID principles:
 * - SRP: Delegates business logic to useIngestConfig hook
 * - IOC: Uses dependency injection via hook callbacks
 * - SOC: Separates concerns into hook layer and UI layer
 * - DRY: Reuses form components and centralizes state management
 */
export function IngestConfigSettings() {
  const { onBlurChange } = useBlurAfterClick();
  const {
    config,
    isLoading: isConfigLoading,
    updateField: updateConfigField,
    error,
  } = useIngestConfig();

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
          <h3 className="font-semibold text-lg text-text-a0">
            Basic Settings
          </h3>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {/* Watch Directory */}
            <div className="flex flex-col gap-2">
              <label
                htmlFor="ingest_dir"
                className="font-medium text-sm text-text-a10 leading-normal"
              >
                Watch Directory
              </label>
              <PathInputWithSuggestions
                value={config.ingest_dir}
                onChange={(value) => {
                  updateConfigField("ingest_dir", value);
                }}
                onSubmit={() => {
                  // No-op: changes are auto-saved via updateField
                }}
              />
            </div>

            {/* Enabled Toggle */}
            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                checked={config.enabled}
                onChange={onBlurChange((e) => {
                  updateConfigField("enabled", e.target.checked);
                })}
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

            {/* Auto Delete After Ingest */}
            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                checked={config.auto_delete_after_ingest}
                onChange={onBlurChange((e) => {
                  updateConfigField("auto_delete_after_ingest", e.target.checked);
                })}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Auto Delete After Ingest
                </span>
                <span className="text-text-a30 text-xs">
                  Delete source files after successful ingest.
                </span>
              </div>
            </label>
          </div>
        </div>

        {/* Retry Settings */}
        <div className="flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-text-a0">
            Retry Settings
          </h3>
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
