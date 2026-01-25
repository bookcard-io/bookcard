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

import { useMemo, useState } from "react";
import { FaToggleOff, FaToggleOn } from "react-icons/fa";
import { useScheduledJobs } from "@/hooks/useScheduledJobs";
import { useScheduledTasksConfig } from "@/hooks/useScheduledTasksConfig";
import type { EasyScheduleState, ScheduleMode } from "@/utils/cron";
import { ScheduledTaskItem } from "./ScheduledTaskItem";

/**
 * Scheduled tasks configuration component.
 *
 * Manages scheduled job definitions (enabled + cron schedule) consumed by the
 * server scheduler.
 *
 * Refactored to follow SOLID principles:
 * - SRP: Domain logic moved to utils/cron.ts, item rendering to ScheduledTaskItem.
 * - SOC: Separates list management from item editing.
 */
export function ScheduledTasksConfig() {
  const { jobs, isLoading, isSaving, error, updateJob } = useScheduledJobs();
  const {
    config: systemConfig,
    isLoading: isConfigLoading,
    isSaving: isConfigSaving,
    error: configError,
    updateField,
  } = useScheduledTasksConfig();

  const [scheduleMode, setScheduleMode] = useState<ScheduleMode>("advanced");

  const defaultEasy = useMemo<EasyScheduleState>(
    () => ({
      frequency: "daily",
      hour: 4,
      minute: 0,
      weekday: 1,
      dayOfMonth: 1,
    }),
    [],
  );

  if (isLoading || isConfigLoading) {
    return (
      <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
        <p className="text-sm text-text-a30">Loading configuration...</p>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
        <p className="text-sm text-text-a30">No scheduled tasks found.</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
      <div className="mb-4 flex items-center gap-3">
        <h2 className="font-semibold text-text-a0 text-xl">
          Scheduled Tasks Configuration
        </h2>
        {(isSaving || isConfigSaving) && (
          <div className="flex items-center gap-2 text-sm text-text-a30">
            <i className="pi pi-spinner animate-spin" aria-hidden="true" />
            <span>Saving...</span>
          </div>
        )}
      </div>

      {(error || configError) && (
        <div className="mb-4 rounded-md bg-danger-a20 px-4 py-3 text-danger-a0 text-sm">
          {error || configError}
        </div>
      )}

      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="font-semibold text-lg text-text-a0">Tasks</h3>
            <div className="flex items-center gap-3">
              {systemConfig && (
                <div className="flex items-center gap-2">
                  <label
                    htmlFor="duration_hours"
                    className="whitespace-nowrap text-sm text-text-a30"
                  >
                    Max duration (hrs):
                  </label>
                  <input
                    id="duration_hours"
                    type="number"
                    min={1}
                    max={24}
                    step={1}
                    value={systemConfig.duration_hours}
                    onChange={(e) => {
                      const value = Number.parseInt(e.target.value, 10);
                      if (!Number.isNaN(value) && value >= 1 && value <= 24) {
                        updateField("duration_hours", value);
                      }
                    }}
                    className="h-8 w-16 rounded-md border border-surface-a20 bg-surface-tonal-a0 px-2 text-sm text-text-a0 focus:border-primary-a0 focus:outline-none focus:ring-1 focus:ring-primary-a0"
                  />
                </div>
              )}
              <button
                type="button"
                onClick={() => {
                  setScheduleMode(
                    scheduleMode === "advanced" ? "easy" : "advanced",
                  );
                }}
                className="flex items-center gap-2 rounded-md border border-surface-a20 bg-surface-tonal-a0 px-3 py-2 text-sm text-text-a0 transition-colors hover:bg-surface-tonal-a10"
              >
                {scheduleMode === "advanced" ? (
                  <FaToggleOn className="h-5 w-5 text-primary-a0" />
                ) : (
                  <FaToggleOff className="h-5 w-5 text-text-a30" />
                )}
                <span>Use cron expression</span>
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            {jobs.map((job) => (
              <ScheduledTaskItem
                key={job.job_name}
                job={job}
                defaultEasy={defaultEasy}
                scheduleMode={scheduleMode}
                onUpdateJob={updateJob}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
