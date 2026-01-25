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

import { useState } from "react";
import { FaChevronDown, FaChevronUp, FaCog } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { NumberInput } from "@/components/forms/NumberInput";
import { Select } from "@/components/forms/Select";
import { TextInput } from "@/components/forms/TextInput";
import { useBlurAfterClick } from "@/components/profile/BlurAfterClickContext";
import type {
  ScheduledJob,
  ScheduledJobUpdate,
} from "@/services/scheduledJobsService";
import {
  buildCronFromEasy,
  clampInt,
  type EasyFrequency,
  type EasyScheduleState,
  formatScheduleSummary,
  formatTaskTitle,
  parseCronToEasy,
  type ScheduleMode,
  WEEKDAY_OPTIONS,
} from "@/utils/cron";

interface ScheduledTaskItemProps {
  job: ScheduledJob;
  defaultEasy: EasyScheduleState;
  scheduleMode: ScheduleMode;
  onUpdateJob: (jobName: string, update: ScheduledJobUpdate) => void;
}

export function ScheduledTaskItem({
  job,
  defaultEasy,
  scheduleMode,
  onUpdateJob,
}: ScheduledTaskItemProps) {
  const { onBlurChange } = useBlurAfterClick();
  const [isExpanded, setIsExpanded] = useState(false);

  // Local state for the editor
  const [easy, setEasy] = useState<EasyScheduleState>(
    () => parseCronToEasy(job.cron_expression) ?? defaultEasy,
  );
  const [advancedCron, setAdvancedCron] = useState<string>(job.cron_expression);

  const jobName = job.job_name;

  const handleEasyChange = (patch: Partial<EasyScheduleState>) => {
    const nextEasy = { ...easy, ...patch };
    setEasy(nextEasy);
    onUpdateJob(jobName, {
      cron_expression: buildCronFromEasy(nextEasy),
    });
  };

  const handleCronChange = (cron: string) => {
    setAdvancedCron(cron);
    onUpdateJob(jobName, { cron_expression: cron });
  };

  const handleIntChange = (
    val: string,
    min: number,
    max: number,
    setter: (v: number) => void,
  ) => {
    const num = parseInt(val, 10);
    if (!Number.isNaN(num)) setter(clampInt(num, min, max));
  };

  return (
    <div className="flex flex-col gap-2">
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
            <span>{formatScheduleSummary(job.cron_expression)}</span>
            {job.last_run_at && (
              <>
                {" • "}
                <span>
                  Last run: {new Date(job.last_run_at).toLocaleString()}
                </span>
              </>
            )}
            {job.last_run_status && (
              <span
                className={`ml-2 rounded px-1.5 py-0.5 font-medium text-xs ${
                  job.last_run_status === "completed"
                    ? "bg-success-a20 text-success-a0"
                    : job.last_run_status === "failed"
                      ? "bg-danger-a20 text-danger-a0"
                      : "bg-surface-a20 text-text-a30"
                }`}
              >
                {job.last_run_status}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={job.enabled}
              onChange={onBlurChange((e) => {
                onUpdateJob(jobName, { enabled: e.target.checked });
              })}
              className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
            />
            <span className="text-sm text-text-a30">Enabled</span>
          </label>
          <Button
            variant="ghost"
            size="xsmall"
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? "Close schedule editor" : "Edit schedule"}
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
                  <span className="font-medium">Easy</span> mode will overwrite
                  it.
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
                    handleIntChange(e.target.value, 0, 6, (weekday) =>
                      handleEasyChange({ weekday }),
                    );
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
                    handleIntChange(e.target.value, 1, 28, (dayOfMonth) =>
                      handleEasyChange({ dayOfMonth }),
                    );
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
                    handleIntChange(e.target.value, 0, 23, (hour) =>
                      handleEasyChange({ hour }),
                    );
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
                    handleIntChange(e.target.value, 0, 59, (minute) =>
                      handleEasyChange({ minute }),
                    );
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
}
