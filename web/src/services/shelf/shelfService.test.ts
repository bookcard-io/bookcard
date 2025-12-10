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
import type { ImportResult, Shelf, ShelfCreate } from "@/types/shelf";
import type { ShelfRepository } from "./shelfRepository";
import { ShelfService } from "./shelfService";

/**
 * Create a mock ShelfRepository for testing.
 *
 * Returns
 * -------
 * ShelfRepository
 *     Mock repository instance.
 */
function createMockRepository(): ShelfRepository {
  return {
    list: vi.fn(),
    create: vi.fn(),
    importReadList: vi.fn(),
  } as unknown as ShelfRepository;
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

describe("ShelfService", () => {
  let mockRepository: ShelfRepository;
  let service: ShelfService;

  beforeEach(() => {
    vi.clearAllMocks();
    mockRepository = createMockRepository();
    service = new ShelfService(mockRepository);
  });

  describe("list", () => {
    it("should delegate to repository list", async () => {
      const mockShelves = [createMockShelf(1), createMockShelf(2)];

      vi.mocked(mockRepository.list).mockResolvedValue({
        isOk: true,
        value: mockShelves,
      } as Awaited<ReturnType<typeof mockRepository.list>>);

      const result = await service.list();

      expect(mockRepository.list).toHaveBeenCalled();
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockShelves);
      }
    });

    it("should propagate repository errors", async () => {
      const apiError = new ApiError("Failed to fetch", 500);

      vi.mocked(mockRepository.list).mockResolvedValue({
        isErr: true,
        error: apiError,
      } as Awaited<ReturnType<typeof mockRepository.list>>);

      const result = await service.list();

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

    it("should delegate to repository create", async () => {
      const mockShelf = createMockShelf(1);

      vi.mocked(mockRepository.create).mockResolvedValue({
        isOk: true,
        value: mockShelf,
      } as Awaited<ReturnType<typeof mockRepository.create>>);

      const result = await service.create(shelfData);

      expect(mockRepository.create).toHaveBeenCalledWith(shelfData);
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockShelf);
      }
    });

    it("should propagate repository errors", async () => {
      const apiError = new ApiError("Validation error", 400);

      vi.mocked(mockRepository.create).mockResolvedValue({
        isErr: true,
        error: apiError,
      } as Awaited<ReturnType<typeof mockRepository.create>>);

      const result = await service.create(shelfData);

      expect(result.isErr).toBe(true);
      if (result.isErr) {
        expect(result.error).toBe(apiError);
      }
    });
  });

  describe("createWithImport", () => {
    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "Test Description",
      is_public: false,
    };
    const importOptions = {
      importer: "comicrack",
      autoMatch: true,
    };

    it("should create shelf and return it when no file provided", async () => {
      const mockShelf = createMockShelf(1);

      vi.mocked(mockRepository.create).mockResolvedValue({
        isOk: true,
        value: mockShelf,
      } as Awaited<ReturnType<typeof mockRepository.create>>);

      const result = await service.createWithImport(
        shelfData,
        null,
        importOptions,
      );

      expect(mockRepository.create).toHaveBeenCalledWith(shelfData);
      expect(mockRepository.importReadList).not.toHaveBeenCalled();
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockShelf);
      }
    });

    it("should return error when shelf creation fails", async () => {
      const apiError = new ApiError("Creation failed", 400);

      vi.mocked(mockRepository.create).mockResolvedValue({
        isErr: true,
        error: apiError,
      } as Awaited<ReturnType<typeof mockRepository.create>>);

      const result = await service.createWithImport(
        shelfData,
        createMockFile(),
        importOptions,
      );

      expect(mockRepository.create).toHaveBeenCalledWith(shelfData);
      expect(mockRepository.importReadList).not.toHaveBeenCalled();
      expect(result.isErr).toBe(true);
      if (result.isErr) {
        expect(result.error).toBe(apiError);
      }
    });

    it("should create shelf and import file successfully", async () => {
      const mockShelf = createMockShelf(1);
      const file = createMockFile();
      const mockImportResult: ImportResult = {
        total_books: 7,
        matched: [],
        unmatched: [],
        errors: [],
      };

      vi.mocked(mockRepository.create).mockResolvedValue({
        isOk: true,
        value: mockShelf,
      } as Awaited<ReturnType<typeof mockRepository.create>>);
      vi.mocked(mockRepository.importReadList).mockResolvedValue({
        isOk: true,
        value: mockImportResult,
      } as Awaited<ReturnType<typeof mockRepository.importReadList>>);

      const result = await service.createWithImport(
        shelfData,
        file,
        importOptions,
      );

      expect(mockRepository.create).toHaveBeenCalledWith(shelfData);
      expect(mockRepository.importReadList).toHaveBeenCalledWith(
        mockShelf.id,
        file,
        importOptions,
      );
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockShelf);
      }
    });

    it("should return shelf even when import fails", async () => {
      const mockShelf = createMockShelf(1);
      const file = createMockFile();
      const importError = new ApiError("Import failed", 500);
      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      vi.mocked(mockRepository.create).mockResolvedValue({
        isOk: true,
        value: mockShelf,
      } as Awaited<ReturnType<typeof mockRepository.create>>);
      vi.mocked(mockRepository.importReadList).mockResolvedValue({
        isErr: true,
        error: importError,
      } as Awaited<ReturnType<typeof mockRepository.importReadList>>);

      const result = await service.createWithImport(
        shelfData,
        file,
        importOptions,
      );

      expect(mockRepository.create).toHaveBeenCalledWith(shelfData);
      expect(mockRepository.importReadList).toHaveBeenCalledWith(
        mockShelf.id,
        file,
        importOptions,
      );
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Failed to import read list:",
        importError,
      );
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockShelf);
      }

      consoleErrorSpy.mockRestore();
    });
  });

  describe("importReadList", () => {
    const shelfId = 1;
    const file = createMockFile();
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

    it("should delegate to repository importReadList", async () => {
      vi.mocked(mockRepository.importReadList).mockResolvedValue({
        isOk: true,
        value: mockImportResult,
      } as Awaited<ReturnType<typeof mockRepository.importReadList>>);

      const result = await service.importReadList(shelfId, file, options);

      expect(mockRepository.importReadList).toHaveBeenCalledWith(
        shelfId,
        file,
        options,
      );
      expect(result.isOk).toBe(true);
      if (result.isOk) {
        expect(result.value).toEqual(mockImportResult);
      }
    });

    it("should propagate repository errors", async () => {
      const apiError = new ApiError("Import failed", 500);

      vi.mocked(mockRepository.importReadList).mockResolvedValue({
        isErr: true,
        error: apiError,
      } as Awaited<ReturnType<typeof mockRepository.importReadList>>);

      const result = await service.importReadList(shelfId, file, options);

      expect(result.isErr).toBe(true);
      if (result.isErr) {
        expect(result.error).toBe(apiError);
      }
    });
  });
});
