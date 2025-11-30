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
 * Scheduled tasks configuration API service.
 *
 * Handles all API calls for scheduled tasks configuration.
 * Follows SRP by handling only API communication.
 * Follows SOC by separating API concerns from state management.
 */

export interface ScheduledTasksConfig {
  id: number | null;
  start_time_hour: number;
  duration_hours: number;
  generate_book_covers: boolean;
  generate_series_covers: boolean;
  reconnect_database: boolean;
  metadata_backup: boolean;
  epub_fixer_daily_scan: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface ScheduledTasksConfigUpdate {
  start_time_hour?: number;
  duration_hours?: number;
  generate_book_covers?: boolean;
  generate_series_covers?: boolean;
  reconnect_database?: boolean;
  metadata_backup?: boolean;
  epub_fixer_daily_scan?: boolean;
}

const CONFIG_API_BASE = "/api/admin/scheduled-tasks-config";

/**
 * Get scheduled tasks configuration.
 *
 * Returns
 * -------
 * Promise<ScheduledTasksConfig>
 *     Configuration with defaults if not found.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function getScheduledTasksConfig(): Promise<ScheduledTasksConfig> {
  const response = await fetch(CONFIG_API_BASE, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to fetch configuration");
  }

  return (await response.json()) as ScheduledTasksConfig;
}

/**
 * Update scheduled tasks configuration.
 *
 * Parameters
 * ----------
 * config : ScheduledTasksConfigUpdate
 *     Configuration updates.
 *
 * Returns
 * -------
 * Promise<ScheduledTasksConfig>
 *     Updated configuration.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function updateScheduledTasksConfig(
  config: ScheduledTasksConfigUpdate,
): Promise<ScheduledTasksConfig> {
  const response = await fetch(CONFIG_API_BASE, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || "Failed to update configuration");
  }

  return (await response.json()) as ScheduledTasksConfig;
}
