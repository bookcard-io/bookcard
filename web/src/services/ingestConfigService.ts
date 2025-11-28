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
 * Ingest configuration API service.
 *
 * Handles all API calls for ingest configuration.
 * Follows SRP by handling only API communication.
 * Follows SOC by separating API concerns from state management.
 */

export interface IngestConfig {
  ingest_dir: string;
  enabled: boolean;
  metadata_providers: string[] | null;
  metadata_merge_strategy: string;
  metadata_priority_order: string[] | null;
  supported_formats: string[] | null;
  ignore_patterns: string[] | null;
  retry_max_attempts: number;
  retry_backoff_seconds: number;
  process_timeout_seconds: number;
  auto_delete_after_ingest: boolean;
  created_at: string;
  updated_at: string;
}

export interface IngestConfigUpdate {
  ingest_dir?: string | null;
  enabled?: boolean | null;
  metadata_providers?: string[] | null;
  metadata_merge_strategy?: string | null;
  metadata_priority_order?: string[] | null;
  supported_formats?: string[] | null;
  ignore_patterns?: string[] | null;
  retry_max_attempts?: number | null;
  retry_backoff_seconds?: number | null;
  process_timeout_seconds?: number | null;
  auto_delete_after_ingest?: boolean | null;
}

const CONFIG_API_BASE = "/api/ingest/config";

/**
 * Get ingest configuration.
 *
 * Returns
 * -------
 * Promise<IngestConfig>
 *     Configuration.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function getIngestConfig(): Promise<IngestConfig> {
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

  return (await response.json()) as IngestConfig;
}

/**
 * Update ingest configuration.
 *
 * Parameters
 * ----------
 * config : IngestConfigUpdate
 *     Configuration updates.
 *
 * Returns
 * -------
 * Promise<IngestConfig>
 *     Updated configuration.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function updateIngestConfig(
  config: IngestConfigUpdate,
): Promise<IngestConfig> {
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

  return (await response.json()) as IngestConfig;
}
