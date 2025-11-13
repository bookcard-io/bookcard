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
import type { Shelf } from "@/types/shelf";
import { useShelfCardMenuActions } from "./useShelfCardMenuActions";

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

describe("useShelfCardMenuActions", () => {
  it("should call onShelfDeleted when handleDelete is called", () => {
    const onShelfDeleted = vi.fn();
    const shelf = createMockShelf(1);

    const { result } = renderHook(() =>
      useShelfCardMenuActions({
        shelf,
        onShelfDeleted,
      }),
    );

    act(() => {
      result.current.handleDelete();
    });

    expect(onShelfDeleted).toHaveBeenCalledTimes(1);
  });

  it("should not throw when onShelfDeleted is undefined", () => {
    const shelf = createMockShelf(1);

    const { result } = renderHook(() =>
      useShelfCardMenuActions({
        shelf,
      }),
    );

    expect(() => {
      act(() => {
        result.current.handleDelete();
      });
    }).not.toThrow();
  });

  it("should not call onDeleteError when handleDelete is called", () => {
    const onShelfDeleted = vi.fn();
    const onDeleteError = vi.fn();
    const shelf = createMockShelf(1);

    const { result } = renderHook(() =>
      useShelfCardMenuActions({
        shelf,
        onShelfDeleted,
        onDeleteError,
      }),
    );

    act(() => {
      result.current.handleDelete();
    });

    expect(onShelfDeleted).toHaveBeenCalledTimes(1);
    expect(onDeleteError).not.toHaveBeenCalled();
  });
});
