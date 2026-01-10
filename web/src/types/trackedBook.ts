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

export interface BookFile {
  name: string;
  format: string;
  size: number;
  path: string;
}

export interface TrackedBook {
  id: number;
  title: string;
  author: string;
  status:
    | "wanted"
    | "searching"
    | "downloading"
    | "paused"
    | "stalled"
    | "seeding"
    | "completed"
    | "failed"
    | "ignored";
  library_id?: number;
  cover_url?: string;
  created_at?: string;
  metadata_source_id?: string;
  metadata_external_id?: string;
  isbn?: string;
  description?: string;
  publisher?: string;
  published_date?: string;
  series_name?: string;
  series_index?: number;
  rating?: number;
  tags?: string[];
  auto_search_enabled?: boolean;
  auto_download_enabled?: boolean;
  preferred_formats?: string[];
  monitor_mode?: MonitorMode;
  exclude_keywords?: string[];
  require_keywords?: string[];
  require_title_match?: boolean;
  require_author_match?: boolean;
  require_isbn_match?: boolean;
  files?: BookFile[];
}

/**
 * Payload for updating a tracked book.
 *
 * Mirrors the backend `TrackedBookUpdate` schema (nullable fields allowed).
 */
export interface TrackedBookUpdate {
  title?: string;
  author?: string;
  isbn?: string | null;
  cover_url?: string | null;
  description?: string | null;
  publisher?: string | null;
  published_date?: string | null;
  rating?: number | null;
  tags?: string[] | null;
  series_name?: string | null;
  series_index?: number | null;
  status?: TrackedBook["status"];
  monitor_mode?: MonitorMode | null;
  auto_search_enabled?: boolean;
  auto_download_enabled?: boolean;
  preferred_formats?: string[] | null;
  exclude_keywords?: string[] | null;
  require_keywords?: string[] | null;
  require_title_match?: boolean;
  require_author_match?: boolean;
  require_isbn_match?: boolean;
  library_id?: number | null;
}

export enum MonitorMode {
  BOOK_ONLY = "book_only",
  SERIES = "series",
  AUTHOR = "author",
}

export interface MetadataSearchResult {
  id: string; // provider specific ID
  title: string;
  author: string;
  authors?: string[]; // Sometimes returned as array
  isbn?: string;
  identifiers?: { isbn?: string }; // Sometimes returned in identifiers object
  year?: string;
  publisher?: string;
  published_date?: string;
  cover_url?: string;
  description?: string;
  provider: string;
  source_id?: string; // specific to some providers
  external_id?: string; // specific to some providers
  score?: number;
  tags?: string[];
}
