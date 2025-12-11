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

export interface PluginInfo {
  name: string;
  version: string;
  description: string;
  author: string;
}

export interface PluginInstallRequest {
  repo_url: string;
  plugin_path?: string;
  branch?: string;
}

export interface PluginListResult {
  plugins: PluginInfo[];
  calibreNotFound: boolean;
  statusMessage?: string;
  statusType?: "warning" | "error" | "success" | "info" | "neutral";
}

const API_BASE = "/api/plugins";

/**
 * List all installed plugins.
 *
 * Returns
 * -------
 * Promise<PluginListResult>
 *     Result containing plugins list and calibre_not_found flag.
 *
 * Throws
 * ------
 * Error
 *     If the request fails for reasons other than calibre_not_found.
 */
export async function listPlugins(
  signal?: AbortSignal,
): Promise<PluginListResult> {
  const response = await fetch(`${API_BASE}`, {
    method: "GET",
    credentials: "include",
    signal,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to list plugins" }));

    // Handle calibre_not_found gracefully without throwing
    // This prevents Next.js from logging it as an unhandled error
    if (error.detail?.error_type === "calibre_not_found") {
      return {
        plugins: [],
        calibreNotFound: true,
        statusMessage: error.detail?.message,
        statusType:
          (error.detail?.message_type as
            | "warning"
            | "error"
            | "success"
            | "info"
            | "neutral"
            | undefined) || "neutral",
      };
    }

    const errorMessage =
      typeof error.detail === "string"
        ? error.detail
        : error.detail?.message || "Failed to list plugins";
    throw new Error(errorMessage);
  }

  return {
    plugins: await response.json(),
    calibreNotFound: false,
  };
}

/**
 * Install a plugin from an uploaded ZIP file.
 *
 * Parameters
 * ----------
 * file : File
 *     Plugin ZIP file to install.
 */
export async function installPluginUpload(file: File): Promise<void> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to install plugin" }));
    const errorMessage =
      typeof error.detail === "string"
        ? error.detail
        : error.detail?.message || "Failed to install plugin";
    const errorObj = new Error(errorMessage);
    if (error.detail?.error_type) {
      (
        errorObj as Error & { errorType?: string; messageType?: string }
      ).errorType = error.detail.error_type;
      (
        errorObj as Error & { errorType?: string; messageType?: string }
      ).messageType = error.detail.message_type;
    }
    throw errorObj;
  }
}

/**
 * Install a plugin from a Git repository.
 *
 * Parameters
 * ----------
 * request : PluginInstallRequest
 *     Git repository installation request.
 */
export async function installPluginGit(
  request: PluginInstallRequest,
): Promise<void> {
  const response = await fetch(`${API_BASE}/git`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to install plugin from Git" }));
    const errorMessage =
      typeof error.detail === "string"
        ? error.detail
        : error.detail?.message || "Failed to install plugin from Git";
    const errorObj = new Error(errorMessage);
    if (error.detail?.error_type) {
      (
        errorObj as Error & { errorType?: string; messageType?: string }
      ).errorType = error.detail.error_type;
      (
        errorObj as Error & { errorType?: string; messageType?: string }
      ).messageType = error.detail.message_type;
    }
    throw errorObj;
  }
}

/**
 * Remove an installed plugin.
 *
 * Parameters
 * ----------
 * pluginName : string
 *     Name of the plugin to remove.
 */
export async function removePlugin(pluginName: string): Promise<void> {
  const response = await fetch(
    `${API_BASE}/${encodeURIComponent(pluginName)}`,
    {
      method: "DELETE",
      credentials: "include",
    },
  );

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to remove plugin" }));
    throw new Error(error.detail || "Failed to remove plugin");
  }
}

/**
 * Sync DeDRM configuration with device serial numbers.
 *
 * Returns
 * -------
 * Promise<{ message: string }>
 *     Success message.
 */
export async function syncDeDRM(): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE}/dedrm/sync`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to sync DeDRM" }));
    throw new Error(error.detail || "Failed to sync DeDRM");
  }

  return response.json();
}
