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
 * Settings API service.
 *
 * Handles all API calls for user settings.
 * Follows SRP by handling only API communication.
 * Follows SOC by separating API concerns from state management.
 */

export interface Setting {
  key: string;
  value: string;
  description?: string | null;
  updated_at: string;
}

export interface SettingsResponse {
  settings: Record<string, Setting>;
}

/**
 * Fetch all user settings from the backend.
 *
 * Returns
 * -------
 * SettingsResponse
 *     All user settings keyed by setting key.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails.
 */
export async function fetchSettings(): Promise<SettingsResponse> {
  const response = await fetch("/api/auth/settings", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to fetch settings");
  }

  return (await response.json()) as SettingsResponse;
}

/**
 * Save a single setting to the backend.
 *
 * Parameters
 * ----------
 * key : string
 *     Setting key.
 * value : string
 *     Setting value.
 *
 * Returns
 * -------
 * Setting
 *     Saved setting entity.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails.
 */
export async function saveSetting(
  key: string,
  value: string,
): Promise<Setting> {
  const response = await fetch(
    `/api/auth/settings/${encodeURIComponent(key)}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ value }),
      credentials: "include",
    },
  );

  if (!response.ok) {
    const errorData = (await response.json()) as { detail?: string };
    throw new Error(errorData.detail || `Failed to save setting ${key}`);
  }

  return (await response.json()) as Setting;
}
