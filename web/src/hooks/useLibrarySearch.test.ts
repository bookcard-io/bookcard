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
import { describe, expect, it, vi } from "vitest";
import { useLibrarySearch } from "./useLibrarySearch";

describe("useLibrarySearch", () => {
  it("should initialize with empty search values", () => {
    const { result } = renderHook(() => useLibrarySearch());
    expect(result.current.searchInputValue).toBe("");
    expect(result.current.filterQuery).toBe("");
  });

  it("should update search input value", () => {
    const { result } = renderHook(() => useLibrarySearch());
    act(() => {
      result.current.handleSearchChange("test query");
    });
    expect(result.current.searchInputValue).toBe("test query");
    expect(result.current.filterQuery).toBe(""); // Should not filter yet
  });

  it("should submit search and update filter query", () => {
    const onClearFilters = vi.fn();
    const { result } = renderHook(() => useLibrarySearch({ onClearFilters }));
    act(() => {
      result.current.handleSearchSubmit("test query");
    });
    expect(result.current.searchInputValue).toBe("test query");
    expect(result.current.filterQuery).toBe("test query");
    expect(onClearFilters).toHaveBeenCalledTimes(1);
  });

  it("should handle suggestion click for TAG", () => {
    const onClearFilters = vi.fn();
    const { result } = renderHook(() => useLibrarySearch({ onClearFilters }));
    act(() => {
      result.current.handleSuggestionClick({
        type: "TAG",
        id: 1,
        name: "fiction",
      });
    });
    expect(result.current.filterQuery).toBe("fiction");
    expect(result.current.searchInputValue).toBe("fiction");
    expect(onClearFilters).toHaveBeenCalledTimes(1);
  });

  it("should handle suggestion click for AUTHOR", () => {
    const onClearFilters = vi.fn();
    const { result } = renderHook(() => useLibrarySearch({ onClearFilters }));
    act(() => {
      result.current.handleSuggestionClick({
        type: "AUTHOR",
        id: 1,
        name: "John Doe",
      });
    });
    expect(result.current.filterQuery).toBe("John Doe");
    expect(result.current.searchInputValue).toBe("John Doe");
    expect(onClearFilters).toHaveBeenCalledTimes(1);
  });

  it("should handle suggestion click for SERIES", () => {
    const onClearFilters = vi.fn();
    const { result } = renderHook(() => useLibrarySearch({ onClearFilters }));
    act(() => {
      result.current.handleSuggestionClick({
        type: "SERIES",
        id: 1,
        name: "Test Series",
      });
    });
    expect(result.current.filterQuery).toBe("Test Series");
    expect(result.current.searchInputValue).toBe("Test Series");
    expect(onClearFilters).toHaveBeenCalledTimes(1);
  });

  it("should handle suggestion click for BOOK", () => {
    const onBookClick = vi.fn();
    const { result } = renderHook(() => useLibrarySearch({ onBookClick }));
    act(() => {
      result.current.handleSuggestionClick({
        type: "BOOK",
        id: 123,
        name: "Test Book",
      });
    });
    expect(onBookClick).toHaveBeenCalledWith(123);
    expect(result.current.filterQuery).toBe(""); // Should not filter
    expect(result.current.searchInputValue).toBe(""); // Should not update input
  });

  it("should clear search", () => {
    const { result } = renderHook(() => useLibrarySearch());
    act(() => {
      result.current.handleSearchSubmit("test query");
    });
    expect(result.current.filterQuery).toBe("test query");

    act(() => {
      result.current.clearSearch();
    });
    expect(result.current.searchInputValue).toBe("");
    expect(result.current.filterQuery).toBe("");
  });

  it("should handle suggestion click for BOOK type without onBookClick", () => {
    const { result } = renderHook(() => useLibrarySearch());
    act(() => {
      result.current.handleSuggestionClick({
        type: "BOOK",
        id: 123,
        name: "Test Book",
      });
    });
    // Should not crash
    expect(result.current.filterQuery).toBe("");
  });
});
