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
 * TypeScript types for book-related data structures.
 *
 * These types match the backend API schemas defined in bookcard/api/schemas.py
 */

import type { ReadStatusValue } from "@/types/reading";

export interface BookReadingSummary {
  /** Current read status (not_read, reading, read), or null when no status exists. */
  read_status: ReadStatusValue | null;
  /** Highest progress recorded for the book (0.0 to 1.0), across formats/devices. */
  max_progress: number | null;
  /** Timestamp when read status was last updated. */
  status_updated_at?: string | null;
  /** Timestamp when reading progress was last updated. */
  progress_updated_at?: string | null;
}

export interface Book {
  /** Calibre book ID. */
  id: number;
  /** Book title. */
  title: string;
  /** List of author names. */
  authors: string[];
  /** List of author IDs corresponding to authors. */
  author_ids?: number[];
  /** Sortable author name. */
  author_sort: string | null;
  /** Sortable title (with articles removed). */
  title_sort: string | null;
  /** Publication date. */
  pubdate: string | null;
  /** Date book was added to library. */
  timestamp: string | null;
  /** Series name if part of a series. */
  series: string | null;
  /** Series ID if part of a series. */
  series_id: number | null;
  /** Position in series. */
  series_index: number | null;
  /** ISBN identifier. */
  isbn: string | null;
  /** Unique identifier for the book. */
  uuid: string;
  /** URL to book cover thumbnail. */
  thumbnail_url: string | null;
  /** Whether the book has a cover image. */
  has_cover: boolean;
  /** List of tag names. */
  tags?: string[];
  /** List of tag IDs corresponding to tags. */
  tag_ids?: number[];
  /** List of identifiers, each with 'type' and 'val' keys. */
  identifiers?: Array<{ type: string; val: string }>;
  /** Book description/comment text. */
  description?: string | null;
  /** Publisher name. */
  publisher?: string | null;
  /** Publisher ID. */
  publisher_id?: number | null;
  /** List of language codes. */
  languages?: string[];
  /** List of language IDs. */
  language_ids?: number[];
  /** Rating value (0-5). */
  rating?: number | null;
  /** Rating ID. */
  rating_id?: number | null;
  /** List of file formats, each with 'format' and 'size' keys. */
  formats?: Array<{ format: string; size: number }>;
  /** Optional denormalized reading summary (status + max progress). */
  reading_summary?: BookReadingSummary | null;
  /** Tracking status for virtual books (e.g., 'wanted', 'downloading'). */
  tracking_status?: string | null;
  /** Whether this is a virtual book (tracked but not in library). */
  is_virtual?: boolean;
  /** ID of the tracked book record if this is a virtual book. */
  tracking_id?: number | null;
}

export interface BookUpdate {
  /** Book title to update. */
  title?: string | null;
  /** Publication date to update. */
  pubdate?: string | null;
  /** List of author names to set (replaces existing). */
  author_names?: string[] | null;
  /** Series name to set (creates if doesn't exist). */
  series_name?: string | null;
  /** Series ID to set (if provided, series_name is ignored). */
  series_id?: number | null;
  /** Series index to update. */
  series_index?: number | null;
  /** ISBN identifier to set (first-class field). */
  isbn?: string | null;
  /** List of tag names to set (replaces existing). */
  tag_names?: string[] | null;
  /** List of identifiers with 'type' and 'val' keys (replaces existing). */
  identifiers?: Array<{ type: string; val: string }> | null;
  /** Book description/comment to set. */
  description?: string | null;
  /** Publisher name to set (creates if doesn't exist). */
  publisher_name?: string | null;
  /** Publisher ID to set (if provided, publisher_name is ignored). */
  publisher_id?: number | null;
  /** List of language codes to set (creates if doesn't exist). */
  language_codes?: string[] | null;
  /** List of language IDs to set (if provided, language_codes is ignored). */
  language_ids?: number[] | null;
  /** Rating value to set (0-5). */
  rating_value?: number | null;
  /** Rating ID to set (if provided, rating_value is ignored). */
  rating_id?: number | null;
  /** Author sort value to set. */
  author_sort?: string | null;
  /** Title sort value to set. */
  title_sort?: string | null;
}

export interface BookListResponse {
  /** List of books for current page. */
  items: Book[];
  /** Total number of books matching the query. */
  total: number;
  /** Current page number (1-indexed). */
  page: number;
  /** Number of items per page. */
  page_size: number;
  /** Total number of pages. */
  total_pages: number;
}

export interface BooksQueryParams {
  /** Page number (1-indexed). */
  page?: number;
  /** Number of items per page. */
  page_size?: number;
  /** Search query to filter by title or author. */
  search?: string;
  /** Author ID to filter by. */
  author_id?: number;
  /** Field to sort by. */
  sort_by?:
    | "timestamp"
    | "pubdate"
    | "title"
    | "author_sort"
    | "series_index"
    | "random";
  pubdate_month?: number;
  pubdate_day?: number;
  /** Sort order. */
  sort_order?: "asc" | "desc";
}
