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

import type {
  PVRDownloadRequest,
  PVRDownloadResponse,
  PVRSearchRequest,
  PVRSearchResponse,
  PVRSearchResultsResponse,
} from "@/types/pvrSearch";

const BASE_URL = "/api/pvr/search";

export const pvrSearchService = {
  search: async (request: PVRSearchRequest): Promise<PVRSearchResponse> => {
    const response = await fetch(BASE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Search failed" }));
      throw new Error(error.detail || "Failed to initiate search");
    }
    return response.json();
  },

  getResults: async (
    trackedBookId: number,
  ): Promise<PVRSearchResultsResponse> => {
    const response = await fetch(`${BASE_URL}/${trackedBookId}/results`);
    if (!response.ok) {
      if (response.status === 404) {
        // It might mean no results yet or not found.
        const error = await response
          .json()
          .catch(() => ({ detail: "No results" }));
        throw new Error(error.detail || "Failed to get results");
      }
      throw new Error("Failed to get search results");
    }
    return response.json();
  },

  download: async (
    trackedBookId: number,
    request: PVRDownloadRequest,
  ): Promise<PVRDownloadResponse> => {
    const response = await fetch(`${BASE_URL}/${trackedBookId}/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Download failed" }));
      throw new Error(error.detail || "Failed to initiate download");
    }
    return response.json();
  },
};
