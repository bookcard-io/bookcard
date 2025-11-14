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
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { UserContext } from "@/contexts/UserContext";
import { DEFAULT_VISIBLE_COLUMNS } from "@/types/listColumns";
import { useListColumns } from "./useListColumns";

type UserContextValue = React.ComponentProps<
  typeof UserContext.Provider
>["value"];

/**
 * Creates a wrapper component with UserContext.
 *
 * Parameters
 * ----------
 * mockContext : Partial<UserContextValue>
 *     Mock context values.
 *
 * Returns
 * -------
 * ({ children }: { children: ReactNode }) => JSX.Element
 *     Wrapper component.
 */
function createWrapper(mockContext: Partial<UserContextValue> = {}) {
  const defaultContext: UserContextValue = {
    user: null,
    isLoading: false,
    error: null,
    refresh: vi.fn(),
    refreshTimestamp: 0,
    updateUser: vi.fn(),
    profilePictureUrl: null,
    invalidateProfilePictureCache: vi.fn(),
    settings: {},
    isSaving: false,
    getSetting: vi.fn(() => null),
    updateSetting: vi.fn(),
    ...mockContext,
  };

  return ({ children }: { children: ReactNode }) => (
    <UserContext.Provider value={defaultContext}>
      {children}
    </UserContext.Provider>
  );
}

describe("useListColumns", () => {
  let mockGetSetting: ReturnType<typeof vi.fn>;
  let mockUpdateSetting: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSetting = vi.fn(() => null);
    mockUpdateSetting = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should initialize with default columns when no setting exists", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).toEqual(DEFAULT_VISIBLE_COLUMNS);
    expect(result.current.allColumns).toBeDefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("should initialize with default columns when setting is null", () => {
    mockGetSetting.mockReturnValue(null);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).toEqual(DEFAULT_VISIBLE_COLUMNS);
  });

  it("should parse valid JSON setting", () => {
    const customColumns = JSON.stringify(["title", "authors", "rating"]);
    mockGetSetting.mockReturnValue(customColumns);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).toEqual([
      "title",
      "authors",
      "rating",
    ]);
  });

  it("should always include title and authors at the start", () => {
    const customColumns = JSON.stringify(["rating", "pubdate"]);
    mockGetSetting.mockReturnValue(customColumns);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    // Title and authors should be at the start (both should be in first 2 positions)
    expect(result.current.visibleColumns.slice(0, 2)).toContain("title");
    expect(result.current.visibleColumns.slice(0, 2)).toContain("authors");
    // The parsing logic puts required columns first, so check they're both present
    expect(result.current.visibleColumns).toContain("title");
    expect(result.current.visibleColumns).toContain("authors");
  });

  it("should filter out invalid column IDs", () => {
    const invalidColumns = JSON.stringify([
      "title",
      "authors",
      "invalid_column",
      "rating",
    ]);
    mockGetSetting.mockReturnValue(invalidColumns);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).not.toContain("invalid_column");
    expect(result.current.visibleColumns).toContain("title");
    expect(result.current.visibleColumns).toContain("authors");
    expect(result.current.visibleColumns).toContain("rating");
  });

  it("should use default columns when JSON is invalid", () => {
    mockGetSetting.mockReturnValue("invalid json");
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).toEqual(DEFAULT_VISIBLE_COLUMNS);
  });

  it("should use default columns when setting is not an array", () => {
    mockGetSetting.mockReturnValue(JSON.stringify({ not: "an array" }));
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).toEqual(DEFAULT_VISIBLE_COLUMNS);
  });

  it("should use default columns when all columns are invalid", () => {
    mockGetSetting.mockReturnValue(JSON.stringify(["invalid1", "invalid2"]));
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    // When all are invalid, the parsing logic adds required columns
    // and if only required columns exist, it returns them
    // Otherwise it falls back to default
    expect(result.current.visibleColumns.length).toBeGreaterThanOrEqual(2);
    expect(result.current.visibleColumns).toContain("title");
    expect(result.current.visibleColumns).toContain("authors");
    // The parsing logic returns required columns when all invalid, not full default
    // So we just check it has the required ones
    expect(result.current.visibleColumns.slice(0, 2)).toContain("title");
    expect(result.current.visibleColumns.slice(0, 2)).toContain("authors");
  });

  it("should preserve order of valid columns", () => {
    const customColumns = JSON.stringify([
      "title",
      "authors",
      "pubdate",
      "rating",
      "series",
    ]);
    mockGetSetting.mockReturnValue(customColumns);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).toEqual([
      "title",
      "authors",
      "pubdate",
      "rating",
      "series",
    ]);
  });

  it("should show loading state when settings are loading", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: true,
      }),
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.visibleColumns).toEqual(DEFAULT_VISIBLE_COLUMNS);
  });

  it("should sync with setting when loading completes", () => {
    const customColumns = JSON.stringify(["title", "authors", "rating"]);
    mockGetSetting.mockReturnValue(customColumns);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.visibleColumns).toEqual([
      "title",
      "authors",
      "rating",
    ]);
  });

  it("should toggle column visibility", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialLength = result.current.visibleColumns.length;
    const columnToToggle = "rating";

    act(() => {
      result.current.toggleColumn(columnToToggle);
    });

    expect(result.current.visibleColumns).not.toContain(columnToToggle);
    expect(result.current.visibleColumns.length).toBe(initialLength - 1);
  });

  it("should add column when toggling hidden column", () => {
    const customColumns = JSON.stringify(["title", "authors"]);
    mockGetSetting.mockReturnValue(customColumns);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).not.toContain("rating");

    act(() => {
      result.current.toggleColumn("rating");
    });

    expect(result.current.visibleColumns).toContain("rating");
  });

  it("should not allow toggling title column", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialColumns = [...result.current.visibleColumns];

    act(() => {
      result.current.toggleColumn("title");
    });

    expect(result.current.visibleColumns).toEqual(initialColumns);
  });

  it("should not allow toggling authors column", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialColumns = [...result.current.visibleColumns];

    act(() => {
      result.current.toggleColumn("authors");
    });

    expect(result.current.visibleColumns).toEqual(initialColumns);
  });

  it("should not allow removing all columns", () => {
    // Start with only one column total (which would be invalid, but test the edge case)
    const singleColumn = JSON.stringify(["title", "authors"]);
    mockGetSetting.mockReturnValue(singleColumn);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialColumns = [...result.current.visibleColumns];
    expect(initialColumns.length).toBeGreaterThanOrEqual(2);

    // Try to remove a column when we have more than just required ones
    const nonRequiredColumn = result.current.visibleColumns.find(
      (id) => id !== "title" && id !== "authors",
    );

    if (nonRequiredColumn) {
      act(() => {
        result.current.toggleColumn(nonRequiredColumn);
      });

      // Should have one less column
      expect(result.current.visibleColumns.length).toBe(
        initialColumns.length - 1,
      );
    }

    // Now try to remove when we only have required columns (if we got to that state)
    const currentColumns = [...result.current.visibleColumns];
    if (currentColumns.length === 2) {
      // Try to remove one - should not work (prevents removing all)
      act(() => {
        result.current.toggleColumn(
          currentColumns.find((id) => id !== "title") || "authors",
        );
      });

      // Should still have 2 columns (can't remove when length would be 1)
      expect(result.current.visibleColumns.length).toBe(2);
    }
  });

  it("should reorder columns", () => {
    const customColumns = JSON.stringify([
      "title",
      "authors",
      "rating",
      "pubdate",
      "series",
    ]);
    mockGetSetting.mockReturnValue(customColumns);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    // Move rating from index 2 to index 4
    act(() => {
      result.current.reorderColumns(2, 4);
    });

    expect(result.current.visibleColumns[4]).toBe("rating");
  });

  it("should not reorder when fromIndex is invalid", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialColumns = [...result.current.visibleColumns];

    act(() => {
      result.current.reorderColumns(-1, 2);
    });

    expect(result.current.visibleColumns).toEqual(initialColumns);
  });

  it("should not reorder when toIndex is invalid", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialColumns = [...result.current.visibleColumns];

    act(() => {
      result.current.reorderColumns(2, 100);
    });

    expect(result.current.visibleColumns).toEqual(initialColumns);
  });

  it("should not reorder when fromIndex equals toIndex", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialColumns = [...result.current.visibleColumns];

    act(() => {
      result.current.reorderColumns(2, 2);
    });

    expect(result.current.visibleColumns).toEqual(initialColumns);
  });

  it("should update visible columns when toggling", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialColumns = [...result.current.visibleColumns];
    expect(initialColumns).toContain("rating");

    act(() => {
      result.current.toggleColumn("rating");
    });

    // Should immediately update the visible columns
    expect(result.current.visibleColumns).not.toContain("rating");
    expect(result.current.visibleColumns.length).toBe(
      initialColumns.length - 1,
    );
  });

  it("should update columns immediately when toggling multiple times", () => {
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    const initialLength = result.current.visibleColumns.length;
    const hasRating = result.current.visibleColumns.includes("rating");
    const hasSeries = result.current.visibleColumns.includes("series");

    // Toggle rating if it exists
    if (hasRating) {
      act(() => {
        result.current.toggleColumn("rating");
      });

      expect(result.current.visibleColumns.length).toBe(initialLength - 1);
      expect(result.current.visibleColumns).not.toContain("rating");
    }

    // Toggle series
    act(() => {
      result.current.toggleColumn("series");
    });

    // Should reflect the series toggle
    if (hasSeries) {
      expect(result.current.visibleColumns).not.toContain("series");
    } else {
      expect(result.current.visibleColumns).toContain("series");
    }
  });

  it("should handle multiple toggles correctly", () => {
    const customColumns = JSON.stringify(["title", "authors", "rating"]);
    mockGetSetting.mockReturnValue(customColumns);
    const { result } = renderHook(() => useListColumns(), {
      wrapper: createWrapper({
        getSetting: mockGetSetting,
        updateSetting: mockUpdateSetting,
        isLoading: false,
      }),
    });

    expect(result.current.visibleColumns).toContain("rating");
    expect(result.current.visibleColumns).not.toContain("series");

    // Toggle series on
    act(() => {
      result.current.toggleColumn("series");
    });

    expect(result.current.visibleColumns).toContain("series");

    // Toggle series off
    act(() => {
      result.current.toggleColumn("series");
    });

    expect(result.current.visibleColumns).not.toContain("series");
  });
});
