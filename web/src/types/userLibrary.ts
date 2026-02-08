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
 * TypeScript types for user-library association data structures.
 *
 * These types match the backend API schemas defined in
 * bookcard/api/schemas/user_libraries.py
 */

export interface UserLibrary {
  /** Association ID. */
  id: number;
  /** User ID. */
  user_id: number;
  /** Library ID. */
  library_id: number;
  /** Whether the library is visible in book listings. */
  is_visible: boolean;
  /** Whether this is the user's active library for ingestion. */
  is_active: boolean;
  /** Name of the associated library. */
  library_name: string | null;
  /** Timestamp when the association was created. */
  created_at: string;
  /** Timestamp when the association was last updated. */
  updated_at: string;
}
