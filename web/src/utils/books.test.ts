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

import { describe, expect, it } from "vitest";
import type { Book } from "@/types/book";
import { deduplicateBooks, getCoverUrlWithCacheBuster } from "./books";

describe("books utils", () => {
  describe("getCoverUrlWithCacheBuster", () => {
    it("should generate cover URL with default cache buster", () => {
      const bookId = 123;
      const url = getCoverUrlWithCacheBuster(bookId);
      expect(url).toMatch(/^\/api\/books\/123\/cover\?v=\d+$/);
    });

    it("should generate cover URL with custom cache buster", () => {
      const bookId = 456;
      const cacheBuster = 1234567890;
      const url = getCoverUrlWithCacheBuster(bookId, cacheBuster);
      expect(url).toBe("/api/books/456/cover?v=1234567890");
    });
  });

  describe("deduplicateBooks", () => {
    const book1: Book = {
      id: 1,
      title: "Book 1",
      authors: ["Author 1"],
      author_sort: "Author 1",
      pubdate: null,
      timestamp: null,
      series: null,
      series_id: null,
      series_index: null,
      isbn: null,
      uuid: "uuid-1",
      thumbnail_url: "/cover1.jpg",
      has_cover: true,
    };

    const book2: Book = {
      id: 2,
      title: "Book 2",
      authors: ["Author 2"],
      author_sort: "Author 2",
      pubdate: null,
      timestamp: null,
      series: null,
      series_id: null,
      series_index: null,
      isbn: null,
      uuid: "uuid-2",
      thumbnail_url: "/cover2.jpg",
      has_cover: true,
    };

    const book1Duplicate: Book = {
      ...book1,
      title: "Book 1 Duplicate",
    };

    it("should return books as-is when no duplicates", () => {
      const books = [book1, book2];
      const result = deduplicateBooks(books);
      expect(result).toEqual(books);
      expect(result).not.toBe(books); // New array
    });

    it("should remove duplicate books by ID", () => {
      const books = [book1, book1Duplicate, book2];
      const result = deduplicateBooks(books);
      expect(result).toHaveLength(2);
      expect(result[0]?.id).toBe(1);
      expect(result[0]?.title).toBe("Book 1"); // First occurrence kept
      expect(result[1]?.id).toBe(2);
    });

    it("should apply coverUrlOverrides", () => {
      const books = [book1];
      const coverUrlOverrides = new Map([[1, "/new-cover.jpg"]]);
      const result = deduplicateBooks(books, coverUrlOverrides);
      expect(result).toHaveLength(1);
      expect(result[0]?.thumbnail_url).toBe("/new-cover.jpg");
    });

    it("should apply bookDataOverrides", () => {
      const books = [book1];
      const bookDataOverrides = new Map([
        [1, { title: "Updated Title", authors: ["New Author"] }],
      ]);
      const result = deduplicateBooks(books, undefined, bookDataOverrides);
      expect(result).toHaveLength(1);
      expect(result[0]?.title).toBe("Updated Title");
      expect(result[0]?.authors).toEqual(["New Author"]);
      expect(result[0]?.id).toBe(1); // Other properties preserved
    });

    it("should apply bookDataOverrides with cover URL", () => {
      const books = [book1];
      const bookDataOverrides = new Map([
        [1, { thumbnail_url: "/override-cover.jpg" }],
      ]);
      const result = deduplicateBooks(books, undefined, bookDataOverrides);
      expect(result).toHaveLength(1);
      expect(result[0]?.thumbnail_url).toBe("/override-cover.jpg");
    });

    it("should prioritize bookDataOverrides over coverUrlOverrides", () => {
      const books = [book1];
      const coverUrlOverrides = new Map([[1, "/old-cover.jpg"]]);
      const bookDataOverrides = new Map([
        [1, { thumbnail_url: "/new-cover.jpg" }],
      ]);
      const result = deduplicateBooks(
        books,
        coverUrlOverrides,
        bookDataOverrides,
      );
      expect(result).toHaveLength(1);
      expect(result[0]?.thumbnail_url).toBe("/new-cover.jpg");
    });

    it("should apply coverUrlOverrides when bookDataOverrides has no thumbnail_url", () => {
      const books = [book1];
      const coverUrlOverrides = new Map([[1, "/fallback-cover.jpg"]]);
      const bookDataOverrides = new Map([[1, { title: "New Title" }]]);
      const result = deduplicateBooks(
        books,
        coverUrlOverrides,
        bookDataOverrides,
      );
      expect(result).toHaveLength(1);
      expect(result[0]?.title).toBe("New Title");
      expect(result[0]?.thumbnail_url).toBe("/fallback-cover.jpg");
    });

    it("should merge bookDataOverrides with existing book data", () => {
      const books = [book1];
      const bookDataOverrides = new Map([[1, { title: "New Title" }]]);
      const result = deduplicateBooks(books, undefined, bookDataOverrides);
      expect(result).toHaveLength(1);
      expect(result[0]?.title).toBe("New Title");
      expect(result[0]?.authors).toEqual(["Author 1"]); // Preserved
      expect(result[0]?.id).toBe(1); // Preserved
    });

    it("should handle empty array", () => {
      const result = deduplicateBooks([]);
      expect(result).toEqual([]);
    });

    it("should handle multiple books with mixed overrides", () => {
      const books = [book1, book2];
      const coverUrlOverrides = new Map([[1, "/override1.jpg"]]);
      const bookDataOverrides = new Map([[2, { title: "Book 2 Updated" }]]);
      const result = deduplicateBooks(
        books,
        coverUrlOverrides,
        bookDataOverrides,
      );
      expect(result).toHaveLength(2);
      expect(result[0]?.thumbnail_url).toBe("/override1.jpg");
      expect(result[1]?.title).toBe("Book 2 Updated");
    });

    it("should not create new objects when no overrides", () => {
      const books = [book1, book2];
      const result = deduplicateBooks(books);
      // When no overrides, should return same book objects
      expect(result[0]).toBe(books[0]);
      expect(result[1]).toBe(books[1]);
    });
  });
});
