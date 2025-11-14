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
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";
import { useShelfEditModal } from "./useShelfEditModal";

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

describe("useShelfEditModal", () => {
  let shelf: Shelf;
  let onEdit: ReturnType<typeof vi.fn>;
  let onShelfUpdate: ReturnType<typeof vi.fn>;
  let onCoverUpdate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    shelf = createMockShelf(1);
    onEdit = vi.fn();
    onShelfUpdate = vi.fn().mockResolvedValue(undefined);
    onCoverUpdate = vi.fn();
  });

  it("should initialize with modal closed", () => {
    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
      }),
    );

    expect(result.current.showEditModal).toBe(false);
  });

  it("should open modal when openEditModal is called", () => {
    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
      }),
    );

    act(() => {
      result.current.openEditModal();
    });

    expect(result.current.showEditModal).toBe(true);
  });

  it("should close modal when closeEditModal is called", () => {
    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
      }),
    );

    act(() => {
      result.current.openEditModal();
    });

    expect(result.current.showEditModal).toBe(true);

    act(() => {
      result.current.closeEditModal();
    });

    expect(result.current.showEditModal).toBe(false);
  });

  it("should call onEdit when provided and handleEditClick is called", () => {
    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
        onEdit,
      }),
    );

    act(() => {
      result.current.handleEditClick();
    });

    expect(onEdit).toHaveBeenCalledWith(1);
    expect(result.current.showEditModal).toBe(false);
  });

  it("should open modal when onEdit is not provided and handleEditClick is called", () => {
    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
      }),
    );

    act(() => {
      result.current.handleEditClick();
    });

    expect(onEdit).not.toHaveBeenCalled();
    expect(result.current.showEditModal).toBe(true);
  });

  it("should update shelf and close modal when handleShelfSave is called with onShelfUpdate", async () => {
    const updateData: ShelfUpdate = {
      name: "Updated Shelf",
      description: "Updated description",
      is_public: true,
    };
    const updatedShelf = { ...shelf, ...updateData };

    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
        onShelfUpdate,
      }),
    );

    act(() => {
      result.current.openEditModal();
    });

    expect(result.current.showEditModal).toBe(true);

    let savedShelf: Shelf | undefined;
    await act(async () => {
      savedShelf = await result.current.handleShelfSave(updateData);
    });

    expect(onShelfUpdate).toHaveBeenCalledWith(updatedShelf);
    expect(result.current.showEditModal).toBe(false);
    expect(savedShelf).toBeDefined();
    expect(savedShelf).toEqual(updatedShelf);
  });

  it("should close modal and return shelf when handleShelfSave is called without onShelfUpdate", async () => {
    const updateData: ShelfUpdate = {
      name: "Updated Shelf",
    };

    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
      }),
    );

    act(() => {
      result.current.openEditModal();
    });

    expect(result.current.showEditModal).toBe(true);

    let savedShelf: Shelf | undefined;
    await act(async () => {
      savedShelf = await result.current.handleShelfSave(updateData);
    });

    expect(onShelfUpdate).not.toHaveBeenCalled();
    expect(result.current.showEditModal).toBe(false);
    expect(savedShelf).toBeDefined();
    expect(savedShelf).toEqual(shelf);
  });

  it("should handle ShelfCreate data", async () => {
    const createData: ShelfCreate = {
      name: "New Shelf",
      description: "New description",
      is_public: false,
    };
    const updatedShelf = { ...shelf, ...createData };

    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
        onShelfUpdate,
      }),
    );

    act(() => {
      result.current.openEditModal();
    });

    let savedShelf: Shelf | undefined;
    await act(async () => {
      savedShelf = await result.current.handleShelfSave(createData);
    });

    expect(onShelfUpdate).toHaveBeenCalledWith(updatedShelf);
    expect(savedShelf).toBeDefined();
    expect(savedShelf).toEqual(updatedShelf);
  });

  it("should call onCoverUpdate when handleCoverSaved is called", () => {
    const updatedShelf = { ...shelf, cover_picture: "new-cover.jpg" };

    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
        onCoverUpdate,
      }),
    );

    act(() => {
      result.current.handleCoverSaved(updatedShelf);
    });

    expect(onCoverUpdate).toHaveBeenCalledWith(1, updatedShelf);
  });

  it("should not throw when onCoverUpdate is not provided and handleCoverSaved is called", () => {
    const updatedShelf = { ...shelf, cover_picture: "new-cover.jpg" };

    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
      }),
    );

    act(() => {
      result.current.handleCoverSaved(updatedShelf);
    });

    // Should not throw
    expect(true).toBe(true);
  });

  it("should call onCoverUpdate when handleCoverDeleted is called", () => {
    const updatedShelf = { ...shelf, cover_picture: null };

    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
        onCoverUpdate,
      }),
    );

    act(() => {
      result.current.handleCoverDeleted(updatedShelf);
    });

    expect(onCoverUpdate).toHaveBeenCalledWith(1, updatedShelf);
  });

  it("should not throw when onCoverUpdate is not provided and handleCoverDeleted is called", () => {
    const updatedShelf = { ...shelf, cover_picture: null };

    const { result } = renderHook(() =>
      useShelfEditModal({
        shelf,
      }),
    );

    act(() => {
      result.current.handleCoverDeleted(updatedShelf);
    });

    // Should not throw
    expect(true).toBe(true);
  });

  it("should update when shelf prop changes", () => {
    const { result, rerender } = renderHook(
      ({ shelf }) =>
        useShelfEditModal({
          shelf,
        }),
      { initialProps: { shelf } },
    );

    const newShelf = createMockShelf(2);
    rerender({ shelf: newShelf });

    act(() => {
      result.current.handleEditClick();
    });

    expect(result.current.showEditModal).toBe(true);
  });
});
