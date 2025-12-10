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
  type DownloadFilesResponse,
  downloadOpenLibraryDumps,
  getDefaultDumpUrls,
  type IngestFilesRequest,
  type IngestFilesResponse,
  ingestOpenLibraryDumps,
} from "./openLibrarySettingsService";

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

describe("openLibrarySettingsService", () => {
  const downloadApiBase = "/api/admin/openlibrary/download-dumps";
  const ingestApiBase = "/api/admin/openlibrary/ingest-dumps";
  const baseHeaders = {
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("getDefaultDumpUrls", () => {
    it("should return default dump URLs", () => {
      const result = getDefaultDumpUrls();

      expect(result).toEqual({
        authors_url:
          "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz",
        works_url: "https://openlibrary.org/data/ol_dump_works_latest.txt.gz",
        editions_url:
          "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz",
      });
    });
  });

  describe("downloadOpenLibraryDumps", () => {
    it("should download OpenLibrary dumps successfully", async () => {
      const urls = [
        "https://example.com/authors.txt.gz",
        "https://example.com/works.txt.gz",
      ];
      const mockResponse: DownloadFilesResponse = {
        message: "Download completed",
        task_id: 123,
        downloaded_files: urls,
        failed_files: [],
      };
      const mockFetchResponse = createMockResponse(true, mockResponse);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await downloadOpenLibraryDumps(urls);

      expect(globalThis.fetch).toHaveBeenCalledWith(downloadApiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify({ urls }),
      });
      expect(result).toEqual(mockResponse);
    });

    it("should handle download with some failed files", async () => {
      const [authorsUrl, worksUrl, editionsUrl] = [
        "https://example.com/authors.txt.gz",
        "https://example.com/works.txt.gz",
        "https://example.com/editions.txt.gz",
      ];
      const urls = [authorsUrl, worksUrl, editionsUrl];
      const mockResponse: DownloadFilesResponse = {
        message: "Partial download completed",
        task_id: 124,
        downloaded_files: [authorsUrl, worksUrl],
        failed_files: [editionsUrl],
      };
      const mockFetchResponse = createMockResponse(true, mockResponse);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await downloadOpenLibraryDumps(urls);

      expect(result).toEqual(mockResponse);
      expect(result.failed_files).toHaveLength(1);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Network error" },
        "Network error",
      ],
      ["without detail in error response", {}, "Failed to download files"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to download files",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const urls = ["https://example.com/authors.txt.gz"];
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(downloadOpenLibraryDumps(urls)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const urls = ["https://example.com/authors.txt.gz"];
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(downloadOpenLibraryDumps(urls)).rejects.toThrow(
        "Failed to download files",
      );
    });

    it("should handle empty URLs array", async () => {
      const urls: string[] = [];
      const mockResponse: DownloadFilesResponse = {
        message: "No files to download",
        task_id: 125,
        downloaded_files: [],
        failed_files: [],
      };
      const mockFetchResponse = createMockResponse(true, mockResponse);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await downloadOpenLibraryDumps(urls);

      expect(globalThis.fetch).toHaveBeenCalledWith(downloadApiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify({ urls }),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("ingestOpenLibraryDumps", () => {
    it("should ingest OpenLibrary dumps successfully with all options", async () => {
      const options: IngestFilesRequest = {
        process_authors: true,
        process_works: true,
        process_editions: true,
      };
      const mockResponse: IngestFilesResponse = {
        message: "Ingest task created",
        task_id: 456,
      };
      const mockFetchResponse = createMockResponse(true, mockResponse);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await ingestOpenLibraryDumps(options);

      expect(globalThis.fetch).toHaveBeenCalledWith(ingestApiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(options),
      });
      expect(result).toEqual(mockResponse);
    });

    it("should ingest OpenLibrary dumps successfully with partial options", async () => {
      const options: IngestFilesRequest = {
        process_authors: true,
        process_works: false,
      };
      const mockResponse: IngestFilesResponse = {
        message: "Ingest task created",
        task_id: 457,
      };
      const mockFetchResponse = createMockResponse(true, mockResponse);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await ingestOpenLibraryDumps(options);

      expect(globalThis.fetch).toHaveBeenCalledWith(ingestApiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(options),
      });
      expect(result).toEqual(mockResponse);
    });

    it("should ingest OpenLibrary dumps successfully with empty options", async () => {
      const options: IngestFilesRequest = {};
      const mockResponse: IngestFilesResponse = {
        message: "Ingest task created",
        task_id: 458,
      };
      const mockFetchResponse = createMockResponse(true, mockResponse);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await ingestOpenLibraryDumps(options);

      expect(globalThis.fetch).toHaveBeenCalledWith(ingestApiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(options),
      });
      expect(result).toEqual(mockResponse);
    });

    it("should ingest OpenLibrary dumps successfully with no arguments", async () => {
      const mockResponse: IngestFilesResponse = {
        message: "Ingest task created",
        task_id: 459,
      };
      const mockFetchResponse = createMockResponse(true, mockResponse);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockFetchResponse,
      );

      const result = await ingestOpenLibraryDumps();

      expect(globalThis.fetch).toHaveBeenCalledWith(ingestApiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify({}),
      });
      expect(result).toEqual(mockResponse);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Processing error" },
        "Processing error",
      ],
      ["without detail in error response", {}, "Failed to ingest files"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to ingest files",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const options: IngestFilesRequest = {
        process_authors: true,
      };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(ingestOpenLibraryDumps(options)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const options: IngestFilesRequest = {
        process_works: true,
      };
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(ingestOpenLibraryDumps(options)).rejects.toThrow(
        "Failed to ingest files",
      );
    });
  });
});
