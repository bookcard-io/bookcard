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
import type { FilterValues } from "@/components/library/widgets/FiltersPanel";
import {
  countActiveFilterTypes,
  createEmptyFilters,
  filtersToApiBody,
  hasActiveFilters,
} from "./filters";

describe("filters utils", () => {
  describe("createEmptyFilters", () => {
    it("should create empty filter values with all arrays initialized", () => {
      const filters = createEmptyFilters();
      expect(filters).toEqual({
        authorIds: [],
        titleIds: [],
        genreIds: [],
        publisherIds: [],
        identifierIds: [],
        seriesIds: [],
        formats: [],
        ratingIds: [],
        languageIds: [],
      });
    });
  });

  describe("hasActiveFilters", () => {
    it("should return false for undefined filters", () => {
      expect(hasActiveFilters(undefined)).toBe(false);
    });

    it("should return false for empty filters", () => {
      const filters = createEmptyFilters();
      expect(hasActiveFilters(filters)).toBe(false);
    });

    it("should return true when authorIds has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        authorIds: [1, 2],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when titleIds has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        titleIds: [1],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when genreIds has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        genreIds: [1],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when publisherIds has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        publisherIds: [1],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when identifierIds has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        identifierIds: [1],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when seriesIds has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        seriesIds: [1],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when formats has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        formats: ["EPUB"],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when ratingIds has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        ratingIds: [1],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when languageIds has values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        languageIds: [1],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });

    it("should return true when multiple filters have values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        authorIds: [1],
        titleIds: [2],
      };
      expect(hasActiveFilters(filters)).toBe(true);
    });
  });

  describe("countActiveFilterTypes", () => {
    it("should return 0 for undefined filters", () => {
      expect(countActiveFilterTypes(undefined)).toBe(0);
    });

    it("should return 0 for empty filters", () => {
      const filters = createEmptyFilters();
      expect(countActiveFilterTypes(filters)).toBe(0);
    });

    it("should return 1 when one filter type is active", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        authorIds: [1, 2, 3],
      };
      expect(countActiveFilterTypes(filters)).toBe(1);
    });

    it("should return 2 when two filter types are active", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        authorIds: [1],
        titleIds: [2],
      };
      expect(countActiveFilterTypes(filters)).toBe(2);
    });

    it("should return 9 when all filter types are active", () => {
      const filters: FilterValues = {
        authorIds: [1],
        titleIds: [1],
        genreIds: [1],
        publisherIds: [1],
        identifierIds: [1],
        seriesIds: [1],
        formats: ["EPUB"],
        ratingIds: [1],
        languageIds: [1],
      };
      expect(countActiveFilterTypes(filters)).toBe(9);
    });

    it("should count filter types, not individual values", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        authorIds: [1, 2, 3, 4, 5],
        titleIds: [1, 2],
      };
      expect(countActiveFilterTypes(filters)).toBe(2);
    });
  });

  describe("filtersToApiBody", () => {
    it("should convert empty filters to null values", () => {
      const filters = createEmptyFilters();
      const result = filtersToApiBody(filters);
      expect(result).toEqual({
        author_ids: null,
        title_ids: null,
        genre_ids: null,
        publisher_ids: null,
        identifier_ids: null,
        series_ids: null,
        formats: null,
        rating_ids: null,
        language_ids: null,
      });
    });

    it("should convert filters with values to arrays", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        authorIds: [1, 2, 3],
        titleIds: [4, 5],
        formats: ["EPUB", "PDF"],
      };
      const result = filtersToApiBody(filters);
      expect(result).toEqual({
        author_ids: [1, 2, 3],
        title_ids: [4, 5],
        genre_ids: null,
        publisher_ids: null,
        identifier_ids: null,
        series_ids: null,
        formats: ["EPUB", "PDF"],
        rating_ids: null,
        language_ids: null,
      });
    });

    it("should convert all filter types correctly", () => {
      const filters: FilterValues = {
        authorIds: [1],
        titleIds: [2],
        genreIds: [3],
        publisherIds: [4],
        identifierIds: [5],
        seriesIds: [6],
        formats: ["EPUB"],
        ratingIds: [7],
        languageIds: [8],
      };
      const result = filtersToApiBody(filters);
      expect(result).toEqual({
        author_ids: [1],
        title_ids: [2],
        genre_ids: [3],
        publisher_ids: [4],
        identifier_ids: [5],
        series_ids: [6],
        formats: ["EPUB"],
        rating_ids: [7],
        language_ids: [8],
      });
    });

    it("should convert empty arrays to null", () => {
      const filters: FilterValues = {
        ...createEmptyFilters(),
        authorIds: [],
        titleIds: [1],
      };
      const result = filtersToApiBody(filters);
      expect(result.author_ids).toBe(null);
      expect(result.title_ids).toEqual([1]);
    });
  });
});
