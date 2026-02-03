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
import type {
  Shelf,
  ShelfCreate,
  ShelfListResponse,
  ShelfUpdate,
} from "@/types/shelf";
import {
  addBookToShelf,
  createShelf,
  deleteShelf,
  deleteShelfCoverPicture,
  getShelf,
  getShelfBooks,
  getShelfCoverPictureUrl,
  listShelves,
  removeBookFromShelf,
  reorderShelfBooks,
  updateShelf,
  uploadShelfCoverPicture,
} from "./shelfService";

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
 * Creates a mock shelf.
 *
 * Parameters
 * ----------
 * id : number
 *     Shelf ID.
 * overrides : Partial<Shelf>
 *     Optional overrides for default values.
 *
 * Returns
 * -------
 * Shelf
 *     Mock shelf object.
 */
function createMockShelf(id: number, overrides: Partial<Shelf> = {}): Shelf {
  return {
    id,
    uuid: `uuid-${id}`,
    name: `Shelf ${id}`,
    description: `Description for shelf ${id}`,
    cover_picture: null,
    is_public: false,
    is_active: true,
    shelf_type: "shelf",
    user_id: 1,
    library_id: 1,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    last_modified: "2025-01-01T00:00:00Z",
    book_count: 0,
    ...overrides,
  };
}

/**
 * Creates a mock shelf list response.
 *
 * Parameters
 * ----------
 * shelves : Shelf[]
 *     List of shelves.
 * total : number
 *     Total count.
 *
 * Returns
 * -------
 * ShelfListResponse
 *     Mock shelf list response.
 */
function createMockShelfListResponse(
  shelves: Shelf[],
  total: number = shelves.length,
): ShelfListResponse {
  return {
    shelves,
    total,
  };
}

describe("shelfService", () => {
  const apiBase = "/api/shelves";
  const baseHeaders = {
    "Content-Type": "application/json",
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("createShelf", () => {
    it("should create shelf successfully", async () => {
      const shelfData: ShelfCreate = {
        name: "New Shelf",
        description: "A new shelf",
        is_public: false,
      };
      const mockShelf = createMockShelf(1, shelfData);
      const mockResponse = createMockResponse(true, mockShelf);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await createShelf(shelfData);

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(shelfData),
      });
      expect(result).toEqual(mockShelf);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Shelf name already exists" },
        "Shelf name already exists",
      ],
      ["without detail in error response", {}, "Failed to create shelf"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to create shelf",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const shelfData: ShelfCreate = { name: "New Shelf", is_public: false };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(createShelf(shelfData)).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const shelfData: ShelfCreate = { name: "New Shelf", is_public: false };
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(createShelf(shelfData)).rejects.toThrow(
        "Failed to create shelf",
      );
    });
  });

  describe("listShelves", () => {
    it("should list shelves successfully", async () => {
      const mockShelves = [createMockShelf(1), createMockShelf(2)];
      const mockResponseData = createMockShelfListResponse(mockShelves);
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await listShelves();

      expect(globalThis.fetch).toHaveBeenCalledWith(apiBase, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
      });
      expect(result).toEqual(mockResponseData);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Unauthorized" },
        "Unauthorized",
      ],
      ["without detail in error response", {}, "Failed to list shelves"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to list shelves",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(listShelves()).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(listShelves()).rejects.toThrow("Failed to list shelves");
    });
  });

  describe("getShelf", () => {
    const shelfId = 1;
    const url = `${apiBase}/${shelfId}`;

    it("should get shelf successfully", async () => {
      const mockShelf = createMockShelf(shelfId);
      const mockResponse = createMockResponse(true, mockShelf);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getShelf(shelfId);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "GET",
        credentials: "include",
      });
      expect(result).toEqual(mockShelf);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Shelf not found" },
        "Shelf not found",
      ],
      ["without detail in error response", {}, "Failed to get shelf"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to get shelf",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getShelf(shelfId)).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getShelf(shelfId)).rejects.toThrow("Failed to get shelf");
    });
  });

  describe("updateShelf", () => {
    const shelfId = 1;
    const url = `${apiBase}/${shelfId}`;

    it("should update shelf successfully", async () => {
      const shelfData: ShelfUpdate = {
        name: "Updated Shelf",
        description: "Updated description",
      };
      const mockShelf = createMockShelf(shelfId, {
        name: shelfData.name ?? "Shelf 1",
        description: shelfData.description ?? null,
      });
      const mockResponse = createMockResponse(true, mockShelf);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateShelf(shelfId, shelfData);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "PATCH",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify(shelfData),
      });
      expect(result).toEqual(mockShelf);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Shelf not found" },
        "Shelf not found",
      ],
      ["without detail in error response", {}, "Failed to update shelf"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to update shelf",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const shelfData: ShelfUpdate = { name: "Updated Shelf" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateShelf(shelfId, shelfData)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const shelfData: ShelfUpdate = { name: "Updated Shelf" };
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateShelf(shelfId, shelfData)).rejects.toThrow(
        "Failed to update shelf",
      );
    });
  });

  describe("deleteShelf", () => {
    const shelfId = 1;
    const url = `${apiBase}/${shelfId}`;

    it("should delete shelf successfully", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await deleteShelf(shelfId);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "DELETE",
        credentials: "include",
      });
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Shelf not found" },
        "Shelf not found",
      ],
      ["without detail in error response", {}, "Failed to delete shelf"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to delete shelf",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteShelf(shelfId)).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteShelf(shelfId)).rejects.toThrow(
        "Failed to delete shelf",
      );
    });
  });

  describe("addBookToShelf", () => {
    const shelfId = 1;
    const bookId = 100;
    const url = `${apiBase}/${shelfId}/books/${bookId}`;

    it("should add book to shelf successfully", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await addBookToShelf(shelfId, bookId);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "POST",
        credentials: "include",
      });
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Book already in shelf" },
        "Book already in shelf",
      ],
      ["without detail in error response", {}, "Failed to add book to shelf"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to add book to shelf",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(addBookToShelf(shelfId, bookId)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(addBookToShelf(shelfId, bookId)).rejects.toThrow(
        "Failed to add book to shelf",
      );
    });
  });

  describe("removeBookFromShelf", () => {
    const shelfId = 1;
    const bookId = 100;
    const url = `${apiBase}/${shelfId}/books/${bookId}`;

    it("should remove book from shelf successfully", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await removeBookFromShelf(shelfId, bookId);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "DELETE",
        credentials: "include",
      });
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Book not in shelf" },
        "Book not in shelf",
      ],
      [
        "without detail in error response",
        {},
        "Failed to remove book from shelf",
      ],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to remove book from shelf",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(removeBookFromShelf(shelfId, bookId)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(removeBookFromShelf(shelfId, bookId)).rejects.toThrow(
        "Failed to remove book from shelf",
      );
    });
  });

  describe("reorderShelfBooks", () => {
    const shelfId = 1;
    const url = `${apiBase}/${shelfId}/books/reorder`;
    const bookOrders = { 100: 1, 101: 2, 102: 3 };

    it("should reorder shelf books successfully", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await reorderShelfBooks(shelfId, bookOrders);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "POST",
        headers: baseHeaders,
        credentials: "include",
        body: JSON.stringify({ book_orders: bookOrders }),
      });
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Invalid book orders" },
        "Invalid book orders",
      ],
      ["without detail in error response", {}, "Failed to reorder shelf books"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to reorder shelf books",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(reorderShelfBooks(shelfId, bookOrders)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(reorderShelfBooks(shelfId, bookOrders)).rejects.toThrow(
        "Failed to reorder shelf books",
      );
    });
  });

  describe("getShelfBooks", () => {
    const shelfId = 1;
    const baseUrl = `${apiBase}/${shelfId}/books`;

    it.each<[string, number, string, string]>([
      [
        "with default parameters",
        1,
        "order",
        "page=1&page_size=20&sort_by=order&sort_order=asc",
      ],
      [
        "with custom page",
        2,
        "order",
        "page=2&page_size=20&sort_by=order&sort_order=asc",
      ],
      [
        "with custom sortBy",
        1,
        "date_added",
        "page=1&page_size=20&sort_by=date_added&sort_order=asc",
      ],
      [
        "with book_id sortBy",
        1,
        "book_id",
        "page=1&page_size=20&sort_by=book_id&sort_order=asc",
      ],
    ])("should get shelf books successfully %s", async (_desc, page, sortBy, expectedParams) => {
      const mockBookIds = [100, 101, 102];
      const url = `${baseUrl}?${expectedParams}`;
      const mockResponse = createMockResponse(true, mockBookIds);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getShelfBooks(shelfId, page, sortBy);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
      });
      expect(result).toEqual(mockBookIds);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Shelf not found" },
        "Shelf not found",
      ],
      ["without detail in error response", {}, "Failed to get shelf books"],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to get shelf books",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getShelfBooks(shelfId)).rejects.toThrow(expectedMessage);
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getShelfBooks(shelfId)).rejects.toThrow(
        "Failed to get shelf books",
      );
    });
  });

  describe("uploadShelfCoverPicture", () => {
    const shelfId = 1;
    const url = `${apiBase}/${shelfId}/cover-picture`;

    it("should upload shelf cover picture successfully", async () => {
      const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
      const mockShelf = createMockShelf(shelfId, {
        cover_picture: "cover.jpg",
      });
      const mockResponse = createMockResponse(true, mockShelf);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await uploadShelfCoverPicture(shelfId, file);

      const formData = new FormData();
      formData.append("file", file);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      expect(result).toEqual(mockShelf);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Invalid file type" },
        "Invalid file type",
      ],
      [
        "without detail in error response",
        {},
        "Failed to upload cover picture",
      ],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to upload cover picture",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(uploadShelfCoverPicture(shelfId, file)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const file = new File(["test"], "cover.jpg", { type: "image/jpeg" });
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(uploadShelfCoverPicture(shelfId, file)).rejects.toThrow(
        "Failed to upload cover picture",
      );
    });
  });

  describe("getShelfCoverPictureUrl", () => {
    it("should return correct cover picture URL", () => {
      const shelfId = 1;
      const expectedUrl = `${apiBase}/${shelfId}/cover-picture`;

      const result = getShelfCoverPictureUrl(shelfId);

      expect(result).toBe(expectedUrl);
    });
  });

  describe("deleteShelfCoverPicture", () => {
    const shelfId = 1;
    const url = `${apiBase}/${shelfId}/cover-picture`;

    it("should delete shelf cover picture successfully", async () => {
      const mockShelf = createMockShelf(shelfId, { cover_picture: null });
      const mockResponse = createMockResponse(true, mockShelf);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await deleteShelfCoverPicture(shelfId);

      expect(globalThis.fetch).toHaveBeenCalledWith(url, {
        method: "DELETE",
        credentials: "include",
      });
      expect(result).toEqual(mockShelf);
    });

    it.each<[string, unknown, string]>([
      [
        "with detail in error response",
        { detail: "Shelf not found" },
        "Shelf not found",
      ],
      [
        "without detail in error response",
        {},
        "Failed to delete cover picture",
      ],
      [
        "with empty detail in error response",
        { detail: "" },
        "Failed to delete cover picture",
      ],
    ])("should throw error when response is not ok %s", async (_desc, errorData, expectedMessage) => {
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteShelfCoverPicture(shelfId)).rejects.toThrow(
        expectedMessage,
      );
    });

    it("should throw error when JSON parsing fails", async () => {
      const mockResponse = createMockResponse(
        false,
        {},
        new Error("Invalid JSON"),
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteShelfCoverPicture(shelfId)).rejects.toThrow(
        "Failed to delete cover picture",
      );
    });
  });
});
