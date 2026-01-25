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

import { useEffect, useMemo, useState } from "react";
import {
  FaChevronDown,
  FaChevronUp,
  FaCog,
  FaToggleOff,
  FaToggleOn,
} from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { NumberInput } from "@/components/forms/NumberInput";
import { Select } from "@/components/forms/Select";
import { TextInput } from "@/components/forms/TextInput";
import { useBlurAfterClick } from "@/components/profile/BlurAfterClickContext";
import { useScheduledJobs } from "@/hooks/useScheduledJobs";
import { useScheduledTasksConfig } from "@/hooks/useScheduledTasksConfig";
import type { ScheduledJob } from "@/services/scheduledJobsService";

type ScheduleMode = "easy" | "advanced";
type EasyFrequency = "daily" | "weekly" | "monthly";

interface EasyScheduleState {
  frequency: EasyFrequency;
  hour: number;
  minute: number;
  weekday: number; // 0-6 (Sun-Sat) for weekly
  dayOfMonth: number; // 1-28 for monthly
}

function clampInt(value: number, min: number, max: number): number {
  if (Number.isNaN(value)) return min;
  return Math.max(min, Math.min(max, Math.trunc(value)));
}

function buildCronFromEasy(easy: EasyScheduleState): string {
  const minute = clampInt(easy.minute, 0, 59);
  const hour = clampInt(easy.hour, 0, 23);

  if (easy.frequency === "weekly") {
    const dow = clampInt(easy.weekday, 0, 6);
    return `${minute} ${hour} * * ${dow}`;
  }
  if (easy.frequency === "monthly") {
    const dom = clampInt(easy.dayOfMonth, 1, 28);
    return `${minute} ${hour} ${dom} * *`;
  }
  // daily
  return `${minute} ${hour} * * *`;
}

function parseCronToEasy(cron: string): EasyScheduleState | null {
  // Expect standard 5-field crontab: minute hour day month day_of_week
  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) return null;
  const minStr = parts[0];
  const hourStr = parts[1];
  const domStr = parts[2];
  const monStr = parts[3];
  const dowStr = parts[4];
  if (
    minStr === undefined ||
    hourStr === undefined ||
    domStr === undefined ||
    monStr === undefined ||
    dowStr === undefined
  ) {
    return null;
  }

  const minute = Number.parseInt(minStr, 10);
  const hour = Number.parseInt(hourStr, 10);
  if (!Number.isFinite(minute) || !Number.isFinite(hour)) return null;
  if (minute < 0 || minute > 59 || hour < 0 || hour > 23) return null;

  // Only parse simple patterns we generate in easy mode.
  if (monStr !== "*") return null;

  // daily: m h * * *
  if (domStr === "*" && dowStr === "*") {
    return {
      frequency: "daily",
      hour,
      minute,
      weekday: 1,
      dayOfMonth: 1,
    };
  }

  // weekly: m h * * <0-6>
  if (domStr === "*" && dowStr !== "*") {
    const weekday = Number.parseInt(dowStr, 10);
    if (!Number.isFinite(weekday) || weekday < 0 || weekday > 6) return null;
    return {
      frequency: "weekly",
      hour,
      minute,
      weekday,
      dayOfMonth: 1,
    };
  }

  // monthly: m h <1-28> * *
  if (dowStr === "*" && domStr !== "*") {
    const dayOfMonth = Number.parseInt(domStr, 10);
    if (!Number.isFinite(dayOfMonth) || dayOfMonth < 1 || dayOfMonth > 28)
      return null;
    return {
      frequency: "monthly",
      hour,
      minute,
      weekday: 1,
      dayOfMonth,
    };
  }

  return null;
}

function formatTaskTitle(job: ScheduledJob): string {
  const fromDescription = job.description?.trim();
  if (fromDescription) return fromDescription;
  return job.job_name
    .split("_")
    .map((p) => p.slice(0, 1).toUpperCase() + p.slice(1))
    .join(" ");
}

function pad2(value: number): string {
  const safe = clampInt(value, 0, 99);
  return safe.toString().padStart(2, "0");
}

function formatScheduleSummary(cronExpression: string): string {
  const easy = parseCronToEasy(cronExpression);
  if (!easy) {
    return `Cron: ${cronExpression}`;
  }

  const time = `${pad2(easy.hour)}:${pad2(easy.minute)}`;
  if (easy.frequency === "daily") {
    return `Daily at ${time}`;
  }
  if (easy.frequency === "weekly") {
    const weekday = WEEKDAY_OPTIONS.find(
      (w) => w.value === easy.weekday,
    )?.label;
    return `Weekly on ${weekday ?? "weekday"} at ${time}`;
  }
  return `Monthly on day ${easy.dayOfMonth} at ${time}`;
}

const WEEKDAY_OPTIONS = [
  { value: 0, label: "Sunday" },
  { value: 1, label: "Monday" },
  { value: 2, label: "Tuesday" },
  { value: 3, label: "Wednesday" },
  { value: 4, label: "Thursday" },
  { value: 5, label: "Friday" },
  { value: 6, label: "Saturday" },
];

/**
 * Scheduled tasks configuration component.
 *
 * Manages scheduled job definitions (enabled + cron schedule) consumed by the
 * server scheduler.
 *
 * Follows SOLID principles:
 * - SRP: Delegates business logic to useScheduledJobs hook
 * - IOC: Uses dependency injection via hook callbacks
 * - SOC: Separates concerns into hook layer and UI layer
 * - DRY: Reuses form components and centralizes state management
 *
 * Features:
 * - Per-job enable/disable
 * - Easy schedule presets (daily/weekly/monthly) + start time
 * - Advanced cron input
 * - Auto-save with debouncing
 * - Loading and error states
 */
export function ScheduledTasksConfig() {
  const { onBlurChange } = useBlurAfterClick();
  const { jobs, isLoading, isSaving, error, updateJob } = useScheduledJobs();
  const {
    config: systemConfig,
    isLoading: isConfigLoading,
    isSaving: isConfigSaving,
    error: configError,
    updateField,
  } = useScheduledTasksConfig();

  const [expandedJobName, setExpandedJobName] = useState<string | null>(null);
  const [scheduleMode, setScheduleMode] = useState<ScheduleMode>("advanced");

  // Per-job editor state (UI only)
  const [easyByJob, setEasyByJob] = useState<Record<string, EasyScheduleState>>(
    {},
  );
  const [advancedCronByJob, setAdvancedCronByJob] = useState<
    Record<string, string>
  >({});

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

  useEffect(() => {
    // Initialize editor state for newly loaded jobs.
    setEasyByJob((prev) => {
      const next = { ...prev };
      for (const job of jobs) {
        if (next[job.job_name]) continue;
        next[job.job_name] =
          parseCronToEasy(job.cron_expression) ?? defaultEasy;
      }
      return next;
    });

    setAdvancedCronByJob((prev) => {
      const next = { ...prev };
      for (const job of jobs) {
        if (typeof next[job.job_name] === "string") continue;
        next[job.job_name] = job.cron_expression;
      }
      return next;
    });
  }, [defaultEasy, jobs]);

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
            {jobs.map((job) => {
              const jobName = job.job_name;
              const easy = easyByJob[jobName] ?? defaultEasy;
              const advancedCron =
                advancedCronByJob[jobName] ?? job.cron_expression;
              const isExpanded = expandedJobName === jobName;

              const handleEasyChange = (patch: Partial<EasyScheduleState>) => {
                const nextEasy = { ...easy, ...patch };
                setEasyByJob((prev) => ({ ...prev, [jobName]: nextEasy }));
                updateJob(jobName, {
                  cron_expression: buildCronFromEasy(nextEasy),
                });
              };

              const handleCronChange = (cron: string) => {
                setAdvancedCronByJob((prev) => ({ ...prev, [jobName]: cron }));
                updateJob(jobName, { cron_expression: cron });
              };

              return (
                <div key={jobName} className="flex flex-col gap-2">
                  <div
                    className={`flex items-center justify-between rounded-md border bg-[var(--color-surface-tonal-a10)] p-4 ${
                      job.enabled
                        ? "border-[var(--color-success-a0)] opacity-100"
                        : "border-[var(--color-surface-a20)] opacity-50"
                    }`}
                  >
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-text-a0">
                          {formatTaskTitle(job)}
                        </span>
                        {!job.enabled && (
                          <span className="rounded bg-[var(--color-surface-a20)] px-2 py-0.5 text-text-a30 text-xs">
                            Disabled
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-text-a30">
                        <span className="capitalize">{job.task_type}</span> •{" "}
                        <span>
                          {formatScheduleSummary(job.cron_expression)}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <label className="flex cursor-pointer items-center gap-2">
                        <input
                          type="checkbox"
                          checked={job.enabled}
                          onChange={onBlurChange((e) => {
                            updateJob(jobName, { enabled: e.target.checked });
                          })}
                          className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
                        />
                        <span className="text-sm text-text-a30">Enabled</span>
                      </label>
                      <Button
                        variant="ghost"
                        size="xsmall"
                        onClick={() => {
                          setExpandedJobName((prev) =>
                            prev === jobName ? null : jobName,
                          );
                        }}
                        title={
                          isExpanded ? "Close schedule editor" : "Edit schedule"
                        }
                      >
                        <FaCog className="h-4 w-4" />
                        {isExpanded ? (
                          <FaChevronUp className="h-4 w-4" />
                        ) : (
                          <FaChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4">
                      {scheduleMode === "easy" ? (
                        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-4">
                          {parseCronToEasy(job.cron_expression) === null && (
                            <div className="text-text-a30 text-xs md:col-span-4">
                              This task currently uses a custom cron. Editing in{" "}
                              <span className="font-medium">Easy</span> mode
                              will overwrite it.
                            </div>
                          )}
                          <Select
                            id={`${jobName}-frequency`}
                            label="Frequency"
                            value={easy.frequency}
                            onChange={(e) => {
                              const freq = e.target.value as EasyFrequency;
                              handleEasyChange({ frequency: freq });
                            }}
                            options={[
                              { value: "daily", label: "Daily" },
                              { value: "weekly", label: "Weekly" },
                              { value: "monthly", label: "Monthly" },
                            ]}
                          />

                          {easy.frequency === "weekly" ? (
                            <Select
                              id={`${jobName}-weekday`}
                              label="Weekday"
                              value={easy.weekday}
                              onChange={(e) => {
                                const weekday = Number.parseInt(
                                  e.target.value,
                                  10,
                                );
                                handleEasyChange({
                                  weekday: clampInt(weekday, 0, 6),
                                });
                              }}
                              options={WEEKDAY_OPTIONS}
                            />
                          ) : (
                            <div />
                          )}

                          {easy.frequency === "monthly" ? (
                            <NumberInput
                              id={`${jobName}-dayOfMonth`}
                              label="Day (1-28)"
                              value={easy.dayOfMonth}
                              onChange={(e) => {
                                const dom = Number.parseInt(e.target.value, 10);
                                if (!Number.isNaN(dom)) {
                                  handleEasyChange({
                                    dayOfMonth: clampInt(dom, 1, 28),
                                  });
                                }
                              }}
                              min={1}
                              max={28}
                              step={1}
                            />
                          ) : (
                            <div />
                          )}

                          <div className="grid grid-cols-2 gap-3">
                            <NumberInput
                              id={`${jobName}-hour`}
                              label="Hour"
                              value={easy.hour}
                              onChange={(e) => {
                                const hour = Number.parseInt(
                                  e.target.value,
                                  10,
                                );
                                if (!Number.isNaN(hour)) {
                                  handleEasyChange({
                                    hour: clampInt(hour, 0, 23),
                                  });
                                }
                              }}
                              min={0}
                              max={23}
                              step={1}
                            />
                            <NumberInput
                              id={`${jobName}-minute`}
                              label="Minute"
                              value={easy.minute}
                              onChange={(e) => {
                                const minute = Number.parseInt(
                                  e.target.value,
                                  10,
                                );
                                if (!Number.isNaN(minute)) {
                                  handleEasyChange({
                                    minute: clampInt(minute, 0, 59),
                                  });
                                }
                              }}
                              min={0}
                              max={59}
                              step={1}
                            />
                          </div>

                          <div className="text-text-a30 text-xs md:col-span-4">
                            Cron preview: {buildCronFromEasy(easy)}
                          </div>
                        </div>
                      ) : (
                        <div className="mt-3">
                          <TextInput
                            id={`${jobName}-cron`}
                            label="Cron expression"
                            value={advancedCron}
                            onChange={(e) => handleCronChange(e.target.value)}
                            placeholder="minute hour day month day_of_week (e.g. 0 4 * * *)"
                            helperText='Standard 5-field cron: "minute hour day month day_of_week"'
                          />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
