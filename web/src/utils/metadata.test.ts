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

import { describe, expect, it, vi } from "vitest";
import type {
  MetadataRecord,
  ProviderStatus,
} from "@/hooks/useMetadataSearchStream";
import type { BookUpdate } from "@/types/book";
import {
  applyBookUpdateToForm,
  convertMetadataRecordToBookUpdate,
  hasFailedProviders,
  sortProviderStatuses,
} from "./metadata";

describe("metadata utils", () => {
  describe("convertMetadataRecordToBookUpdate", () => {
    it("should convert minimal metadata record", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result).toEqual({
        title: "Test Book",
        author_names: ["Author 1"],
      });
    });

    it("should convert full metadata record", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1", "Author 2"],
        url: "https://example.com",
        cover_url: "https://example.com/cover.jpg",
        description: "Book description",
        series: "Test Series",
        series_index: 1,
        identifiers: { isbn: "1234567890", asin: "B00TEST" },
        publisher: "Test Publisher",
        published_date: "2024-01-15",
        rating: 4.5,
        languages: ["en", "fr"],
        tags: ["fiction", "sci-fi"],
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result).toEqual({
        title: "Test Book",
        author_names: ["Author 1", "Author 2"],
        series_name: "Test Series",
        series_index: 1,
        description: "Book description",
        publisher_name: "Test Publisher",
        pubdate: "2024-01-15",
        identifiers: [
          { type: "isbn", val: "1234567890" },
          { type: "asin", val: "B00TEST" },
        ],
        isbn: "1234567890",
        language_codes: ["en", "fr"],
        tag_names: ["fiction", "sci-fi"],
        rating_value: 5,
      });
    });

    it("should handle empty authors array", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: [],
        url: "https://example.com",
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result).not.toHaveProperty("author_names");
    });

    it("should handle null series_index", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        series: "Test Series",
        series_index: null,
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result.series_index).toBe(null);
    });

    it("should handle undefined series_index", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        series: "Test Series",
        series_index: undefined,
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result.series_index).toBe(undefined);
    });

    it("should convert published_date to YYYY-MM-DD format", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        published_date: "2024-01-15T10:30:00Z",
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result.pubdate).toBe("2024-01-15");
    });

    it("should handle invalid published_date", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        published_date: "invalid-date",
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result.pubdate).toBe(null);
    });

    it("should normalize rating to 0-5 range", () => {
      const record1: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        rating: 4.7,
      };
      const result1 = convertMetadataRecordToBookUpdate(record1);
      expect(result1.rating_value).toBe(5);

      const record2: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        rating: -1,
      };
      const result2 = convertMetadataRecordToBookUpdate(record2);
      expect(result2.rating_value).toBe(0);

      const record3: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        rating: 10,
      };
      const result3 = convertMetadataRecordToBookUpdate(record3);
      expect(result3.rating_value).toBe(5);
    });

    it("should handle null rating", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        rating: null,
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result).not.toHaveProperty("rating_value");
    });

    it("should convert identifiers from Record to array", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        identifiers: { isbn: "123", asin: "456" },
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result.identifiers).toEqual([
        { type: "isbn", val: "123" },
        { type: "asin", val: "456" },
      ]);
    });

    it("should filter out empty identifier values", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        identifiers: { isbn: "123", asin: "" },
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result.identifiers).toEqual([{ type: "isbn", val: "123" }]);
    });

    it("should handle empty identifiers", () => {
      const record: MetadataRecord = {
        source_id: "test",
        external_id: "123",
        title: "Test Book",
        authors: ["Author 1"],
        url: "https://example.com",
        identifiers: {},
      };
      const result = convertMetadataRecordToBookUpdate(record);
      expect(result).not.toHaveProperty("identifiers");
    });
  });

  describe("applyBookUpdateToForm", () => {
    it("should call handleFieldChange for each defined field", () => {
      const handleFieldChange = vi.fn();
      const update: BookUpdate = {
        title: "New Title",
        author_names: ["Author 1"],
        series_name: "Series",
        series_index: 1,
        description: "Description",
        publisher_name: "Publisher",
        pubdate: "2024-01-15",
        identifiers: [{ type: "isbn", val: "123" }],
        language_codes: ["en"],
        tag_names: ["tag1"],
        rating_value: 4,
      };
      applyBookUpdateToForm(update, handleFieldChange);
      expect(handleFieldChange).toHaveBeenCalledTimes(11);
      expect(handleFieldChange).toHaveBeenCalledWith("title", "New Title");
      expect(handleFieldChange).toHaveBeenCalledWith("author_names", [
        "Author 1",
      ]);
      expect(handleFieldChange).toHaveBeenCalledWith("series_name", "Series");
      expect(handleFieldChange).toHaveBeenCalledWith("series_index", 1);
      expect(handleFieldChange).toHaveBeenCalledWith(
        "description",
        "Description",
      );
      expect(handleFieldChange).toHaveBeenCalledWith(
        "publisher_name",
        "Publisher",
      );
      expect(handleFieldChange).toHaveBeenCalledWith("pubdate", "2024-01-15");
      expect(handleFieldChange).toHaveBeenCalledWith("identifiers", [
        { type: "isbn", val: "123" },
      ]);
      expect(handleFieldChange).toHaveBeenCalledWith("language_codes", ["en"]);
      expect(handleFieldChange).toHaveBeenCalledWith("tag_names", ["tag1"]);
      expect(handleFieldChange).toHaveBeenCalledWith("rating_value", 4);
    });

    it("should not call handleFieldChange for undefined fields", () => {
      const handleFieldChange = vi.fn();
      const update: BookUpdate = {
        title: "New Title",
      };
      applyBookUpdateToForm(update, handleFieldChange);
      expect(handleFieldChange).toHaveBeenCalledTimes(1);
      expect(handleFieldChange).toHaveBeenCalledWith("title", "New Title");
    });

    it("should not call handleFieldChange for null fields", () => {
      const handleFieldChange = vi.fn();
      const update: BookUpdate = {
        title: "New Title",
        description: null,
        series_name: null,
      };
      applyBookUpdateToForm(update, handleFieldChange);
      expect(handleFieldChange).toHaveBeenCalledTimes(1);
      expect(handleFieldChange).toHaveBeenCalledWith("title", "New Title");
    });

    it("should handle empty update", () => {
      const handleFieldChange = vi.fn();
      const update: BookUpdate = {};
      applyBookUpdateToForm(update, handleFieldChange);
      expect(handleFieldChange).not.toHaveBeenCalled();
    });
  });

  describe("sortProviderStatuses", () => {
    it("should sort by status priority", () => {
      const statuses = new Map<string, ProviderStatus>([
        [
          "provider1",
          {
            id: "provider1",
            name: "Provider 1",
            status: "completed",
            resultCount: 5,
            discovered: 5,
          },
        ],
        [
          "provider2",
          {
            id: "provider2",
            name: "Provider 2",
            status: "searching",
            resultCount: 0,
            discovered: 0,
          },
        ],
        [
          "provider3",
          {
            id: "provider3",
            name: "Provider 3",
            status: "pending",
            resultCount: 0,
            discovered: 0,
          },
        ],
        [
          "provider4",
          {
            id: "provider4",
            name: "Provider 4",
            status: "failed",
            resultCount: 0,
            discovered: 0,
          },
        ],
      ]);
      const result = sortProviderStatuses(statuses);
      expect(result).toHaveLength(4);
      expect(result[0]?.status).toBe("searching");
      expect(result[1]?.status).toBe("pending");
      expect(result[2]?.status).toBe("completed");
      expect(result[3]?.status).toBe("failed");
    });

    it("should handle empty map", () => {
      const statuses = new Map<string, ProviderStatus>();
      const result = sortProviderStatuses(statuses);
      expect(result).toEqual([]);
    });

    it("should handle single status", () => {
      const statuses = new Map<string, ProviderStatus>([
        [
          "provider1",
          {
            id: "provider1",
            name: "Provider 1",
            status: "completed",
            resultCount: 5,
            discovered: 5,
          },
        ],
      ]);
      const result = sortProviderStatuses(statuses);
      expect(result).toHaveLength(1);
      expect(result[0]?.status).toBe("completed");
    });

    it("should handle unknown status", () => {
      const statuses = new Map<string, ProviderStatus>([
        [
          "provider1",
          {
            id: "provider1",
            name: "Provider 1",
            status: "unknown" as ProviderStatus["status"],
            resultCount: 0,
            discovered: 0,
          },
        ],
      ]);
      const result = sortProviderStatuses(statuses);
      expect(result).toHaveLength(1);
      expect(result[0]?.status).toBe("unknown");
    });
  });

  describe("hasFailedProviders", () => {
    it("should return true when any provider has failed", () => {
      const statuses = new Map<string, ProviderStatus>([
        [
          "provider1",
          {
            id: "provider1",
            name: "Provider 1",
            status: "completed",
            resultCount: 5,
            discovered: 5,
          },
        ],
        [
          "provider2",
          {
            id: "provider2",
            name: "Provider 2",
            status: "failed",
            resultCount: 0,
            discovered: 0,
          },
        ],
      ]);
      expect(hasFailedProviders(statuses)).toBe(true);
    });

    it("should return false when no providers have failed", () => {
      const statuses = new Map<string, ProviderStatus>([
        [
          "provider1",
          {
            id: "provider1",
            name: "Provider 1",
            status: "completed",
            resultCount: 5,
            discovered: 5,
          },
        ],
        [
          "provider2",
          {
            id: "provider2",
            name: "Provider 2",
            status: "searching",
            resultCount: 0,
            discovered: 0,
          },
        ],
      ]);
      expect(hasFailedProviders(statuses)).toBe(false);
    });

    it("should return false for empty map", () => {
      const statuses = new Map<string, ProviderStatus>();
      expect(hasFailedProviders(statuses)).toBe(false);
    });

    it("should return true when all providers have failed", () => {
      const statuses = new Map<string, ProviderStatus>([
        [
          "provider1",
          {
            id: "provider1",
            name: "Provider 1",
            status: "failed",
            resultCount: 0,
            discovered: 0,
          },
        ],
        [
          "provider2",
          {
            id: "provider2",
            name: "Provider 2",
            status: "failed",
            resultCount: 0,
            discovered: 0,
          },
        ],
      ]);
      expect(hasFailedProviders(statuses)).toBe(true);
    });
  });
});
