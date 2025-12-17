// Copyright (C) 2025 khoa and others
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
 * Type definitions for reading-related API responses and requests.
 *
 * These types correspond to the Pydantic schemas defined in
 * bookcard/api/schemas/reading.py.
 */

/**
 * Request schema for creating/updating reading progress.
 */
export interface ReadingProgressCreate {
  /** Book ID. */
  book_id: number;
  /** Book format (EPUB, PDF, etc.). */
  format: string;
  /** Reading progress as percentage (0.0 to 1.0). */
  progress: number;
  /** Canonical Fragment Identifier for EPUB (optional). */
  cfi?: string | null;
  /** Page number for PDF or comic formats (optional). */
  page_number?: number | null;
  /** Device identifier (optional). */
  device?: string | null;
  /** Whether reading in spread mode for comics (optional). */
  spread_mode?: boolean | null;
  /** Reading direction for comics: 'ltr', 'rtl', or 'vertical' (optional). */
  reading_direction?: string | null;
}

/**
 * Response schema for reading progress data.
 */
export interface ReadingProgress {
  /** Progress primary key. */
  id: number;
  /** User ID. */
  user_id: number;
  /** Library ID. */
  library_id: number;
  /** Book ID. */
  book_id: number;
  /** Book format. */
  format: string;
  /** Reading progress (0.0 to 1.0). */
  progress: number;
  /** CFI for EPUB. */
  cfi?: string | null;
  /** Page number for PDF or comic formats. */
  page_number?: number | null;
  /** Device identifier. */
  device?: string | null;
  /** Whether reading in spread mode for comics. */
  spread_mode?: boolean | null;
  /** Reading direction for comics: 'ltr', 'rtl', or 'vertical'. */
  reading_direction?: string | null;
  /** Last update timestamp. */
  updated_at: string;
}

/**
 * Request schema for starting a reading session.
 */
export interface ReadingSessionCreate {
  /** Book ID. */
  book_id: number;
  /** Book format (EPUB, PDF, etc.). */
  format: string;
  /** Device identifier (optional). */
  device?: string | null;
}

/**
 * Response schema for reading session data.
 */
export interface ReadingSession {
  /** Session primary key. */
  id: number;
  /** User ID. */
  user_id: number;
  /** Library ID. */
  library_id: number;
  /** Book ID. */
  book_id: number;
  /** Book format. */
  format: string;
  /** Session start timestamp. */
  started_at: string;
  /** Session end timestamp (null if ongoing). */
  ended_at?: string | null;
  /** Progress at session start. */
  progress_start: number;
  /** Progress at session end (null if ongoing). */
  progress_end?: number | null;
  /** Device identifier. */
  device?: string | null;
  /** Record creation timestamp. */
  created_at: string;
  /** Session duration in seconds (null if ongoing). */
  duration?: number | null;
}

/**
 * Read status values.
 */
export type ReadStatusValue = "not_read" | "reading" | "read";

/**
 * Response schema for read status data.
 */
export interface ReadStatus {
  /** Status primary key. */
  id: number;
  /** User ID. */
  user_id: number;
  /** Library ID. */
  library_id: number;
  /** Book ID. */
  book_id: number;
  /** Current read status (not_read, reading, read). */
  status: ReadStatusValue;
  /** Timestamp when book was first opened. */
  first_opened_at?: string | null;
  /** Timestamp when book was marked as read. */
  marked_as_read_at?: string | null;
  /** Whether book was automatically marked as read. */
  auto_marked: boolean;
  /** Progress percentage when marked as read. */
  progress_when_marked?: number | null;
  /** Record creation timestamp. */
  created_at: string;
  /** Last update timestamp. */
  updated_at: string;
}

/**
 * Response schema for recent reads list.
 */
export interface RecentReadsResponse {
  /** List of recent reading progress records. */
  reads: ReadingProgress[];
  /** Total number of recent reads. */
  total: number;
}

/**
 * Response schema for reading history.
 */
export interface ReadingHistoryResponse {
  /** List of reading sessions. */
  sessions: ReadingSession[];
  /** Total number of sessions. */
  total: number;
}

/**
 * Response schema for listing reading sessions.
 */
export interface ReadingSessionsListResponse {
  /** List of reading sessions. */
  sessions: ReadingSession[];
  /** Total number of sessions. */
  total: number;
  /** Current page number. */
  page: number;
  /** Number of items per page. */
  page_size: number;
}
