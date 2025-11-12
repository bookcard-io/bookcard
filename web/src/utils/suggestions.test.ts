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
import type { SearchSuggestionsResponse } from "@/types/search";
import { flattenSuggestions } from "./suggestions";

describe("suggestions utils", () => {
  describe("flattenSuggestions", () => {
    it("should flatten empty response", () => {
      const response: SearchSuggestionsResponse = {
        books: [],
        authors: [],
        tags: [],
        series: [],
      };
      const result = flattenSuggestions(response);
      expect(result).toEqual([]);
    });

    it("should flatten books", () => {
      const response: SearchSuggestionsResponse = {
        books: [
          { id: 1, name: "Book 1" },
          { id: 2, name: "Book 2" },
        ],
        authors: [],
        tags: [],
        series: [],
      };
      const result = flattenSuggestions(response);
      expect(result).toEqual([
        { type: "BOOK", id: 1, name: "Book 1" },
        { type: "BOOK", id: 2, name: "Book 2" },
      ]);
    });

    it("should flatten authors", () => {
      const response: SearchSuggestionsResponse = {
        books: [],
        authors: [
          { id: 1, name: "Author 1" },
          { id: 2, name: "Author 2" },
        ],
        tags: [],
        series: [],
      };
      const result = flattenSuggestions(response);
      expect(result).toEqual([
        { type: "AUTHOR", id: 1, name: "Author 1" },
        { type: "AUTHOR", id: 2, name: "Author 2" },
      ]);
    });

    it("should flatten tags", () => {
      const response: SearchSuggestionsResponse = {
        books: [],
        authors: [],
        tags: [
          { id: 1, name: "Tag 1" },
          { id: 2, name: "Tag 2" },
        ],
        series: [],
      };
      const result = flattenSuggestions(response);
      expect(result).toEqual([
        { type: "TAG", id: 1, name: "Tag 1" },
        { type: "TAG", id: 2, name: "Tag 2" },
      ]);
    });

    it("should flatten series", () => {
      const response: SearchSuggestionsResponse = {
        books: [],
        authors: [],
        tags: [],
        series: [
          { id: 1, name: "Series 1" },
          { id: 2, name: "Series 2" },
        ],
      };
      const result = flattenSuggestions(response);
      expect(result).toEqual([
        { type: "SERIES", id: 1, name: "Series 1" },
        { type: "SERIES", id: 2, name: "Series 2" },
      ]);
    });

    it("should flatten all types in order", () => {
      const response: SearchSuggestionsResponse = {
        books: [{ id: 1, name: "Book 1" }],
        authors: [{ id: 2, name: "Author 1" }],
        tags: [{ id: 3, name: "Tag 1" }],
        series: [{ id: 4, name: "Series 1" }],
      };
      const result = flattenSuggestions(response);
      expect(result).toEqual([
        { type: "BOOK", id: 1, name: "Book 1" },
        { type: "AUTHOR", id: 2, name: "Author 1" },
        { type: "TAG", id: 3, name: "Tag 1" },
        { type: "SERIES", id: 4, name: "Series 1" },
      ]);
    });

    it("should handle multiple items of each type", () => {
      const response: SearchSuggestionsResponse = {
        books: [
          { id: 1, name: "Book 1" },
          { id: 2, name: "Book 2" },
        ],
        authors: [
          { id: 3, name: "Author 1" },
          { id: 4, name: "Author 2" },
        ],
        tags: [{ id: 5, name: "Tag 1" }],
        series: [],
      };
      const result = flattenSuggestions(response);
      expect(result).toHaveLength(5);
      expect(result[0]).toEqual({ type: "BOOK", id: 1, name: "Book 1" });
      expect(result[1]).toEqual({ type: "BOOK", id: 2, name: "Book 2" });
      expect(result[2]).toEqual({ type: "AUTHOR", id: 3, name: "Author 1" });
      expect(result[3]).toEqual({ type: "AUTHOR", id: 4, name: "Author 2" });
      expect(result[4]).toEqual({ type: "TAG", id: 5, name: "Tag 1" });
    });
  });
});
