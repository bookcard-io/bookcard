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

import type { MetadataSearchResult, TrackedBook } from "@/types/trackedBook";

const BASE_URL = "/api/tracked-books";
const METADATA_SEARCH_URL = "/api/metadata/search";

export const trackedBookService = {
  getAll: async (): Promise<TrackedBook[]> => {
    const response = await fetch(BASE_URL);
    if (!response.ok) {
      // Fallback for demo if API not ready
      if (response.status === 404 || response.status === 500) {
        console.warn("API not ready, returning empty list");
        return [];
      }
      throw new Error("Failed to fetch tracked books");
    }
    const data = await response.json();
    return Array.isArray(data) ? data : data.items || [];
  },

  get: async (id: number | string): Promise<TrackedBook> => {
    const response = await fetch(`${BASE_URL}/${id}`);
    if (!response.ok) throw new Error("Failed to fetch tracked book");
    return response.json();
  },

  add: async (
    book: Partial<TrackedBook> | MetadataSearchResult,
  ): Promise<TrackedBook> => {
    const response = await fetch(BASE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(book),
    });
    if (!response.ok) throw new Error("Failed to add tracked book");
    return response.json();
  },

  update: async (
    id: number | string,
    book: Partial<TrackedBook>,
  ): Promise<TrackedBook> => {
    const response = await fetch(`${BASE_URL}/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(book),
    });
    if (!response.ok) throw new Error("Failed to update tracked book");
    return response.json();
  },

  delete: async (id: number | string): Promise<void> => {
    const response = await fetch(`${BASE_URL}/${id}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete tracked book");
  },

  searchMetadata: async (
    query: string,
    providers?: string[],
  ): Promise<MetadataSearchResult[]> => {
    let url = `${METADATA_SEARCH_URL}?query=${encodeURIComponent(query)}`;
    if (providers && providers.length > 0) {
      url += `&provider_ids=${encodeURIComponent(providers.join(","))}`;
    }
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to search metadata");
    const data = await response.json();
    return data; // Assuming API returns array of MetadataSearchResult
  },
};
