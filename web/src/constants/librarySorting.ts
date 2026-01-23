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
 * Library sorting constants.
 *
 * Single source of truth for sort fields, sort orders, and their UI labels.
 * This module is intentionally UI-framework agnostic so it can be used by:
 * - the library UI (`SortPanel`, `SortByDropdown`)
 * - the profile configuration UI (`DefaultSortFieldConfiguration`)
 * - state hooks (`useLibrarySorting`)
 */

export const SORT_FIELDS = [
  "title",
  "author_sort",
  "timestamp",
  "pubdate",
  "series_index",
] as const;

export type SortField = (typeof SORT_FIELDS)[number];

export const DEFAULT_SORT_FIELD: SortField = "timestamp";

export const SORT_ORDERS = ["asc", "desc"] as const;

export type SortOrder = (typeof SORT_ORDERS)[number];

export const DEFAULT_SORT_ORDER: SortOrder = "desc";

export const SORT_OPTIONS = [
  { label: "Title", value: "title" },
  { label: "Author", value: "author_sort" },
  { label: "Added date", value: "timestamp" },
  { label: "Modified date", value: "pubdate" },
  { label: "Size", value: "series_index" },
] as const satisfies ReadonlyArray<{ label: string; value: SortField }>;

export const SORT_ORDER_OPTIONS = [
  { value: "asc", label: "Ascending" },
  { value: "desc", label: "Descending" },
] as const satisfies ReadonlyArray<{ value: SortOrder; label: string }>;
