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
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";
import { useShelfGridOperations } from "./useShelfGridOperations";

vi.mock("@/hooks/useShelves", () => ({
  useShelves: vi.fn(),
}));

vi.mock("@/contexts/ShelvesContext", () => ({
  useShelvesContext: vi.fn(),
}));

vi.mock("@/services/shelfService", () => ({
  deleteShelf: vi.fn(),
}));

import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useShelves } from "@/hooks/useShelves";
import { deleteShelf } from "@/services/shelfService";

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

describe("useShelfGridOperations", () => {
  let mockUpdateShelf: ReturnType<typeof vi.fn>;
  let mockCreateShelf: ReturnType<typeof vi.fn>;
  let mockRefreshContext: ReturnType<typeof vi.fn>;
  let shelfDataUpdateRef: React.RefObject<{
    updateShelf: (shelfId: number, shelfData: Partial<Shelf>) => void;
    updateCover: (shelfId: number) => void;
  }>;
  let onShelvesDeleted: ReturnType<typeof vi.fn<(shelfIds: number[]) => void>>;
  let onError: ReturnType<typeof vi.fn<(error: Error) => void>>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockUpdateShelf = vi.fn().mockResolvedValue(undefined);
    mockCreateShelf = vi.fn();
    mockRefreshContext = vi.fn().mockResolvedValue(undefined);

    vi.mocked(deleteShelf).mockReset();
    vi.mocked(deleteShelf).mockResolvedValue(undefined);

    vi.mocked(useShelves).mockReturnValue({
      shelves: [],
      isLoading: false,
      error: null,
      createShelf: mockCreateShelf,
      updateShelf: mockUpdateShelf,
      deleteShelf: vi.fn(),
      refresh: vi.fn(),
    } as ReturnType<typeof useShelves>);

    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [],
      isLoading: false,
      error: null,
      refresh: mockRefreshContext,
    } as ReturnType<typeof useShelvesContext>);

    shelfDataUpdateRef = {
      current: {
        updateShelf: vi.fn(),
        updateCover: vi.fn(),
      },
    };

    onShelvesDeleted = vi.fn<(shelfIds: number[]) => void>();
    onError = vi.fn<(error: Error) => void>();
  });

  it("should update shelf and refresh context", async () => {
    const shelf = createMockShelf(1);
    const updatedShelf = {
      ...shelf,
      name: "Updated Shelf",
      description: "Updated description",
      is_public: true,
    };

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    await result.current.handleShelfUpdate(updatedShelf);

    expect(mockUpdateShelf).toHaveBeenCalledWith(1, {
      name: "Updated Shelf",
      description: "Updated description",
      is_public: true,
    });
    expect(mockRefreshContext).toHaveBeenCalled();
    expect(shelfDataUpdateRef.current?.updateShelf).toHaveBeenCalledWith(1, {
      name: "Updated Shelf",
      description: "Updated description",
      is_public: true,
    });
  });

  it("should update cover with updated shelf data", () => {
    const shelf = createMockShelf(1);
    const updatedShelf = {
      ...shelf,
      cover_picture: "new-cover.jpg",
    };

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    result.current.handleCoverUpdate(1, updatedShelf);

    expect(shelfDataUpdateRef.current?.updateShelf).toHaveBeenCalledWith(1, {
      cover_picture: "new-cover.jpg",
    });
    expect(shelfDataUpdateRef.current?.updateCover).not.toHaveBeenCalled();
  });

  it("should update cover with cache-busting when updatedShelf is not provided", () => {
    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    result.current.handleCoverUpdate(1);

    expect(shelfDataUpdateRef.current?.updateCover).toHaveBeenCalledWith(1);
    expect(shelfDataUpdateRef.current?.updateShelf).not.toHaveBeenCalled();
  });

  it("should delete single shelf", async () => {
    const shelfId = 1;
    vi.mocked(deleteShelf).mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    await result.current.handleShelfDelete(shelfId);

    expect(deleteShelf).toHaveBeenCalledWith(1);
    expect(onShelvesDeleted).toHaveBeenCalledWith([1]);
    expect(mockRefreshContext).toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it("should delete multiple shelves", async () => {
    const shelfIds = [1, 2, 3];
    vi.mocked(deleteShelf).mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    await result.current.handleShelfDelete(shelfIds);

    expect(deleteShelf).toHaveBeenCalledTimes(3);
    expect(deleteShelf).toHaveBeenCalledWith(1);
    expect(deleteShelf).toHaveBeenCalledWith(2);
    expect(deleteShelf).toHaveBeenCalledWith(3);
    expect(onShelvesDeleted).toHaveBeenCalledWith([1, 2, 3]);
    expect(mockRefreshContext).toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it("should handle delete error with Error instance", async () => {
    const shelfId = 1;
    const error = new Error("Delete failed");
    vi.mocked(deleteShelf).mockRejectedValue(error);

    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    await expect(result.current.handleShelfDelete(shelfId)).rejects.toThrow(
      "Delete failed",
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      "Failed to delete shelf(s):",
      error,
    );
    expect(onError).toHaveBeenCalledWith(error);
    expect(onShelvesDeleted).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it("should handle delete error with non-Error value", async () => {
    const shelfId = 1;
    const errorValue = "String error";
    vi.mocked(deleteShelf).mockRejectedValue(errorValue);

    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    await expect(result.current.handleShelfDelete(shelfId)).rejects.toEqual(
      expect.any(Error),
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      "Failed to delete shelf(s):",
      expect.any(Error),
    );
    expect(onError).toHaveBeenCalledWith(expect.any(Error));
    expect(onShelvesDeleted).not.toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it("should create shelf and refresh context", async () => {
    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "New description",
      is_public: false,
    };
    const newShelf = createMockShelf(1);
    mockCreateShelf.mockResolvedValue(newShelf);

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    const createdShelf = await result.current.handleCreateShelf(shelfData);

    expect(mockCreateShelf).toHaveBeenCalledWith(shelfData);
    expect(mockRefreshContext).toHaveBeenCalled();
    expect(createdShelf).toEqual(newShelf);
  });

  it("should handle ShelfUpdate data for create", async () => {
    const shelfData: ShelfUpdate = {
      name: "New Shelf",
      description: "New description",
      is_public: false,
    };
    const newShelf = createMockShelf(1);
    mockCreateShelf.mockResolvedValue(newShelf);

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    const createdShelf = await result.current.handleCreateShelf(shelfData);

    expect(mockCreateShelf).toHaveBeenCalledWith(shelfData);
    expect(createdShelf).toEqual(newShelf);
  });

  it("should work without onShelvesDeleted callback", async () => {
    const shelfId = 1;
    vi.mocked(deleteShelf).mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onError,
      }),
    );

    await result.current.handleShelfDelete(shelfId);

    expect(deleteShelf).toHaveBeenCalledWith(1);
    expect(mockRefreshContext).toHaveBeenCalled();
    // Should not throw even if callback is undefined
    expect(true).toBe(true);
  });

  it("should work without onError callback", async () => {
    const shelfId = 1;
    const error = new Error("Delete failed");
    vi.mocked(deleteShelf).mockRejectedValue(error);

    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
      }),
    );

    await expect(result.current.handleShelfDelete(shelfId)).rejects.toThrow(
      "Delete failed",
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      "Failed to delete shelf(s):",
      error,
    );

    consoleSpy.mockRestore();
  });

  it("should handle null shelfDataUpdateRef.current", async () => {
    const shelf = createMockShelf(1);
    const updatedShelf = {
      ...shelf,
      name: "Updated Shelf",
    };
    shelfDataUpdateRef.current =
      undefined as unknown as typeof shelfDataUpdateRef.current;

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    await result.current.handleShelfUpdate(updatedShelf);

    expect(mockUpdateShelf).toHaveBeenCalled();
    expect(mockRefreshContext).toHaveBeenCalled();
    // Should not throw when ref.current is null
    expect(true).toBe(true);
  });

  it("should handle null shelfDataUpdateRef.current for cover update", () => {
    const updatedShelf = createMockShelf(1);
    shelfDataUpdateRef.current =
      undefined as unknown as typeof shelfDataUpdateRef.current;

    const { result } = renderHook(() =>
      useShelfGridOperations({
        shelfDataUpdateRef,
        onShelvesDeleted,
        onError,
      }),
    );

    result.current.handleCoverUpdate(1, updatedShelf);

    // Should not throw when ref.current is null
    expect(true).toBe(true);
  });
});
