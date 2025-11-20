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
 * OpenLibrary data dump settings API service.
 *
 * Handles all API calls for OpenLibrary data dump configuration.
 * Follows SRP by handling only API communication.
 * Follows SOC by separating API concerns from state management.
 */

export interface OpenLibraryDumpConfig {
  /** URL for the authors dump file. */
  authors_url: string | null;
  /** URL for the works dump file. */
  works_url: string | null;
}

export interface DownloadFilesRequest {
  urls: string[];
}

export interface DownloadFilesResponse {
  message: string;
  task_id: number;
  downloaded_files: string[];
  failed_files: string[];
}

export interface IngestFilesResponse {
  message: string;
  task_id: number;
}

// Default URLs from Open Library dumps page
const DEFAULT_AUTHORS_URL =
  "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz";
const DEFAULT_WORKS_URL =
  "https://openlibrary.org/data/ol_dump_works_latest.txt.gz";

const DOWNLOAD_API_BASE = "/api/admin/openlibrary/download-dumps";
const INGEST_API_BASE = "/api/admin/openlibrary/ingest-dumps";

/**
 * Get default URLs for OpenLibrary dumps.
 *
 * Returns
 * -------
 * OpenLibraryDumpConfig
 *     Default configuration with URLs.
 */
export function getDefaultDumpUrls(): OpenLibraryDumpConfig {
  return {
    authors_url: DEFAULT_AUTHORS_URL,
    works_url: DEFAULT_WORKS_URL,
  };
}

/**
 * Download OpenLibrary dump files from URLs.
 *
 * Parameters
 * ----------
 * urls : string[]
 *     Array of file URLs to download.
 *
 * Returns
 * -------
 * Promise<DownloadFilesResponse>
 *     Response with download results.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function downloadOpenLibraryDumps(
  urls: string[],
): Promise<DownloadFilesResponse> {
  const response = await fetch(DOWNLOAD_API_BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ urls }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to download files" }));
    throw new Error(error.detail || "Failed to download files");
  }

  return response.json();
}

/**
 * Ingest OpenLibrary dump files into local database.
 *
 * Creates a background task that processes downloaded dump files
 * and ingests them into a local SQLite database for fast lookups.
 *
 * Returns
 * -------
 * Promise<IngestFilesResponse>
 *     Response with ingest task results.
 *
 * Throws
 * ------
 * Error
 *     If the request fails.
 */
export async function ingestOpenLibraryDumps(): Promise<IngestFilesResponse> {
  const response = await fetch(INGEST_API_BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to ingest files" }));
    throw new Error(error.detail || "Failed to ingest files");
  }

  return response.json();
}
