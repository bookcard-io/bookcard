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
 * Email server configuration API service.
 *
 * Handles all API calls for email server configuration.
 * Follows SRP by handling only API communication.
 * Follows SOC by separating API concerns from state management.
 */

export interface EmailServerConfigData {
  id: number | null;
  has_smtp_password: boolean;
  server_type: "smtp" | "gmail";
  smtp_host: string | null;
  smtp_port: number | null;
  smtp_username: string | null;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
  smtp_from_email: string | null;
  smtp_from_name: string | null;
  max_email_size_mb: number;
  gmail_token: Record<string, unknown> | null;
  enabled: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface EmailServerConfigUpdate {
  server_type?: "smtp" | "gmail";
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_username?: string | null;
  smtp_password?: string;
  smtp_use_tls?: boolean;
  smtp_use_ssl?: boolean;
  smtp_from_email?: string | null;
  smtp_from_name?: string | null;
  max_email_size_mb?: number;
  gmail_token?: Record<string, unknown> | null;
  enabled?: boolean;
}

const API_BASE = "/api/auth/email-server-config";

/**
 * Fetch the current email server configuration.
 *
 * Returns
 * -------
 * Promise<EmailServerConfigData>
 *     Current email server configuration.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function fetchEmailServerConfig(): Promise<EmailServerConfigData> {
  const response = await fetch(API_BASE, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to fetch email server config" }));
    throw new Error(error.detail || "Failed to fetch email server config");
  }

  return response.json();
}

/**
 * Update the email server configuration.
 *
 * Parameters
 * ----------
 * data : EmailServerConfigUpdate
 *     Configuration update data.
 *
 * Returns
 * -------
 * Promise<EmailServerConfigData>
 *     Updated email server configuration.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function updateEmailServerConfig(
  data: EmailServerConfigUpdate,
): Promise<EmailServerConfigData> {
  const response = await fetch(API_BASE, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update email server config" }));
    throw new Error(error.detail || "Failed to update email server config");
  }

  return response.json();
}
