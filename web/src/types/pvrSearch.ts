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

export interface PVRSearchRequest {
  tracked_book_id: number;
  indexer_ids?: number[];
  max_results_per_indexer?: number;
}

export interface PVRSearchResponse {
  tracked_book_id: number;
  search_initiated: boolean;
  message: string;
}

export interface ReleaseInfoRead {
  indexer_id?: number;
  title: string;
  download_url: string;
  size_bytes?: number;
  publish_date?: string;
  seeders?: number;
  leechers?: number;
  quality?: string;
  author?: string;
  isbn?: string;
  description?: string;
  category?: string;
  additional_info?: Record<string, string | number | null>;
  warning?: string;
}

export interface SearchResultRead {
  release: ReleaseInfoRead;
  score: number;
  indexer_name?: string;
  indexer_priority: number;
  indexer_protocol?: string;
}

export interface PVRSearchResultsResponse {
  tracked_book_id: number;
  results: SearchResultRead[];
  total: number;
}

export interface PVRDownloadRequest {
  release_index: number;
  download_client_id?: number;
}

export interface PVRDownloadResponse {
  tracked_book_id: number;
  download_item_id: number;
  release_title: string;
  message: string;
}
