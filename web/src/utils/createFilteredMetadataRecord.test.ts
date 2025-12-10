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
import type { MetadataFieldKey } from "@/components/metadata/metadataFields";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { createFilteredMetadataRecord } from "./createFilteredMetadataRecord";

/**
 * Create a mock metadata record for testing.
 *
 * Parameters
 * ----------
 * overrides : Partial<MetadataRecord>
 *     Optional overrides for record properties.
 *
 * Returns
 * -------
 * MetadataRecord
 *     Mock metadata record.
 */
function createMockRecord(
  overrides: Partial<MetadataRecord> = {},
): MetadataRecord {
  return {
    source_id: "test-source",
    external_id: "test-id",
    title: "Test Book",
    authors: ["Test Author"],
    url: "https://example.com",
    cover_url: "https://example.com/cover.jpg",
    description: "Test description",
    series: "Test Series",
    series_index: 1,
    publisher: "Test Publisher",
    published_date: "2024-01-01",
    rating: 4,
    identifiers: { isbn: "1234567890" },
    tags: ["fiction"],
    languages: ["en"],
    ...overrides,
  };
}

describe("createFilteredMetadataRecord", () => {
  it("should include all fields when all are selected", () => {
    const record = createMockRecord();
    const selectedFields = new Set<MetadataFieldKey>([
      "title",
      "authors",
      "series",
      "publisher",
      "published_date",
      "description",
      "identifiers",
      "tags",
      "rating",
      "languages",
      "cover",
    ]);

    const result = createFilteredMetadataRecord(record, selectedFields);

    expect(result.title).toBe(record.title);
    expect(result.authors).toEqual(record.authors);
    expect(result.series).toBe(record.series);
    expect(result.series_index).toBe(record.series_index);
    expect(result.publisher).toBe(record.publisher);
    expect(result.published_date).toBe(record.published_date);
    expect(result.description).toBe(record.description);
    expect(result.identifiers).toEqual(record.identifiers);
    expect(result.tags).toEqual(record.tags);
    expect(result.rating).toBe(record.rating);
    expect(result.languages).toEqual(record.languages);
    expect(result.cover_url).toBe(record.cover_url);
  });

  it("should exclude unselected fields", () => {
    const record = createMockRecord();
    const selectedFields = new Set<MetadataFieldKey>(["title"]);

    const result = createFilteredMetadataRecord(record, selectedFields);

    expect(result.title).toBe(record.title);
    expect(result.authors).toEqual([]);
    expect(result.series).toBeNull();
    expect(result.series_index).toBeNull();
    expect(result.publisher).toBeNull();
    expect(result.published_date).toBeNull();
    expect(result.description).toBeNull();
    expect(result.identifiers).toBeUndefined();
    expect(result.tags).toBeUndefined();
    expect(result.rating).toBeNull();
    expect(result.languages).toBeUndefined();
    expect(result.cover_url).toBeNull();
  });

  it("should handle empty selected fields set", () => {
    const record = createMockRecord();
    const selectedFields = new Set<MetadataFieldKey>();

    const result = createFilteredMetadataRecord(record, selectedFields);

    expect(result.title).toBe("");
    expect(result.authors).toEqual([]);
    expect(result.series).toBeNull();
    expect(result.cover_url).toBeNull();
  });

  it("should preserve non-filterable fields", () => {
    const record = createMockRecord();
    const selectedFields = new Set<MetadataFieldKey>(["title"]);

    const result = createFilteredMetadataRecord(record, selectedFields);

    expect(result.source_id).toBe(record.source_id);
    expect(result.external_id).toBe(record.external_id);
    expect(result.url).toBe(record.url);
  });

  it.each([
    {
      field: "title" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.title,
    },
    {
      field: "authors" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.authors,
    },
    {
      field: "series" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.series,
    },
    {
      field: "publisher" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.publisher,
    },
    {
      field: "published_date" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.published_date,
    },
    {
      field: "description" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.description,
    },
    {
      field: "identifiers" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.identifiers,
    },
    { field: "tags" as MetadataFieldKey, check: (r: MetadataRecord) => r.tags },
    {
      field: "rating" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.rating,
    },
    {
      field: "languages" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.languages,
    },
    {
      field: "cover" as MetadataFieldKey,
      check: (r: MetadataRecord) => r.cover_url,
    },
  ])("should include $field when selected and exclude when not", ({
    field,
    check,
  }) => {
    const record = createMockRecord();
    const selectedFields = new Set<MetadataFieldKey>([field]);

    const result = createFilteredMetadataRecord(record, selectedFields);

    expect(check(result)).toEqual(check(record));
  });

  it("should handle series_index with series field", () => {
    const record = createMockRecord({ series: "Test Series", series_index: 5 });
    const selectedFieldsWithSeries = new Set<MetadataFieldKey>(["series"]);
    const selectedFieldsWithoutSeries = new Set<MetadataFieldKey>(["title"]);

    const resultWithSeries = createFilteredMetadataRecord(
      record,
      selectedFieldsWithSeries,
    );
    const resultWithoutSeries = createFilteredMetadataRecord(
      record,
      selectedFieldsWithoutSeries,
    );

    expect(resultWithSeries.series_index).toBe(5);
    expect(resultWithoutSeries.series_index).toBeNull();
  });

  it("should handle null values in original record", () => {
    const record = createMockRecord({
      series: null,
      publisher: null,
      description: null,
      rating: null,
      cover_url: null,
    });
    const selectedFields = new Set<MetadataFieldKey>([
      "series",
      "publisher",
      "description",
      "rating",
      "cover",
    ]);

    const result = createFilteredMetadataRecord(record, selectedFields);

    expect(result.series).toBeNull();
    expect(result.publisher).toBeNull();
    expect(result.description).toBeNull();
    expect(result.rating).toBeNull();
    expect(result.cover_url).toBeNull();
  });

  it("should handle undefined values in original record", () => {
    const record = createMockRecord({
      identifiers: undefined,
      tags: undefined,
      languages: undefined,
    });
    const selectedFields = new Set<MetadataFieldKey>([
      "identifiers",
      "tags",
      "languages",
    ]);

    const result = createFilteredMetadataRecord(record, selectedFields);

    expect(result.identifiers).toBeUndefined();
    expect(result.tags).toBeUndefined();
    expect(result.languages).toBeUndefined();
  });
});
