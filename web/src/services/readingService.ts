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
 * Service for interacting with reading API endpoints.
 *
 * Provides methods for managing reading progress, sessions, and status.
 */

import { AUTH_COOKIE_NAME } from "@/constants/config";
import type {
  ReadingHistoryResponse,
  ReadingProgress,
  ReadingProgressCreate,
  ReadingSession,
  ReadingSessionCreate,
  ReadingSessionsListResponse,
  ReadStatus,
  RecentReadsResponse,
} from "@/types/reading";

const API_BASE = "/api/reading";

const localProgressKey = (bookId: number, format: string) =>
  `reading-progress:${bookId}:${format.toLowerCase()}`;

const hasAuthCookie = () =>
  typeof document !== "undefined" &&
  document.cookie.includes(`${AUTH_COOKIE_NAME}=`);

const buildLocalProgress = (
  data: ReadingProgressCreate,
  updatedAt: string,
): ReadingProgress => ({
  id: -1,
  user_id: 0,
  library_id: 0,
  book_id: data.book_id,
  format: data.format,
  progress: data.progress,
  cfi: data.cfi ?? null,
  page_number: data.page_number ?? null,
  device: data.device ?? null,
  spread_mode: data.spread_mode ?? null,
  reading_direction: data.reading_direction ?? null,
  updated_at: updatedAt,
});

/**
 * Update reading progress for a book.
 *
 * Parameters
 * ----------
 * data : ReadingProgressCreate
 *     Progress update data.
 *
 * Returns
 * -------
 * Promise<ReadingProgress>
 *     Updated reading progress.
 */
export async function updateProgress(
  data: ReadingProgressCreate,
): Promise<ReadingProgress> {
  if (!hasAuthCookie() && typeof window !== "undefined") {
    const updatedAt = new Date().toISOString();
    const progress = buildLocalProgress(data, updatedAt);
    window.localStorage.setItem(
      localProgressKey(data.book_id, data.format),
      JSON.stringify(progress),
    );
    return progress;
  }

  const response = await fetch(`${API_BASE}/progress`, {
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
      .catch(() => ({ detail: "Failed to update reading progress" }));
    throw new Error(error.detail || "Failed to update reading progress");
  }

  return response.json();
}

/**
 * Get reading progress for a book.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID.
 * format : string
 *     Book format (EPUB, PDF, etc.).
 *
 * Returns
 * -------
 * Promise<ReadingProgress>
 *     Reading progress data.
 */
export async function getProgress(
  bookId: number,
  format: string,
): Promise<ReadingProgress | null> {
  if (!hasAuthCookie() && typeof window !== "undefined") {
    const cached = window.localStorage.getItem(
      localProgressKey(bookId, format),
    );
    if (!cached) {
      return null;
    }
    try {
      return JSON.parse(cached) as ReadingProgress;
    } catch {
      return null;
    }
  }

  const params = new URLSearchParams({
    book_id: bookId.toString(),
    format,
  });

  const response = await fetch(`${API_BASE}/progress?${params}`, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    // 404 is expected when there's no progress yet
    if (response.status === 404) {
      return null;
    }
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to get reading progress" }));
    throw new Error(error.detail || "Failed to get reading progress");
  }

  return response.json();
}

/**
 * Start a reading session.
 *
 * Parameters
 * ----------
 * data : ReadingSessionCreate
 *     Session creation data.
 *
 * Returns
 * -------
 * Promise<ReadingSession>
 *     Created reading session.
 */
export async function startSession(
  data: ReadingSessionCreate,
): Promise<ReadingSession> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to start reading session" }));
    throw new Error(error.detail || "Failed to start reading session");
  }

  return response.json();
}

/**
 * End a reading session.
 *
 * Parameters
 * ----------
 * sessionId : number
 *     Session ID.
 * progressEnd : number
 *     Final reading progress (0.0 to 1.0).
 *
 * Returns
 * -------
 * Promise<ReadingSession>
 *     Updated reading session.
 */
export async function endSession(
  sessionId: number,
  progressEnd: number,
): Promise<ReadingSession> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ progress_end: progressEnd }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to end reading session" }));
    throw new Error(error.detail || "Failed to end reading session");
  }

  return response.json();
}

/**
 * List reading sessions.
 *
 * Parameters
 * ----------
 * bookId : number | undefined
 *     Filter by book ID (optional).
 * page : number
 *     Page number (default: 1).
 * pageSize : number
 *     Items per page (default: 50).
 *
 * Returns
 * -------
 * Promise<ReadingSessionsListResponse>
 *     List of reading sessions with pagination.
 */
export async function listSessions(
  bookId?: number,
  page: number = 1,
  pageSize: number = 50,
): Promise<ReadingSessionsListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (bookId !== undefined) {
    params.append("book_id", bookId.toString());
  }

  const response = await fetch(`${API_BASE}/sessions?${params}`, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to list reading sessions" }));
    throw new Error(error.detail || "Failed to list reading sessions");
  }

  return response.json();
}

/**
 * Get recent reads.
 *
 * Parameters
 * ----------
 * limit : number
 *     Maximum number of recent reads (default: 10).
 *
 * Returns
 * -------
 * Promise<RecentReadsResponse>
 *     List of recent reads.
 */
export async function getRecentReads(
  limit: number = 10,
): Promise<RecentReadsResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
  });

  const response = await fetch(`${API_BASE}/recent?${params}`, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to get recent reads" }));
    throw new Error(error.detail || "Failed to get recent reads");
  }

  return response.json();
}

/**
 * Get reading history for a book.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID.
 * limit : number
 *     Maximum number of sessions (default: 50).
 *
 * Returns
 * -------
 * Promise<ReadingHistoryResponse>
 *     Reading history for the book.
 */
export async function getReadingHistory(
  bookId: number,
  limit: number = 50,
): Promise<ReadingHistoryResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
  });

  const response = await fetch(`${API_BASE}/history/${bookId}?${params}`, {
    method: "GET",
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to get reading history" }));
    throw new Error(error.detail || "Failed to get reading history");
  }

  return response.json();
}

/**
 * Get read status for a book.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID.
 *
 * Returns
 * -------
 * Promise<ReadStatus | null>
 *     Read status data, or null if the book has not been read (404).
 */
export async function getReadStatus(
  bookId: number,
): Promise<ReadStatus | null> {
  const response = await fetch(`${API_BASE}/status/${bookId}`, {
    method: "GET",
    credentials: "include",
  });

  if (response.status === 404) {
    // 404 means the book hasn't been read yet, which is a valid state
    return null;
  }

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to get read status" }));
    throw new Error(error.detail || "Failed to get read status");
  }

  return response.json();
}

/**
 * Update read status for a book.
 *
 * Parameters
 * ----------
 * bookId : number
 *     Book ID.
 * status : 'read' | 'not_read'
 *     New read status.
 *
 * Returns
 * -------
 * Promise<ReadStatus>
 *     Updated read status.
 */
export async function updateReadStatus(
  bookId: number,
  status: "read" | "not_read",
): Promise<ReadStatus> {
  const response = await fetch(`${API_BASE}/status/${bookId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update read status" }));
    throw new Error(error.detail || "Failed to update read status");
  }

  return response.json();
}
