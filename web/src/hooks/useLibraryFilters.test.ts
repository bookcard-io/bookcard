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
import { createEmptyFilters } from "@/utils/filters";
import { useLibraryFilters } from "./useLibraryFilters";

describe("useLibraryFilters", () => {
  it("should initialize with empty filters", () => {
    const { result } = renderHook(() => useLibraryFilters());
    expect(result.current.filters).toEqual(createEmptyFilters());
    expect(result.current.selectedFilterSuggestions).toEqual({});
    expect(result.current.showFiltersPanel).toBe(false);
  });

  it("should toggle filters panel", () => {
    const { result } = renderHook(() => useLibraryFilters());
    act(() => {
      result.current.handleFiltersClick();
    });
    expect(result.current.showFiltersPanel).toBe(true);

    act(() => {
      result.current.handleFiltersClick();
    });
    expect(result.current.showFiltersPanel).toBe(false);
  });

  it("should update filters", () => {
    const { result } = renderHook(() => useLibraryFilters());
    const newFilters = {
      ...createEmptyFilters(),
      authorIds: [1, 2],
    };
    act(() => {
      result.current.handleFiltersChange(newFilters);
    });
    expect(result.current.filters).toEqual(newFilters);
  });

  it("should update selected suggestions", () => {
    const { result } = renderHook(() => useLibraryFilters());
    const suggestions = {
      authorIds: [{ id: 1, name: "Author 1" }],
    };
    act(() => {
      result.current.handleSuggestionsChange(suggestions);
    });
    expect(result.current.selectedFilterSuggestions).toEqual(suggestions);
  });

  it("should apply filters and close panel", () => {
    const onClearSearch = vi.fn();
    const { result } = renderHook(() => useLibraryFilters({ onClearSearch }));
    const appliedFilters = {
      ...createEmptyFilters(),
      authorIds: [1],
    };

    act(() => {
      result.current.handleApplyFilters(appliedFilters);
    });

    expect(result.current.filters).toEqual(appliedFilters);
    expect(result.current.showFiltersPanel).toBe(false);
    expect(onClearSearch).toHaveBeenCalledTimes(1);
  });

  it("should clear filters", () => {
    const { result } = renderHook(() => useLibraryFilters());
    act(() => {
      result.current.handleFiltersChange({
        ...createEmptyFilters(),
        authorIds: [1],
      });
      result.current.handleSuggestionsChange({
        authorIds: [{ id: 1, name: "Author 1" }],
      });
    });

    act(() => {
      result.current.handleClearFilters();
    });

    expect(result.current.filters).toEqual(createEmptyFilters());
    expect(result.current.selectedFilterSuggestions).toEqual({});
  });

  it("should close filters panel", () => {
    const { result } = renderHook(() => useLibraryFilters());
    act(() => {
      result.current.handleFiltersClick();
    });
    expect(result.current.showFiltersPanel).toBe(true);

    act(() => {
      result.current.handleCloseFiltersPanel();
    });
    expect(result.current.showFiltersPanel).toBe(false);
  });

  it("should clear filters programmatically", () => {
    const { result } = renderHook(() => useLibraryFilters());
    act(() => {
      result.current.handleFiltersChange({
        ...createEmptyFilters(),
        authorIds: [1],
      });
    });

    act(() => {
      result.current.clearFilters();
    });

    expect(result.current.filters).toEqual(createEmptyFilters());
  });

  it("should close filters panel programmatically", () => {
    const { result } = renderHook(() => useLibraryFilters());
    act(() => {
      result.current.handleFiltersClick();
    });

    act(() => {
      result.current.closeFiltersPanel();
    });

    expect(result.current.showFiltersPanel).toBe(false);
  });

  it("should call onFiltersPanelChange when panel visibility changes", () => {
    const onFiltersPanelChange = vi.fn();
    const { result } = renderHook(() =>
      useLibraryFilters({ onFiltersPanelChange }),
    );

    act(() => {
      result.current.handleFiltersClick();
    });
    expect(onFiltersPanelChange).toHaveBeenCalledWith(true);

    act(() => {
      result.current.handleFiltersClick();
    });
    expect(onFiltersPanelChange).toHaveBeenCalledWith(false);
  });
});
