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

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Shelf } from "@/types/shelf";
import { useRecentShelves } from "./useRecentShelves";

/**
 * Creates a mock shelf with the given ID.
 *
 * Parameters
 * ----------
 * id : number
 *     Shelf ID.
 *
 * Returns
 * -------
 * Shelf
 *     Mock shelf object.
 */
function createMockShelf(id: number): Shelf {
  return {
    id,
    uuid: `uuid-${id}`,
    name: `Shelf ${id}`,
    description: null,
    cover_picture: null,
    is_public: false,
    is_active: true,
    user_id: 1,
    library_id: 1,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    last_modified: "2024-01-01T00:00:00Z",
    book_count: 0,
  };
}

describe("useRecentShelves", () => {
  let mockStorage: Record<string, string>;

  beforeEach(() => {
    mockStorage = {};
    vi.stubGlobal("localStorage", {
      getItem: vi.fn((key: string) => mockStorage[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        mockStorage[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete mockStorage[key];
      }),
      clear: vi.fn(() => {
        mockStorage = {};
      }),
    });
  });

  afterEach(() => {
    mockStorage = {};
    vi.unstubAllGlobals();
  });

  it("should initialize with empty array when localStorage is empty", async () => {
    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([]);
    });
  });

  it("should load recent shelf IDs from localStorage on mount", async () => {
    const storedIds = [1, 2, 3];
    localStorage.setItem("calibre_recent_shelves", JSON.stringify(storedIds));

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual(storedIds);
    });
  });

  it("should handle invalid JSON in localStorage", async () => {
    localStorage.setItem("calibre_recent_shelves", "invalid json");

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([]);
    });
  });

  it("should handle non-array value in localStorage", async () => {
    localStorage.setItem("calibre_recent_shelves", JSON.stringify({ id: 1 }));

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([]);
    });
  });

  it("should handle localStorage.getItem throwing error", async () => {
    vi.stubGlobal("localStorage", {
      getItem: vi.fn(() => {
        throw new Error("Storage error");
      }),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    });

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([]);
    });
  });

  it("should add shelf to recent list", async () => {
    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([]);
    });

    act(() => {
      result.current.addRecentShelf(1);
    });

    expect(result.current.recentShelfIds).toEqual([1]);
    expect(localStorage.getItem("calibre_recent_shelves")).toBe(
      JSON.stringify([1]),
    );
  });

  it("should move existing shelf to front when added again", async () => {
    localStorage.setItem("calibre_recent_shelves", JSON.stringify([1, 2, 3]));

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([1, 2, 3]);
    });

    act(() => {
      result.current.addRecentShelf(2);
    });

    expect(result.current.recentShelfIds).toEqual([2, 1, 3]);
  });

  it("should limit recent shelves to 5", async () => {
    localStorage.setItem(
      "calibre_recent_shelves",
      JSON.stringify([1, 2, 3, 4, 5]),
    );

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([1, 2, 3, 4, 5]);
    });

    act(() => {
      result.current.addRecentShelf(6);
    });

    expect(result.current.recentShelfIds).toEqual([6, 1, 2, 3, 4]);
    expect(result.current.recentShelfIds).toHaveLength(5);
  });

  it("should handle localStorage.setItem throwing error", async () => {
    const setItemSpy = vi.fn(() => {
      throw new Error("Storage error");
    });
    vi.stubGlobal("localStorage", {
      getItem: vi.fn(() => null),
      setItem: setItemSpy,
      removeItem: vi.fn(),
      clear: vi.fn(),
    });

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([]);
    });

    act(() => {
      result.current.addRecentShelf(1);
    });

    expect(result.current.recentShelfIds).toEqual([1]);
    expect(setItemSpy).toHaveBeenCalled();
  });

  it("should get recent shelves from available shelves", async () => {
    localStorage.setItem("calibre_recent_shelves", JSON.stringify([2, 1, 3]));

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([2, 1, 3]);
    });

    const allShelves: Shelf[] = [
      createMockShelf(1),
      createMockShelf(2),
      createMockShelf(3),
      createMockShelf(4),
    ];

    const recentShelves = result.current.getRecentShelves(allShelves);
    expect(recentShelves).toHaveLength(3);
    expect(recentShelves[0]?.id).toBe(2);
    expect(recentShelves[1]?.id).toBe(1);
    expect(recentShelves[2]?.id).toBe(3);
  });

  it("should filter out shelves that no longer exist", async () => {
    localStorage.setItem("calibre_recent_shelves", JSON.stringify([1, 99, 2]));

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([1, 99, 2]);
    });

    const allShelves: Shelf[] = [createMockShelf(1), createMockShelf(2)];

    const recentShelves = result.current.getRecentShelves(allShelves);
    expect(recentShelves).toHaveLength(2);
    expect(recentShelves[0]?.id).toBe(1);
    expect(recentShelves[1]?.id).toBe(2);
  });

  it("should return empty array when no recent shelves match", async () => {
    localStorage.setItem("calibre_recent_shelves", JSON.stringify([99, 100]));

    const { result } = renderHook(() => useRecentShelves());

    await waitFor(() => {
      expect(result.current.recentShelfIds).toEqual([99, 100]);
    });

    const allShelves: Shelf[] = [createMockShelf(1), createMockShelf(2)];

    const recentShelves = result.current.getRecentShelves(allShelves);
    expect(recentShelves).toEqual([]);
  });
});
