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

/**
 * Scheduled jobs API service.
 *
 * Wraps `/api/admin/scheduled-jobs` endpoints for listing and updating job
 * definitions consumed by APScheduler.
 */

export interface ScheduledJob {
  id: number;
  job_name: string;
  description: string | null;
  task_type: string;
  cron_expression: string;
  enabled: boolean;
  user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface ScheduledJobUpdate {
  enabled?: boolean;
  cron_expression?: string;
}

const BASE = "/api/admin/scheduled-jobs";

async function getErrorDetail(response: Response): Promise<string | null> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    return typeof data.detail === "string" && data.detail.trim().length > 0
      ? data.detail
      : null;
  } catch {
    return null;
  }
}

/**
 * List all scheduled jobs.
 */
export async function listScheduledJobs(): Promise<ScheduledJob[]> {
  const response = await fetch(BASE, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  if (!response.ok) {
    const detail = await getErrorDetail(response);
    throw new Error(detail || "Failed to fetch scheduled jobs");
  }

  return (await response.json()) as ScheduledJob[];
}

/**
 * Update a scheduled job by its unique `job_name`.
 */
export async function updateScheduledJob(
  jobName: string,
  update: ScheduledJobUpdate,
): Promise<ScheduledJob> {
  const response = await fetch(`${BASE}/${encodeURIComponent(jobName)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(update),
  });

  if (!response.ok) {
    const detail = await getErrorDetail(response);
    throw new Error(detail || "Failed to update scheduled job");
  }

  return (await response.json()) as ScheduledJob;
}
