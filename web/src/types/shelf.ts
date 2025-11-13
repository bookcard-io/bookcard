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
 * TypeScript types for shelf-related data structures.
 *
 * These types match the backend API schemas defined in fundamental/api/schemas/shelves.py
 */

export interface Shelf {
  /** Shelf primary key. */
  id: number;
  /** Unique identifier for external references. */
  uuid: string;
  /** Shelf name. */
  name: string;
  /** Optional description of the shelf. */
  description: string | null;
  /** Path to cover picture file (relative to data_directory). */
  cover_picture: string | null;
  /** Whether the shelf is shared with everyone. */
  is_public: boolean;
  /** Whether the shelf is active (mirrors library's active status). */
  is_active: boolean;
  /** Owner user ID. */
  user_id: number;
  /** Library ID the shelf belongs to. */
  library_id: number;
  /** Shelf creation timestamp. */
  created_at: string;
  /** Last update timestamp. */
  updated_at: string;
  /** Last time books were added/removed/reordered. */
  last_modified: string;
  /** Number of books in the shelf. */
  book_count: number;
}

export interface ShelfCreate {
  /** Shelf name (must be unique per user for private, globally for public). */
  name: string;
  /** Optional description of the shelf. */
  description?: string | null;
  /** Whether the shelf is shared with everyone. */
  is_public: boolean;
}

export interface ShelfUpdate {
  /** New shelf name (optional). */
  name?: string | null;
  /** New description (optional). */
  description?: string | null;
  /** New public status (optional). */
  is_public?: boolean | null;
}

export interface ShelfListResponse {
  /** List of shelves. */
  shelves: Shelf[];
  /** Total number of shelves. */
  total: number;
}

export interface BookShelfLink {
  /** Calibre book ID. */
  book_id: number;
  /** Display order within the shelf. */
  order: number;
  /** Timestamp when book was added to shelf. */
  date_added: string;
}

export interface ShelfReorderRequest {
  /** Mapping of book_id to new order value. */
  book_orders: Record<number, number>;
}

export interface ShelfBooksResponse {
  /** List of book IDs in order. */
  book_ids: number[];
  /** Total number of books in the shelf. */
  total: number;
  /** Current page number. */
  page: number;
  /** Number of items per page. */
  page_size: number;
  /** Sort field used. */
  sort_by: string;
  /** Sort order used ('asc' or 'desc'). */
  sort_order: string;
}
