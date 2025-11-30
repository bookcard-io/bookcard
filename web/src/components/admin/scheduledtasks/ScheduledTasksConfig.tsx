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

import { NumberInput } from "@/components/forms/NumberInput";
import { useBlurAfterClick } from "@/components/profile/BlurAfterClickContext";
import { useScheduledTasksConfig } from "@/hooks/useScheduledTasksConfig";

/**
 * Scheduled tasks configuration component.
 *
 * Manages scheduled tasks configuration settings including timing,
 * cover generation, database operations, and EPUB fixer options.
 *
 * Follows SOLID principles:
 * - SRP: Delegates business logic to useScheduledTasksConfig hook
 * - IOC: Uses dependency injection via hook callbacks
 * - SOC: Separates concerns into hook layer and UI layer
 * - DRY: Reuses form components and centralizes state management
 *
 * Features:
 * - Time and duration configuration
 * - Boolean toggles for various scheduled tasks
 * - Auto-save with debouncing
 * - Loading and error states
 */
export function ScheduledTasksConfig() {
  const { onBlurChange } = useBlurAfterClick();
  const { config, isLoading, isSaving, error, updateField } =
    useScheduledTasksConfig();

  if (isLoading) {
    return (
      <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
        <p className="text-sm text-text-a30">Loading configuration...</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
        <p className="text-danger-a10 text-sm">Failed to load configuration</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
      <div className="mb-4 flex items-center gap-3">
        <h2 className="font-semibold text-text-a0 text-xl">
          Scheduled Tasks Configuration
        </h2>
        {isSaving && (
          <div className="flex items-center gap-2 text-sm text-text-a30">
            <i className="pi pi-spinner animate-spin" aria-hidden="true" />
            <span>Saving...</span>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error}
        </div>
      )}

      <div className="flex flex-col gap-6">
        {/* Timing Configuration */}
        <div className="flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-text-a0">Timing</h3>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <NumberInput
              id="start_time_hour"
              label="Start Time (Hour)"
              value={config.start_time_hour}
              onChange={(e) => {
                const value = parseInt(e.target.value, 10);
                if (!Number.isNaN(value) && value >= 0 && value <= 23) {
                  updateField("start_time_hour", value);
                }
              }}
              min={0}
              max={23}
              step={1}
              helperText="Hour of day to start scheduled tasks (0-23)"
            />

            <NumberInput
              id="duration_hours"
              label="Duration (Hours)"
              value={config.duration_hours}
              onChange={(e) => {
                const value = parseInt(e.target.value, 10);
                if (!Number.isNaN(value) && value >= 1 && value <= 24) {
                  updateField("duration_hours", value);
                }
              }}
              min={1}
              max={24}
              step={1}
              helperText="Maximum duration for scheduled tasks in hours (1-24)"
            />
          </div>
        </div>

        {/* Tasks To Run */}
        <div className="flex flex-col gap-4">
          <h3 className="font-semibold text-lg text-text-a0">Tasks To Run</h3>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                checked={config.generate_book_covers}
                onChange={onBlurChange((e) => {
                  updateField("generate_book_covers", e.target.checked);
                })}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Generate Book Covers
                </span>
                <span className="text-text-a30 text-xs">
                  Generate book cover thumbnails during scheduled tasks.
                </span>
              </div>
            </label>

            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                checked={config.generate_series_covers}
                onChange={onBlurChange((e) => {
                  updateField("generate_series_covers", e.target.checked);
                })}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Generate Series Covers
                </span>
                <span className="text-text-a30 text-xs">
                  Generate series cover thumbnails during scheduled tasks.
                </span>
              </div>
            </label>

            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                checked={config.reconnect_database}
                onChange={onBlurChange((e) => {
                  updateField("reconnect_database", e.target.checked);
                })}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Reconnect Database
                </span>
                <span className="text-text-a30 text-xs">
                  Reconnect to Calibre database during scheduled tasks.
                </span>
              </div>
            </label>

            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                checked={config.metadata_backup}
                onChange={onBlurChange((e) => {
                  updateField("metadata_backup", e.target.checked);
                })}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Metadata Backup
                </span>
                <span className="text-text-a30 text-xs">
                  Backup metadata during scheduled tasks.
                </span>
              </div>
            </label>

            <label className="flex cursor-pointer items-start gap-3 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4 transition-colors hover:border-surface-a30">
              <input
                type="checkbox"
                checked={config.epub_fixer_daily_scan}
                onChange={onBlurChange((e) => {
                  updateField("epub_fixer_daily_scan", e.target.checked);
                })}
                className="mt-0.5 h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
              />
              <div className="flex flex-col gap-1">
                <span className="font-medium text-sm text-text-a10">
                  Daily EPUB Fixer Scan
                </span>
                <span className="text-text-a30 text-xs">
                  Enable daily EPUB fixer scan during scheduled tasks.
                </span>
              </div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
