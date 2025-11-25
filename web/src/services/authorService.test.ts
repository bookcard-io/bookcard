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
import type { AuthorWithMetadata } from "@/types/author";
import {
  deleteAuthorPhoto,
  fetchAuthor,
  fetchAuthors,
  fetchAuthorsPage,
  mergeAuthors,
  recommendMergeAuthor,
  updateAuthor,
  uploadAuthorPhoto,
  uploadPhotoFromUrl,
} from "./authorService";

/**
 * Create a mock fetch response.
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

describe("authorService", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("fetchAuthor", () => {
    it("should fetch author successfully with numeric ID", async () => {
      const mockAuthor: AuthorWithMetadata = {
        key: "OL123A",
        name: "Test Author",
        personal_name: "Test",
      };
      const mockResponse = createMockResponse(true, mockAuthor);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchAuthor("123");

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123", {
        cache: "no-store",
      });
      expect(result).toEqual(mockAuthor);
    });

    it("should normalize authorId by removing /authors/ prefix", async () => {
      const mockAuthor: AuthorWithMetadata = {
        key: "OL123A",
        name: "Test Author",
      };
      const mockResponse = createMockResponse(true, mockAuthor);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await fetchAuthor("/authors/123");

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123", {
        cache: "no-store",
      });
    });

    it("should normalize authorId by removing leading / prefix", async () => {
      const mockAuthor: AuthorWithMetadata = {
        key: "OL123A",
        name: "Test Author",
      };
      const mockResponse = createMockResponse(true, mockAuthor);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await fetchAuthor("/123");

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123", {
        cache: "no-store",
      });
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Author not found" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchAuthor("123")).rejects.toThrow("Author not found");
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchAuthor("123")).rejects.toThrow(
        "Failed to fetch author",
      );
    });
  });

  describe("fetchAuthorsPage", () => {
    it("should fetch authors page successfully", async () => {
      const mockResponseData = {
        items: [
          {
            key: "OL123A",
            name: "Author 1",
          },
          {
            key: "OL456B",
            name: "Author 2",
          },
        ],
        total: 2,
        page: 1,
        page_size: 20,
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchAuthorsPage({
        page: 1,
        pageSize: 20,
      });

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors?page=1&page_size=20",
        {
          cache: "no-store",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should fetch authors page with unmatched filter", async () => {
      const mockResponseData = {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchAuthorsPage({
        page: 1,
        pageSize: 20,
        filter: "unmatched",
      });

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors?page=1&page_size=20&filter=unmatched",
        {
          cache: "no-store",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should not add filter param when filter is 'all'", async () => {
      const mockResponseData = {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchAuthorsPage({
        page: 1,
        pageSize: 20,
        filter: "all",
      });

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors?page=1&page_size=20",
        {
          cache: "no-store",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should not add filter param when filter is undefined", async () => {
      const mockResponseData = {
        items: [],
        total: 0,
        page: 1,
        page_size: 20,
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchAuthorsPage({
        page: 1,
        pageSize: 20,
      });

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors?page=1&page_size=20",
        {
          cache: "no-store",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to fetch authors" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchAuthorsPage({ page: 1, pageSize: 20 })).rejects.toThrow(
        "Failed to fetch authors",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchAuthorsPage({ page: 1, pageSize: 20 })).rejects.toThrow(
        "Failed to fetch authors",
      );
    });
  });

  describe("fetchAuthors", () => {
    it("should fetch authors as array", async () => {
      const mockAuthors: AuthorWithMetadata[] = [
        {
          key: "OL123A",
          name: "Author 1",
        },
        {
          key: "OL456B",
          name: "Author 2",
        },
      ];
      const mockResponse = createMockResponse(true, mockAuthors);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchAuthors();

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors", {
        cache: "no-store",
      });
      expect(result).toEqual(mockAuthors);
    });

    it("should fetch authors from paginated response", async () => {
      const mockPaginatedResponse = {
        items: [
          {
            key: "OL123A",
            name: "Author 1",
          },
          {
            key: "OL456B",
            name: "Author 2",
          },
        ],
        total: 2,
        page: 1,
        page_size: 20,
      };
      const mockResponse = createMockResponse(true, mockPaginatedResponse);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await fetchAuthors();

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors", {
        cache: "no-store",
      });
      expect(result).toEqual(mockPaginatedResponse.items);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to fetch authors" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchAuthors()).rejects.toThrow("Failed to fetch authors");
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(fetchAuthors()).rejects.toThrow("Failed to fetch authors");
    });
  });

  describe("updateAuthor", () => {
    it("should update author successfully", async () => {
      const mockAuthor: AuthorWithMetadata = {
        key: "OL123A",
        name: "Updated Author",
        personal_name: "Updated",
      };
      const mockResponse = createMockResponse(true, mockAuthor);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const update = {
        name: "Updated Author",
        personal_name: "Updated",
      };

      const result = await updateAuthor("123", update);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(update),
        cache: "no-store",
      });
      expect(result).toEqual(mockAuthor);
    });

    it("should normalize authorId by removing /authors/ prefix", async () => {
      const mockAuthor: AuthorWithMetadata = {
        key: "OL123A",
        name: "Updated Author",
      };
      const mockResponse = createMockResponse(true, mockAuthor);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const update = {
        name: "Updated Author",
      };

      await updateAuthor("/authors/123", update);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(update),
        cache: "no-store",
      });
    });

    it("should normalize authorId by removing leading / prefix", async () => {
      const mockAuthor: AuthorWithMetadata = {
        key: "OL123A",
        name: "Updated Author",
      };
      const mockResponse = createMockResponse(true, mockAuthor);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const update = {
        name: "Updated Author",
      };

      await updateAuthor("/123", update);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(update),
        cache: "no-store",
      });
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to update author" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const update = {
        name: "Updated Author",
      };

      await expect(updateAuthor("123", update)).rejects.toThrow(
        "Failed to update author",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const update = {
        name: "Updated Author",
      };

      await expect(updateAuthor("123", update)).rejects.toThrow(
        "Failed to update author",
      );
    });
  });

  describe("uploadAuthorPhoto", () => {
    it("should upload author photo successfully", async () => {
      const mockResponseData = {
        photo_id: 1,
        photo_url: "https://example.com/photo.jpg",
        file_path: "/path/to/photo.jpg",
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const file = new File(["test"], "photo.jpg", { type: "image/jpeg" });
      const result = await uploadAuthorPhoto("123", file);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123/photos", {
        method: "POST",
        body: expect.any(FormData),
        cache: "no-store",
      });
      expect(result).toEqual(mockResponseData);
    });

    it("should normalize authorId by removing /authors/ prefix", async () => {
      const mockResponseData = {
        photo_id: 1,
        photo_url: "https://example.com/photo.jpg",
        file_path: "/path/to/photo.jpg",
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const file = new File(["test"], "photo.jpg", { type: "image/jpeg" });
      await uploadAuthorPhoto("/authors/123", file);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123/photos", {
        method: "POST",
        body: expect.any(FormData),
        cache: "no-store",
      });
    });

    it("should normalize authorId by removing leading / prefix", async () => {
      const mockResponseData = {
        photo_id: 1,
        photo_url: "https://example.com/photo.jpg",
        file_path: "/path/to/photo.jpg",
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const file = new File(["test"], "photo.jpg", { type: "image/jpeg" });
      await uploadAuthorPhoto("/123", file);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/123/photos", {
        method: "POST",
        body: expect.any(FormData),
        cache: "no-store",
      });
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to upload photo" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const file = new File(["test"], "photo.jpg", { type: "image/jpeg" });

      await expect(uploadAuthorPhoto("123", file)).rejects.toThrow(
        "Failed to upload photo",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const file = new File(["test"], "photo.jpg", { type: "image/jpeg" });

      await expect(uploadAuthorPhoto("123", file)).rejects.toThrow(
        "Failed to upload photo",
      );
    });
  });

  describe("uploadPhotoFromUrl", () => {
    it("should upload photo from URL successfully", async () => {
      const mockResponseData = {
        photo_id: 1,
        photo_url: "https://example.com/photo.jpg",
        file_path: "/path/to/photo.jpg",
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await uploadPhotoFromUrl(
        "123",
        "https://example.com/source.jpg",
      );

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors/123/photos-from-url",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url: "https://example.com/source.jpg" }),
          cache: "no-store",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should normalize authorId by removing /authors/ prefix", async () => {
      const mockResponseData = {
        photo_id: 1,
        photo_url: "https://example.com/photo.jpg",
        file_path: "/path/to/photo.jpg",
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await uploadPhotoFromUrl(
        "/authors/123",
        "https://example.com/source.jpg",
      );

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors/123/photos-from-url",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url: "https://example.com/source.jpg" }),
          cache: "no-store",
        },
      );
    });

    it("should normalize authorId by removing leading / prefix", async () => {
      const mockResponseData = {
        photo_id: 1,
        photo_url: "https://example.com/photo.jpg",
        file_path: "/path/to/photo.jpg",
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await uploadPhotoFromUrl("/123", "https://example.com/source.jpg");

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors/123/photos-from-url",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url: "https://example.com/source.jpg" }),
          cache: "no-store",
        },
      );
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to upload photo from URL" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(
        uploadPhotoFromUrl("123", "https://example.com/source.jpg"),
      ).rejects.toThrow("Failed to upload photo from URL");
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(
        uploadPhotoFromUrl("123", "https://example.com/source.jpg"),
      ).rejects.toThrow("Failed to upload photo from URL");
    });
  });

  describe("deleteAuthorPhoto", () => {
    it("should delete author photo successfully", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await deleteAuthorPhoto("123", 1);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors/123/photos/1",
        {
          method: "DELETE",
          cache: "no-store",
        },
      );
    });

    it("should normalize authorId by removing /authors/ prefix", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await deleteAuthorPhoto("/authors/123", 1);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors/123/photos/1",
        {
          method: "DELETE",
          cache: "no-store",
        },
      );
    });

    it("should normalize authorId by removing leading / prefix", async () => {
      const mockResponse = createMockResponse(true);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await deleteAuthorPhoto("/123", 1);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors/123/photos/1",
        {
          method: "DELETE",
          cache: "no-store",
        },
      );
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to delete photo" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteAuthorPhoto("123", 1)).rejects.toThrow(
        "Failed to delete photo",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(deleteAuthorPhoto("123", 1)).rejects.toThrow(
        "Failed to delete photo",
      );
    });
  });

  describe("recommendMergeAuthor", () => {
    it("should recommend merge author successfully", async () => {
      const mockResponseData = {
        recommended_keep_id: "123",
        authors: [
          {
            id: "123",
            key: "OL123A",
            name: "Author 1",
            book_count: 10,
            is_verified: true,
            metadata_score: 0.9,
            photo_url: "https://example.com/photo.jpg",
            relationship_counts: {
              alternate_names: 2,
              remote_ids: 1,
              photos: 3,
              links: 1,
              works: 5,
              work_subjects: 2,
              similarities: 1,
              user_metadata: 0,
              user_photos: 1,
            },
          },
          {
            id: "456",
            key: "OL456B",
            name: "Author 2",
            book_count: 5,
            is_verified: false,
            metadata_score: 0.7,
            photo_url: null,
          },
        ],
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await recommendMergeAuthor(["123", "456"]);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/authors/merge/recommend",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ author_ids: ["123", "456"] }),
          cache: "no-store",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should handle null recommended_keep_id", async () => {
      const mockResponseData = {
        recommended_keep_id: null,
        authors: [
          {
            id: "123",
            key: "OL123A",
            name: "Author 1",
            book_count: 10,
            is_verified: true,
            metadata_score: 0.9,
            photo_url: null,
          },
        ],
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await recommendMergeAuthor(["123"]);

      expect(result.recommended_keep_id).toBeNull();
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to get merge recommendation" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(recommendMergeAuthor(["123", "456"])).rejects.toThrow(
        "Failed to get merge recommendation",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(recommendMergeAuthor(["123", "456"])).rejects.toThrow(
        "Failed to get merge recommendation",
      );
    });
  });

  describe("mergeAuthors", () => {
    it("should merge authors successfully", async () => {
      const mockResponseData = {
        id: "123",
        key: "OL123A",
        name: "Merged Author",
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await mergeAuthors(["123", "456"], "123");

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/authors/merge", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          author_ids: ["123", "456"],
          keep_author_id: "123",
        }),
        cache: "no-store",
      });
      expect(result).toEqual(mockResponseData);
    });

    it("should handle null id and key in response", async () => {
      const mockResponseData = {
        id: null,
        key: null,
        name: "Merged Author",
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await mergeAuthors(["123", "456"], "123");

      expect(result.id).toBeNull();
      expect(result.key).toBeNull();
      expect(result.name).toBe("Merged Author");
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to merge authors" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(mergeAuthors(["123", "456"], "123")).rejects.toThrow(
        "Failed to merge authors",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(mergeAuthors(["123", "456"], "123")).rejects.toThrow(
        "Failed to merge authors",
      );
    });
  });
});
