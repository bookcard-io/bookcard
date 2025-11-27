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
 * Provides methods for sending books to e-reader devices and updating book metadata.
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

/**
 * Send multiple books via email.
 *
 * Sends all books in a single API call. The backend will create
 * a background task for each book and enqueue them.
 *
 * Parameters
 * ----------
 * bookIds : number[]
 *     List of book IDs to send.
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
export async function sendBooksToDeviceBatch(
  bookIds: number[],
  options?: SendBookOptions,
): Promise<void> {
  if (bookIds.length === 0) {
    return;
  }

  const response = await fetch("/api/books/send/batch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      book_ids: bookIds,
      to_email: options?.toEmail || null,
      file_format: options?.fileFormat || null,
    }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to send books" }));
    throw new Error(error.detail || "Failed to send books");
  }
}

/**
 * Update a book's rating.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID to update.
 * rating : number | null
 *     Rating value (0-5) or null to remove rating.
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
export async function updateBookRating(
  bookId: number,
  rating: number | null,
): Promise<void> {
  const response = await fetch(`/api/books/${bookId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      rating_value: rating,
    }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update rating" }));
    throw new Error(error.detail || "Failed to update rating");
  }
}

/**
 * Convert a book format.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID to convert.
 * sourceFormat : string
 *     Source format (e.g., 'MOBI', 'AZW3').
 * targetFormat : string
 *     Target format (e.g., 'EPUB', 'KEPUB').
 *
 * Returns
 * -------
 * Promise<BookConvertResponse>
 *     Response containing task ID and optional message.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails.
 */
export interface BookConvertResponse {
  task_id: number;
  message?: string | null;
  existing_conversion_id?: number | null;
}

export async function convertBookFormat(
  bookId: number,
  sourceFormat: string,
  targetFormat: string,
): Promise<BookConvertResponse> {
  const response = await fetch(`/api/books/${bookId}/convert`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      source_format: sourceFormat,
      target_format: targetFormat,
    }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to convert book" }));
    throw new Error(error.detail || "Failed to convert book");
  }

  return response.json();
}

/**
 * Get conversion history for a book.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID.
 * page : number
 *     Page number (1-indexed).
 * pageSize : number
 *     Number of items per page.
 *
 * Returns
 * -------
 * Promise<BookConversionListResponse>
 *     Paginated list of conversion records.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails.
 */
export interface BookConversionRead {
  id: number;
  book_id: number;
  original_format: string;
  target_format: string;
  conversion_method: string;
  status: string;
  error_message: string | null;
  original_backed_up: boolean;
  created_at: string;
  completed_at: string | null;
  duration: number | null;
}

export interface BookConversionListResponse {
  items: BookConversionRead[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export async function getBookConversions(
  bookId: number,
  page: number = 1,
  pageSize: number = 20,
): Promise<BookConversionListResponse> {
  const response = await fetch(
    `/api/books/${bookId}/conversions?page=${page}&page_size=${pageSize}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
    },
  );

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to get conversion history" }));
    throw new Error(error.detail || "Failed to get conversion history");
  }

  return response.json();
}
