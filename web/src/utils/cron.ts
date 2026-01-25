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

export type ScheduleMode = "easy" | "advanced";
export type EasyFrequency = "daily" | "weekly" | "monthly";

export interface EasyScheduleState {
  frequency: EasyFrequency;
  hour: number;
  minute: number;
  weekday: number; // 0-6 (Sun-Sat) for weekly
  dayOfMonth: number; // 1-28 for monthly
}

export const WEEKDAY_OPTIONS = [
  { value: 0, label: "Sunday" },
  { value: 1, label: "Monday" },
  { value: 2, label: "Tuesday" },
  { value: 3, label: "Wednesday" },
  { value: 4, label: "Thursday" },
  { value: 5, label: "Friday" },
  { value: 6, label: "Saturday" },
];

export function clampInt(value: number, min: number, max: number): number {
  if (Number.isNaN(value)) return min;
  return Math.max(min, Math.min(max, Math.trunc(value)));
}

function pad2(value: number): string {
  const safe = clampInt(value, 0, 99);
  return safe.toString().padStart(2, "0");
}

export function buildCronFromEasy(easy: EasyScheduleState): string {
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

export function parseCronToEasy(cron: string): EasyScheduleState | null {
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

export function formatScheduleSummary(cronExpression: string): string {
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

export interface JobLike {
  description?: string | null;
  job_name: string;
}

export function formatTaskTitle(job: JobLike): string {
  const fromDescription = job.description?.trim();
  if (fromDescription) return fromDescription;
  return job.job_name
    .split("_")
    .map((p) => p.slice(0, 1).toUpperCase() + p.slice(1))
    .join(" ");
}
