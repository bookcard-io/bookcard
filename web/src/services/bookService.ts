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
 * Service for interacting with book API endpoints.
 *
 * Provides methods for sending books to e-reader devices.
 */

/**
 * Send a book via email.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID to send.
 * options : SendBookOptions | undefined
 *     Optional send options including email and file format.
 *     If email is not provided, sends to user's default device.
 *
 * Returns
 * -------
 * Promise<void>
 *     Success response.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails.
 */
export interface SendBookOptions {
  /** Email address to send to. If not provided, sends to default device. */
  toEmail?: string;
  /** Optional file format to send (e.g., 'EPUB', 'MOBI'). */
  fileFormat?: string;
}

export async function sendBookToDevice(
  bookId: number,
  options?: SendBookOptions,
): Promise<void> {
  const response = await fetch(`/api/books/${bookId}/send`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      to_email: options?.toEmail || null,
      file_format: options?.fileFormat || null,
    }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to send book" }));
    throw new Error(error.detail || "Failed to send book");
  }
}
