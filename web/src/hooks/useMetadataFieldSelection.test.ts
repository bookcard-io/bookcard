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

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  getAvailableFieldKeys,
  type MetadataFieldKey,
} from "@/components/metadata/metadataFields";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { useMetadataFieldSelection } from "./useMetadataFieldSelection";

// Mock the metadataFields module
vi.mock("@/components/metadata/metadataFields", () => ({
  getAvailableFieldKeys: vi.fn(),
}));

describe("useMetadataFieldSelection", () => {
  const mockRecord: MetadataRecord = {
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
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getAvailableFieldKeys).mockReturnValue(
      new Set<MetadataFieldKey>(["title", "authors", "cover", "description"]),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with empty selectedFields when not expanded", () => {
    const { result } = renderHook(() =>
      useMetadataFieldSelection({
        record: mockRecord,
        isExpanded: false,
      }),
    );

    expect(result.current.selectedFields.size).toBe(0);
    expect(getAvailableFieldKeys).not.toHaveBeenCalled();
  });

  it("should initialize with all available fields when expanded", () => {
    const availableFields = new Set<MetadataFieldKey>([
      "title",
      "authors",
      "cover",
    ]);
    vi.mocked(getAvailableFieldKeys).mockReturnValue(availableFields);

    const { result } = renderHook(() =>
      useMetadataFieldSelection({
        record: mockRecord,
        isExpanded: true,
      }),
    );

    expect(result.current.selectedFields).toEqual(availableFields);
    expect(getAvailableFieldKeys).toHaveBeenCalledWith(mockRecord);
  });

  it("should update selectedFields when isExpanded changes from false to true", () => {
    const availableFields = new Set<MetadataFieldKey>(["title", "authors"]);
    vi.mocked(getAvailableFieldKeys).mockReturnValue(availableFields);

    const { result, rerender } = renderHook(
      ({ isExpanded }) =>
        useMetadataFieldSelection({
          record: mockRecord,
          isExpanded,
        }),
      { initialProps: { isExpanded: false } },
    );

    expect(result.current.selectedFields.size).toBe(0);

    act(() => {
      rerender({ isExpanded: true });
    });

    expect(result.current.selectedFields).toEqual(availableFields);
    expect(getAvailableFieldKeys).toHaveBeenCalledWith(mockRecord);
  });

  it("should toggle a field on", () => {
    const { result } = renderHook(() =>
      useMetadataFieldSelection({
        record: mockRecord,
        isExpanded: false,
      }),
    );

    expect(result.current.selectedFields.has("title")).toBe(false);

    act(() => {
      result.current.toggleField("title");
    });

    expect(result.current.selectedFields.has("title")).toBe(true);
  });

  it("should toggle a field off", () => {
    const availableFields = new Set<MetadataFieldKey>(["title", "authors"]);
    vi.mocked(getAvailableFieldKeys).mockReturnValue(availableFields);

    const { result } = renderHook(() =>
      useMetadataFieldSelection({
        record: mockRecord,
        isExpanded: true,
      }),
    );

    expect(result.current.selectedFields.has("title")).toBe(true);

    act(() => {
      result.current.toggleField("title");
    });

    expect(result.current.selectedFields.has("title")).toBe(false);
    expect(result.current.selectedFields.has("authors")).toBe(true);
  });

  it("should select all available fields", () => {
    const availableFields = new Set<MetadataFieldKey>([
      "title",
      "authors",
      "cover",
    ]);
    vi.mocked(getAvailableFieldKeys).mockReturnValue(availableFields);

    const { result } = renderHook(() =>
      useMetadataFieldSelection({
        record: mockRecord,
        isExpanded: false,
      }),
    );

    expect(result.current.selectedFields.size).toBe(0);

    act(() => {
      result.current.selectAll();
    });

    expect(result.current.selectedFields).toEqual(availableFields);
    expect(getAvailableFieldKeys).toHaveBeenCalledWith(mockRecord);
  });

  it("should deselect all fields", () => {
    const availableFields = new Set<MetadataFieldKey>(["title", "authors"]);
    vi.mocked(getAvailableFieldKeys).mockReturnValue(availableFields);

    const { result } = renderHook(() =>
      useMetadataFieldSelection({
        record: mockRecord,
        isExpanded: true,
      }),
    );

    expect(result.current.selectedFields.size).toBeGreaterThan(0);

    act(() => {
      result.current.deselectAll();
    });

    expect(result.current.selectedFields.size).toBe(0);
  });

  it("should update selectedFields when record changes", () => {
    const firstRecord: MetadataRecord = {
      ...mockRecord,
      title: "First Book",
    };
    const secondRecord: MetadataRecord = {
      ...mockRecord,
      title: "Second Book",
    };

    const firstFields = new Set<MetadataFieldKey>(["title", "authors"]);
    const secondFields = new Set<MetadataFieldKey>(["title", "cover"]);

    vi.mocked(getAvailableFieldKeys)
      .mockReturnValueOnce(firstFields)
      .mockReturnValueOnce(secondFields);

    const { result, rerender } = renderHook(
      ({ record, isExpanded }) =>
        useMetadataFieldSelection({
          record,
          isExpanded,
        }),
      { initialProps: { record: firstRecord, isExpanded: true } },
    );

    expect(result.current.selectedFields).toEqual(firstFields);

    act(() => {
      rerender({ record: secondRecord, isExpanded: true });
    });

    expect(result.current.selectedFields).toEqual(secondFields);
  });

  it("should not update selectedFields when record changes but not expanded", () => {
    const firstRecord: MetadataRecord = {
      ...mockRecord,
      title: "First Book",
    };
    const secondRecord: MetadataRecord = {
      ...mockRecord,
      title: "Second Book",
    };

    const { result, rerender } = renderHook(
      ({ record, isExpanded }) =>
        useMetadataFieldSelection({
          record,
          isExpanded,
        }),
      { initialProps: { record: firstRecord, isExpanded: false } },
    );

    expect(result.current.selectedFields.size).toBe(0);

    act(() => {
      rerender({ record: secondRecord, isExpanded: false });
    });

    expect(result.current.selectedFields.size).toBe(0);
    expect(getAvailableFieldKeys).not.toHaveBeenCalled();
  });

  it("should handle multiple toggle operations", () => {
    const { result } = renderHook(() =>
      useMetadataFieldSelection({
        record: mockRecord,
        isExpanded: false,
      }),
    );

    act(() => {
      result.current.toggleField("title");
      result.current.toggleField("authors");
      result.current.toggleField("cover");
    });

    expect(result.current.selectedFields.has("title")).toBe(true);
    expect(result.current.selectedFields.has("authors")).toBe(true);
    expect(result.current.selectedFields.has("cover")).toBe(true);

    act(() => {
      result.current.toggleField("title");
    });

    expect(result.current.selectedFields.has("title")).toBe(false);
    expect(result.current.selectedFields.has("authors")).toBe(true);
    expect(result.current.selectedFields.has("cover")).toBe(true);
  });

  it("should handle selectAll after deselectAll", () => {
    const availableFields = new Set<MetadataFieldKey>(["title", "authors"]);
    vi.mocked(getAvailableFieldKeys).mockReturnValue(availableFields);

    const { result } = renderHook(() =>
      useMetadataFieldSelection({
        record: mockRecord,
        isExpanded: true,
      }),
    );

    act(() => {
      result.current.deselectAll();
    });

    expect(result.current.selectedFields.size).toBe(0);

    act(() => {
      result.current.selectAll();
    });

    expect(result.current.selectedFields).toEqual(availableFields);
  });
});
