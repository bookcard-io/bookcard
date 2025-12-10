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

import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/libs/errors";
import {
  buildImportFormData,
  parseJsonResponse,
} from "@/libs/response/handlers";
import type { Result } from "@/libs/result";
import type { ImportResult, Shelf, ShelfCreate } from "@/types/shelf";
import type { HttpClient } from "../http/HttpClient";
import { HttpShelfRepository } from "./shelfRepository";

vi.mock("@/libs/response/handlers", () => ({
  buildImportFormData: vi.fn(),
  parseJsonResponse: vi.fn(),
}));

/**
 * Create a mock HttpClient for testing.
 *
 * Returns
 * -------
 * HttpClient
 *     Mock HttpClient instance.
 */
function createMockClient(): HttpClient {
  return {
    request: vi.fn(),
  } as unknown as HttpClient;
}

/**
 * Create a mock Shelf for testing.
 *
 * Parameters
 * ----------
 * id : number
 *     Shelf ID.
 *
 * Returns
 * -------
 * Shelf
 *     Mock shelf object.
 */
function createMockShelf(id: number = 1): Shelf {
  return {
    id,
    uuid: `uuid-${id}`,
    name: `Shelf ${id}`,
    description: null,
    cover_picture: null,
    is_public: false,
    is_active: true,
    shelf_type: "shelf",
    user_id: 1,
    library_id: 1,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    last_modified: "2024-01-01T00:00:00Z",
    book_count: 0,
  };
}

/**
 * Create a mock File for testing.
 *
 * Parameters
 * ----------
 * name : string
 *     File name.
 *
 * Returns
 * -------
 * File
 *     Mock File instance.
 */
function createMockFile(name: string = "test.cbl"): File {
  const blob = new Blob(["test content"], { type: "text/plain" });
  return new File([blob], name, { type: "text/plain" });
}

/**
 * Create a mock Response for testing.
 *
 * Parameters
 * ----------
 * ok : boolean
 *     Whether the response is OK.
 * status : number
 *     HTTP status code.
 * body : unknown
 *     Response body data.
 *
 * Returns
 * -------
 * Response
 *     Mock Response instance.
 */
function createMockResponse(
  ok: boolean,
  status: number,
  body: unknown,
): Response {
  return {
    ok,
    status,
    json: vi.fn().mockResolvedValue(body),
    text: vi.fn().mockResolvedValue(JSON.stringify(body)),
  } as unknown as Response;
}

describe("HttpShelfRepository", () => {
  let mockClient: HttpClient;
  let repository: HttpShelfRepository;

  beforeEach(() => {
    vi.clearAllMocks();
    mockClient = createMockClient();
    repository = new HttpShelfRepository(mockClient);
  });

  describe("list", () => {
    it("should return list of shelves on success", async () => {
      const mockShelves = [createMockShelf(1), createMockShelf(2)];
      const mockResponse = createMockResponse(true, 200, mockShelves);

      vi.mocked(mockClient.request).mockResolvedValue(mockResponse);
      vi.mocked(parseJsonResponse).mockImplementation(
        async () =>
          ({
            isOk: true,
            value: mockShelves,
          }) as Result<Shelf[], ApiError>,
      );

      const result = await repository.list();

      expect(mockClient.request).toHaveBeenCalledWith("/shelves", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });
      expect(parseJsonResponse).toHaveBeenCalledWith(
        mockResponse,
        "Failed to fetch shelves",
      );
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockShelves);
      }
    });

    it("should return error when request fails", async () => {
      const mockResponse = createMockResponse(false, 500, {
        detail: "Server error",
      });
      const apiError = new ApiError("Server error", 500);

      vi.mocked(mockClient.request).mockResolvedValue(mockResponse);
      vi.mocked(parseJsonResponse).mockImplementation(
        async () =>
          ({
            isErr: true,
            error: apiError,
          }) as Result<Shelf[], ApiError>,
      );

      const result = await repository.list();

      expect(result.isErr).toBe(true);
      if (result.isErr) {
        expect(result.error).toBe(apiError);
      }
    });
  });

  describe("create", () => {
    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "Test Description",
      is_public: false,
    };

    it("should create shelf successfully", async () => {
      const mockShelf = createMockShelf(1);
      const mockResponse = createMockResponse(true, 201, mockShelf);

      vi.mocked(mockClient.request).mockResolvedValue(mockResponse);
      vi.mocked(parseJsonResponse).mockImplementation(
        async () =>
          ({
            isOk: true,
            value: mockShelf,
          }) as Result<Shelf, ApiError>,
      );

      const result = await repository.create(shelfData);

      expect(mockClient.request).toHaveBeenCalledWith("/shelves", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(shelfData),
      });
      expect(parseJsonResponse).toHaveBeenCalledWith(
        mockResponse,
        "Failed to create shelf",
      );
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockShelf);
      }
    });

    it("should return error when creation fails", async () => {
      const mockResponse = createMockResponse(false, 400, {
        detail: "Validation error",
      });
      const apiError = new ApiError("Validation error", 400);

      vi.mocked(mockClient.request).mockResolvedValue(mockResponse);
      vi.mocked(parseJsonResponse).mockImplementation(
        async () =>
          ({
            isErr: true,
            error: apiError,
          }) as Result<Shelf, ApiError>,
      );

      const result = await repository.create(shelfData);

      expect(result.isErr).toBe(true);
      if (result.isErr) {
        expect(result.error).toBe(apiError);
      }
    });
  });

  describe("importReadList", () => {
    const shelfId = 1;
    const file = createMockFile("test.cbl");
    const options = {
      importer: "comicrack",
      autoMatch: true,
    };
    const mockImportResult: ImportResult = {
      total_books: 7,
      matched: [],
      unmatched: [],
      errors: [],
    };

    it("should import read list successfully", async () => {
      const mockFormData = new FormData();
      const mockResponse = createMockResponse(true, 200, mockImportResult);

      vi.mocked(buildImportFormData).mockReturnValue(mockFormData);
      vi.mocked(mockClient.request).mockResolvedValue(mockResponse);
      vi.mocked(parseJsonResponse).mockImplementation(
        async () =>
          ({
            isOk: true,
            value: mockImportResult,
          }) as Result<ImportResult, ApiError>,
      );

      const result = await repository.importReadList(shelfId, file, options);

      expect(buildImportFormData).toHaveBeenCalledWith(file, options);
      expect(mockClient.request).toHaveBeenCalledWith(
        `/shelves/${shelfId}/import`,
        {
          method: "POST",
          headers: {},
          body: mockFormData,
        },
      );
      expect(parseJsonResponse).toHaveBeenCalledWith(
        mockResponse,
        "Failed to import read list",
      );
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockImportResult);
      }
    });

    it("should return error when import fails", async () => {
      const mockFormData = new FormData();
      const mockResponse = createMockResponse(false, 500, {
        detail: "Import failed",
      });
      const apiError = new ApiError("Import failed", 500);

      vi.mocked(buildImportFormData).mockReturnValue(mockFormData);
      vi.mocked(mockClient.request).mockResolvedValue(mockResponse);
      vi.mocked(parseJsonResponse).mockImplementation(
        async () =>
          ({
            isErr: true,
            error: apiError,
          }) as Result<ImportResult, ApiError>,
      );

      const result = await repository.importReadList(shelfId, file, options);

      expect(result.isErr).toBe(true);
      if (result.isErr) {
        expect(result.error).toBe(apiError);
      }
    });

    it.each([
      { importer: "comicrack", autoMatch: true },
      { importer: "comicrack", autoMatch: false },
      { importer: "calibre", autoMatch: true },
      { importer: "calibre", autoMatch: false },
    ])(
      "should handle import with importer '$importer' and autoMatch $autoMatch",
      async ({ importer, autoMatch }) => {
        const importOptions = { importer, autoMatch };
        const mockFormData = new FormData();
        const mockResponse = createMockResponse(true, 200, mockImportResult);

        vi.mocked(buildImportFormData).mockReturnValue(mockFormData);
        vi.mocked(mockClient.request).mockResolvedValue(mockResponse);
        vi.mocked(parseJsonResponse).mockImplementation(
          async () =>
            ({
              isOk: true,
              value: mockImportResult,
            }) as Result<ImportResult, ApiError>,
        );

        const result = await repository.importReadList(
          shelfId,
          file,
          importOptions,
        );

        expect(buildImportFormData).toHaveBeenCalledWith(file, importOptions);
        expect(result.isOk).toBe(true);
      },
    );
  });
});
