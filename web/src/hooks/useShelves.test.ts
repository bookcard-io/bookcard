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
  createShelf: vi.fn(),
  listShelves: vi.fn(),
  updateShelf: vi.fn(),
  deleteShelf: vi.fn(),
}));

import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  createShelf,
  deleteShelf,
  listShelves,
  updateShelf,
} from "@/services/shelfService";
import type { Shelf } from "@/types/shelf";
import { useShelves } from "./useShelves";

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
    shelf_type: "shelf",
    user_id: 1,
    library_id: 1,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
    last_modified: "2024-01-01T00:00:00Z",
    book_count: 0,
  };
}

describe("useShelves", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should initialize with loading state", () => {
    const mockShelves = [createMockShelf(1), createMockShelf(2)];
    vi.mocked(listShelves).mockResolvedValue({
      shelves: mockShelves,
      total: 2,
    });

    const { result } = renderHook(() => useShelves());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.shelves).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("should load shelves successfully", async () => {
    const mockShelves = [createMockShelf(1), createMockShelf(2)];
    vi.mocked(listShelves).mockResolvedValue({
      shelves: mockShelves,
      total: 2,
    });

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.shelves).toEqual(mockShelves);
    expect(result.current.error).toBeNull();
  });

  it("should handle error when loading shelves", async () => {
    const errorMessage = "Failed to load shelves";
    vi.mocked(listShelves).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.shelves).toEqual([]);
    expect(result.current.error).toBe(errorMessage);
  });

  it("should handle non-Error rejection when loading", async () => {
    vi.mocked(listShelves).mockRejectedValue("String error");

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to load shelves");
  });

  it("should create shelf and refresh list", async () => {
    const newShelf = createMockShelf(3);
    const mockShelves = [createMockShelf(1), createMockShelf(2)];
    vi.mocked(listShelves)
      .mockResolvedValueOnce({
        shelves: mockShelves,
        total: 2,
      })
      .mockResolvedValueOnce({
        shelves: [...mockShelves, newShelf],
        total: 3,
      });
    vi.mocked(createShelf).mockResolvedValue(newShelf);

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.createShelf({
      name: "New Shelf",
      is_public: false,
    });

    await waitFor(() => {
      expect(result.current.shelves).toHaveLength(3);
    });

    expect(createShelf).toHaveBeenCalledWith({
      name: "New Shelf",
      is_public: false,
    });
  });

  it("should handle error when creating shelf", async () => {
    const mockShelves = [createMockShelf(1)];
    vi.mocked(listShelves).mockResolvedValue({
      shelves: mockShelves,
      total: 1,
    });
    const errorMessage = "Failed to create shelf";
    vi.mocked(createShelf).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(
      result.current.createShelf({
        name: "New Shelf",
        is_public: false,
      }),
    ).rejects.toThrow();

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage);
    });
  });

  it("should update shelf and refresh list", async () => {
    const mockShelves = [createMockShelf(1)];
    const originalShelf = mockShelves[0];
    if (!originalShelf) {
      throw new Error("originalShelf is undefined");
    }
    const updatedShelf: Shelf = {
      ...originalShelf,
      name: "Updated Shelf",
    };
    vi.mocked(listShelves)
      .mockResolvedValueOnce({
        shelves: mockShelves,
        total: 1,
      })
      .mockResolvedValueOnce({
        shelves: [updatedShelf],
        total: 1,
      });
    vi.mocked(updateShelf).mockResolvedValue(updatedShelf);

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.updateShelf(1, {
      name: "Updated Shelf",
    });

    await waitFor(() => {
      expect(result.current.shelves[0]?.name).toBe("Updated Shelf");
    });

    expect(updateShelf).toHaveBeenCalledWith(1, {
      name: "Updated Shelf",
    });
  });

  it("should handle error when updating shelf", async () => {
    const mockShelves = [createMockShelf(1)];
    vi.mocked(listShelves).mockResolvedValue({
      shelves: mockShelves,
      total: 1,
    });
    const errorMessage = "Failed to update shelf";
    vi.mocked(updateShelf).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(
      result.current.updateShelf(1, {
        name: "Updated Shelf",
      }),
    ).rejects.toThrow();

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage);
    });
  });

  it("should delete shelf and refresh list", async () => {
    const mockShelves = [createMockShelf(1), createMockShelf(2)];
    vi.mocked(listShelves)
      .mockResolvedValueOnce({
        shelves: mockShelves,
        total: 2,
      })
      .mockResolvedValueOnce({
        shelves: mockShelves[1] ? [mockShelves[1]] : [],
        total: 1,
      });
    vi.mocked(deleteShelf).mockResolvedValue(undefined);

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await result.current.deleteShelf(1);

    await waitFor(() => {
      expect(result.current.shelves).toHaveLength(1);
    });

    expect(deleteShelf).toHaveBeenCalledWith(1);
  });

  it("should handle error when deleting shelf", async () => {
    const mockShelves = [createMockShelf(1)];
    vi.mocked(listShelves).mockResolvedValue({
      shelves: mockShelves,
      total: 1,
    });
    const errorMessage = "Failed to delete shelf";
    vi.mocked(deleteShelf).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await expect(result.current.deleteShelf(1)).rejects.toThrow();

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage);
    });
  });

  it("should refresh shelves list", async () => {
    const mockShelves1 = [createMockShelf(1)];
    const mockShelves2 = [createMockShelf(1), createMockShelf(2)];
    vi.mocked(listShelves)
      .mockResolvedValueOnce({
        shelves: mockShelves1,
        total: 1,
      })
      .mockResolvedValueOnce({
        shelves: mockShelves2,
        total: 2,
      });

    const { result } = renderHook(() => useShelves());

    await waitFor(() => {
      expect(result.current.shelves).toHaveLength(1);
    });

    await result.current.refresh();

    await waitFor(() => {
      expect(result.current.shelves).toHaveLength(2);
    });
  });
});
