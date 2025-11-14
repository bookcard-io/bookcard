import { describe, expect, it } from "vitest";
import type { Book } from "@/types/book";
import {
  formatAuthors,
  getBookCardAriaLabel,
  getBookListItemAriaLabel,
} from "./book";

describe("book utils", () => {
  const createMockBook = (title: string, authors: string[]): Book => ({
    id: 1,
    title,
    authors,
    author_sort: authors.join(", "),
    pubdate: null,
    timestamp: null,
    series: null,
    series_id: null,
    series_index: null,
    isbn: null,
    uuid: "uuid-1",
    thumbnail_url: null,
    has_cover: false,
  });

  describe("formatAuthors", () => {
    it("should format single author", () => {
      expect(formatAuthors(["John Doe"])).toBe("John Doe");
    });

    it("should format multiple authors", () => {
      expect(formatAuthors(["John Doe", "Jane Smith"])).toBe(
        "John Doe, Jane Smith",
      );
    });

    it("should return 'Unknown Author' for empty array", () => {
      expect(formatAuthors([])).toBe("Unknown Author");
    });
  });

  describe("getBookCardAriaLabel", () => {
    it("should generate aria label for unselected book", () => {
      const book = createMockBook("Test Book", ["John Doe"]);
      const result = getBookCardAriaLabel(book, false);
      expect(result).toBe("Test Book by John Doe. Click to view details.");
    });

    it("should generate aria label for selected book", () => {
      const book = createMockBook("Test Book", ["John Doe"]);
      const result = getBookCardAriaLabel(book, true);
      expect(result).toBe(
        "Test Book by John Doe (selected). Click to view details.",
      );
    });

    it("should handle multiple authors", () => {
      const book = createMockBook("Test Book", ["John Doe", "Jane Smith"]);
      const result = getBookCardAriaLabel(book, false);
      expect(result).toBe(
        "Test Book by John Doe, Jane Smith. Click to view details.",
      );
    });

    it("should handle empty authors array", () => {
      const book = createMockBook("Test Book", []);
      const result = getBookCardAriaLabel(book, false);
      expect(result).toBe(
        "Test Book by Unknown Author. Click to view details.",
      );
    });
  });

  describe("getBookListItemAriaLabel", () => {
    it("should generate aria label for unselected book", () => {
      const book = createMockBook("Test Book", ["John Doe"]);
      const result = getBookListItemAriaLabel(book, false);
      expect(result).toBe("Test Book by John Doe. Click to view details.");
    });

    it("should generate aria label for selected book", () => {
      const book = createMockBook("Test Book", ["John Doe"]);
      const result = getBookListItemAriaLabel(book, true);
      expect(result).toBe(
        "Test Book by John Doe (selected). Click to view details.",
      );
    });

    it("should handle multiple authors", () => {
      const book = createMockBook("Test Book", ["John Doe", "Jane Smith"]);
      const result = getBookListItemAriaLabel(book, false);
      expect(result).toBe(
        "Test Book by John Doe, Jane Smith. Click to view details.",
      );
    });

    it("should handle empty authors array", () => {
      const book = createMockBook("Test Book", []);
      const result = getBookListItemAriaLabel(book, false);
      expect(result).toBe(
        "Test Book by Unknown Author. Click to view details.",
      );
    });
  });
});
