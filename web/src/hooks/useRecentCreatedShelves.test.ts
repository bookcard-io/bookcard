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

import { renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Shelf } from "@/types/shelf";
import { useRecentCreatedShelves } from "./useRecentCreatedShelves";

/**
 * Creates a mock shelf with the given ID and creation date.
 *
 * Parameters
 * ----------
 * id : number
 *     Shelf ID.
 * created_at : string
 *     Creation timestamp.
 *
 * Returns
 * -------
 * Shelf
 *     Mock shelf object.
 */
function createMockShelf(id: number, created_at: string): Shelf {
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
    created_at,
    updated_at: created_at,
    last_modified: created_at,
    book_count: 0,
  };
}

describe("useRecentCreatedShelves", () => {
  it("should return empty array when shelves is empty", () => {
    const { result } = renderHook(() => useRecentCreatedShelves([]));
    expect(result.current).toEqual([]);
  });

  it("should return shelves sorted by creation date (most recent first)", () => {
    const shelves: Shelf[] = [
      createMockShelf(1, "2024-01-01T00:00:00Z"),
      createMockShelf(2, "2024-01-03T00:00:00Z"),
      createMockShelf(3, "2024-01-02T00:00:00Z"),
    ];

    const { result } = renderHook(() => useRecentCreatedShelves(shelves));
    expect(result.current).toHaveLength(3);
    expect(result.current[0]?.id).toBe(2);
    expect(result.current[1]?.id).toBe(3);
    expect(result.current[2]?.id).toBe(1);
  });

  it("should limit results to 5 most recent shelves", () => {
    const shelves: Shelf[] = Array.from({ length: 10 }, (_, i) =>
      createMockShelf(
        i + 1,
        `2024-01-${String(i + 1).padStart(2, "0")}T00:00:00Z`,
      ),
    );

    const { result } = renderHook(() => useRecentCreatedShelves(shelves));
    expect(result.current).toHaveLength(3);
    expect(result.current[0]?.id).toBe(10);
    expect(result.current[4]?.id).toBe(6);
  });

  it("should handle shelves with same creation date", () => {
    const sameDate = "2024-01-01T00:00:00Z";
    const shelves: Shelf[] = [
      createMockShelf(1, sameDate),
      createMockShelf(2, sameDate),
      createMockShelf(3, sameDate),
    ];

    const { result } = renderHook(() => useRecentCreatedShelves(shelves));
    expect(result.current).toHaveLength(3);
    expect(result.current.map((s) => s.id)).toContain(1);
    expect(result.current.map((s) => s.id)).toContain(2);
    expect(result.current.map((s) => s.id)).toContain(3);
  });

  it("should memoize result when shelves array reference doesn't change", () => {
    const shelves: Shelf[] = [
      createMockShelf(1, "2024-01-01T00:00:00Z"),
      createMockShelf(2, "2024-01-02T00:00:00Z"),
    ];

    const { result, rerender } = renderHook(
      ({ shelves }) => useRecentCreatedShelves(shelves),
      { initialProps: { shelves } },
    );

    const firstResult = result.current;
    rerender({ shelves });
    expect(result.current).toBe(firstResult);
  });

  it("should recalculate when shelves array changes", () => {
    const shelves1: Shelf[] = [createMockShelf(1, "2024-01-01T00:00:00Z")];
    const shelves2: Shelf[] = [
      createMockShelf(1, "2024-01-01T00:00:00Z"),
      createMockShelf(2, "2024-01-02T00:00:00Z"),
    ];

    const { result, rerender } = renderHook(
      ({ shelves }) => useRecentCreatedShelves(shelves),
      { initialProps: { shelves: shelves1 } },
    );

    expect(result.current).toHaveLength(1);
    rerender({ shelves: shelves2 });
    expect(result.current).toHaveLength(2);
  });
});
