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

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getOpenLibraryDumpConfig,
  type OpenLibraryDumpConfig,
  type OpenLibraryDumpConfigUpdate,
  updateOpenLibraryDumpConfig,
} from "./openLibraryConfigService";

/**
 * Creates a mock fetch response.
 *
 * Parameters
 * ----------
 * ok : boolean
 *     Response ok status.
 * jsonData : unknown
 *     JSON data to return.
 * jsonError : Error | null
 *     Optional error to throw from json().
 *
 * Returns
 * -------
 * Response
 *     Mock response object.
 */
function createMockResponse(
  ok: boolean,
  jsonData: unknown = {},
  jsonError: Error | null = null,
) {
  return {
    ok,
    json: jsonError
      ? vi.fn().mockRejectedValue(jsonError)
      : vi.fn().mockResolvedValue(jsonData),
  };
}

/**
 * Creates a mock OpenLibrary dump config data.
 *
 * Parameters
 * ----------
 * overrides : Partial<OpenLibraryDumpConfig>
 *     Optional overrides for default values.
 *
 * Returns
 * -------
 * OpenLibraryDumpConfig
 *     Mock OpenLibrary dump config data.
 */
function createMockConfig(
  overrides: Partial<OpenLibraryDumpConfig> = {},
): OpenLibraryDumpConfig {
  return {
    id: 1,
    authors_url: "https://example.com/authors.txt.gz",
    works_url: "https://example.com/works.txt.gz",
    editions_url: "https://example.com/editions.txt.gz",
    default_process_authors: true,
    default_process_works: true,
    default_process_editions: true,
    staleness_threshold_days: 30,
    enable_auto_download: false,
    enable_auto_process: false,
    auto_check_interval_hours: 24,
    updated_at: "2025-01-01T00:00:00Z",
    created_at: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("openLibraryConfigService", () => {
  const apiBase = "/api/admin/openlibrary-dump-config";
  const baseHeaders = {
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("getOpenLibraryDumpConfig", () => {
    it("should fetch OpenLibrary dump config successfully", async () => {
      const mockConfig = createMockConfig();
      const mockResponse = createMockResponse(true, mockConfig);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getOpenLibraryDumpConfig();

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "GET",
        headers: baseHeaders,
        credentials: "include",
      });
      expect(result).toEqual(mockConfig);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Unauthorized" },
        "Unauthorized",
      ],
      ["without detail in error response", {}, "Failed to fetch configuration"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to fetch configuration",
      ],
    ])(
      "should throw error when response is not ok %s",
      async (_desc, errorData, expectedMessage) => {
        const mockResponse = createMockResponse(false, errorData);
        (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
          mockResponse,
        );

        await expect(getOpenLibraryDumpConfig()).rejects.toThrow(
          expectedMessage,
        );
      },
    );

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getOpenLibraryDumpConfig()).rejects.toThrow("Invalid JSON");
    });
  });

  describe("updateOpenLibraryDumpConfig", () => {
    it("should update OpenLibrary dump config successfully", async () => {
      const updateData: OpenLibraryDumpConfigUpdate = {
        authors_url: "https://example.com/new-authors.txt.gz",
        enable_auto_download: true,
        staleness_threshold_days: 60,
      };
      const mockConfig = createMockConfig(updateData);
      const mockResponse = createMockResponse(true, mockConfig);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateOpenLibraryDumpConfig(updateData);

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "PUT",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(updateData),
      });
      expect(result).toEqual(mockConfig);
    });

    it("should update OpenLibrary dump config with null values", async () => {
      const updateData: OpenLibraryDumpConfigUpdate = {
        authors_url: null,
        works_url: null,
        editions_url: null,
      };
      const mockConfig = createMockConfig(updateData);
      const mockResponse = createMockResponse(true, mockConfig);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateOpenLibraryDumpConfig(updateData);

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "PUT",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(updateData),
      });
      expect(result).toEqual(mockConfig);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Validation error" },
        "Validation error",
      ],
      [
        "without detail in error response",
        {},
        "Failed to update configuration",
      ],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to update configuration",
      ],
    ])(
      "should throw error when response is not ok %s",
      async (_desc, errorData, expectedMessage) => {
        const updateData: OpenLibraryDumpConfigUpdate = {
          enable_auto_download: false,
        };
        const mockResponse = createMockResponse(false, errorData);
        (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
          mockResponse,
        );

        await expect(updateOpenLibraryDumpConfig(updateData)).rejects.toThrow(
          expectedMessage,
        );
      },
    );

    it("should throw error when JSON parsing fails", async () => {
      const updateData: OpenLibraryDumpConfigUpdate = {
        enable_auto_process: true,
      };
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateOpenLibraryDumpConfig(updateData)).rejects.toThrow(
        "Invalid JSON",
      );
    });
  });
});
