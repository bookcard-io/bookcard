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

import { vi } from "vitest";

vi.mock("@/services/shelfService", () => ({
  getShelf: vi.fn(),
}));

import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { getShelf } from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";
import { useShelf } from "./useShelf";

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

describe("useShelf", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should initialize with loading state", () => {
    const mockShelf = createMockShelf(1);
    vi.mocked(getShelf).mockResolvedValue(mockShelf);

    const { result } = renderHook(() => useShelf(1));

    expect(result.current.isLoading).toBe(true);
    expect(result.current.shelf).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("should load shelf successfully", async () => {
    const mockShelf = createMockShelf(1);
    vi.mocked(getShelf).mockResolvedValue(mockShelf);

    const { result } = renderHook(() => useShelf(1));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.shelf).toEqual(mockShelf);
    expect(result.current.error).toBeNull();
    expect(getShelf).toHaveBeenCalledWith(1);
  });

  it("should handle error when loading shelf", async () => {
    const errorMessage = "Failed to load shelf";
    vi.mocked(getShelf).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useShelf(1));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.shelf).toBeNull();
    expect(result.current.error).toBe(errorMessage);
  });

  it("should handle non-Error rejection", async () => {
    vi.mocked(getShelf).mockRejectedValue("String error");

    const { result } = renderHook(() => useShelf(1));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.shelf).toBeNull();
    expect(result.current.error).toBe("Failed to load shelf");
  });

  it("should refresh shelf data", async () => {
    const mockShelf1 = createMockShelf(1);
    const mockShelf2 = { ...mockShelf1, name: "Updated Shelf" };
    vi.mocked(getShelf)
      .mockResolvedValueOnce(mockShelf1)
      .mockResolvedValueOnce(mockShelf2);

    const { result } = renderHook(() => useShelf(1));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.shelf).toEqual(mockShelf1);

    await result.current.refresh();

    await waitFor(() => {
      expect(result.current.shelf).toEqual(mockShelf2);
    });
  });

  it("should reload shelf when shelfId changes", async () => {
    const mockShelf1 = createMockShelf(1);
    const mockShelf2 = createMockShelf(2);
    vi.mocked(getShelf)
      .mockResolvedValueOnce(mockShelf1)
      .mockResolvedValueOnce(mockShelf2);

    const { result, rerender } = renderHook(
      ({ shelfId }) => useShelf(shelfId),
      { initialProps: { shelfId: 1 } },
    );

    await waitFor(() => {
      expect(result.current.shelf).toEqual(mockShelf1);
    });

    rerender({ shelfId: 2 });

    await waitFor(() => {
      expect(result.current.shelf).toEqual(mockShelf2);
    });

    expect(getShelf).toHaveBeenCalledWith(2);
  });
});
