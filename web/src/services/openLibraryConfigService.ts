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
 * OpenLibrary dump configuration API service.
 *
 * Handles all API calls for OpenLibrary dump configuration.
 * Follows SRP by handling only API communication.
 * Follows SOC by separating API concerns from state management.
 */

export interface OpenLibraryDumpConfig {
  id: number | null;
  authors_url: string | null;
  works_url: string | null;
  editions_url: string | null;
  default_process_authors: boolean;
  default_process_works: boolean;
  default_process_editions: boolean;
  staleness_threshold_days: number;
  enable_auto_download: boolean;
  enable_auto_process: boolean;
  auto_check_interval_hours: number;
  updated_at: string | null;
  created_at: string | null;
}

export interface OpenLibraryDumpConfigUpdate {
  authors_url?: string | null;
  works_url?: string | null;
  editions_url?: string | null;
  default_process_authors?: boolean;
  default_process_works?: boolean;
  default_process_editions?: boolean;
  staleness_threshold_days?: number;
  enable_auto_download?: boolean;
  enable_auto_process?: boolean;
  auto_check_interval_hours?: number;
}

const CONFIG_API_BASE = "/api/admin/openlibrary-dump-config";

/**
 * Get OpenLibrary dump configuration.
 *
 * Returns
 * -------
 * Promise<OpenLibraryDumpConfig>
 *     Configuration with defaults if not found.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function getOpenLibraryDumpConfig(): Promise<OpenLibraryDumpConfig> {
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

  return (await response.json()) as OpenLibraryDumpConfig;
}

/**
 * Update OpenLibrary dump configuration.
 *
 * Parameters
 * ----------
 * config : OpenLibraryDumpConfigUpdate
 *     Configuration updates.
 *
 * Returns
 * -------
 * Promise<OpenLibraryDumpConfig>
 *     Updated configuration.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function updateOpenLibraryDumpConfig(
  config: OpenLibraryDumpConfigUpdate,
): Promise<OpenLibraryDumpConfig> {
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

  return (await response.json()) as OpenLibraryDumpConfig;
}
