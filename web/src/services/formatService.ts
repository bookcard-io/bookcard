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
 * Service for book format operations.
 *
 * Provides methods for uploading and managing book file formats.
 * Follows SRP by separating data layer from business logic.
 * Follows IOC by allowing dependency injection for testing.
 */

/**
 * Result of a format upload operation.
 */
export interface FormatUploadResult {
  /** Upload status. */
  status: "success" | "conflict";
}

/**
 * Upload a book format file.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID to upload format for.
 * file : File
 *     File to upload.
 * replace : boolean
 *     Whether to replace existing format (default: false).
 *
 * Returns
 * -------
 * Promise<FormatUploadResult>
 *     Upload result with status.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails (non-409 errors).
 */
export async function uploadFormat(
  bookId: number,
  file: File,
  replace: boolean = false,
): Promise<FormatUploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const url = new URL(`/api/books/${bookId}/formats`, window.location.origin);
  if (replace) {
    url.searchParams.set("replace", "true");
  }

  const response = await fetch(url.toString(), {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (response.status === 409) {
    return { status: "conflict" };
  }

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to upload format" }));
    throw new Error(error.detail || "Failed to upload format");
  }

  return { status: "success" };
}
