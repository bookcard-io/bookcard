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
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Shelf } from "@/types/shelf";
import { useShelfSelection } from "./useShelfSelection";

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

describe("useShelfSelection", () => {
  let onSelectionChange: ReturnType<
    typeof vi.fn<(selectedIds: Set<number>) => void>
  >;

  beforeEach(() => {
    onSelectionChange = vi.fn<(selectedIds: Set<number>) => void>();
  });

  it("should initialize with empty selection", () => {
    const { result } = renderHook(() => useShelfSelection());

    expect(result.current.selectedShelfIds.size).toBe(0);
    expect(result.current.isShelfSelected(1)).toBe(false);
  });

  it("should select shelf when handleShelfSelect is called", () => {
    const shelf = createMockShelf(1);
    const allShelves = [shelf];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() => useShelfSelection());

    act(() => {
      result.current.handleShelfSelect(shelf, allShelves, mockEvent);
    });

    expect(result.current.selectedShelfIds.has(1)).toBe(true);
    expect(result.current.isShelfSelected(1)).toBe(true);
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
  });

  it("should deselect shelf when handleShelfSelect is called on selected shelf", () => {
    const shelf = createMockShelf(1);
    const allShelves = [shelf];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() => useShelfSelection());

    act(() => {
      result.current.handleShelfSelect(shelf, allShelves, mockEvent);
    });

    expect(result.current.isShelfSelected(1)).toBe(true);

    act(() => {
      result.current.handleShelfSelect(shelf, allShelves, mockEvent);
    });

    expect(result.current.selectedShelfIds.has(1)).toBe(false);
    expect(result.current.isShelfSelected(1)).toBe(false);
  });

  it("should handle event without stopPropagation", () => {
    const shelf = createMockShelf(1);
    const allShelves = [shelf];
    const mockEvent = {} as React.MouseEvent;

    const { result } = renderHook(() => useShelfSelection());

    act(() => {
      result.current.handleShelfSelect(shelf, allShelves, mockEvent);
    });

    expect(result.current.isShelfSelected(1)).toBe(true);
    // Should not throw when stopPropagation is not available
    expect(true).toBe(true);
  });

  it("should remove shelves from selection", () => {
    const shelf1 = createMockShelf(1);
    const shelf2 = createMockShelf(2);
    const shelf3 = createMockShelf(3);
    const allShelves = [shelf1, shelf2, shelf3];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() => useShelfSelection());

    act(() => {
      result.current.handleShelfSelect(shelf1, allShelves, mockEvent);
      result.current.handleShelfSelect(shelf2, allShelves, mockEvent);
      result.current.handleShelfSelect(shelf3, allShelves, mockEvent);
    });

    expect(result.current.selectedShelfIds.size).toBe(3);

    act(() => {
      result.current.removeFromSelection([1, 3]);
    });

    expect(result.current.selectedShelfIds.size).toBe(1);
    expect(result.current.isShelfSelected(1)).toBe(false);
    expect(result.current.isShelfSelected(2)).toBe(true);
    expect(result.current.isShelfSelected(3)).toBe(false);
  });

  it("should clear all selections", () => {
    const shelf1 = createMockShelf(1);
    const shelf2 = createMockShelf(2);
    const allShelves = [shelf1, shelf2];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() => useShelfSelection());

    act(() => {
      result.current.handleShelfSelect(shelf1, allShelves, mockEvent);
      result.current.handleShelfSelect(shelf2, allShelves, mockEvent);
    });

    expect(result.current.selectedShelfIds.size).toBe(2);

    act(() => {
      result.current.clearSelection();
    });

    expect(result.current.selectedShelfIds.size).toBe(0);
    expect(result.current.isShelfSelected(1)).toBe(false);
    expect(result.current.isShelfSelected(2)).toBe(false);
  });

  it("should notify parent of selection changes", async () => {
    const shelf = createMockShelf(1);
    const allShelves = [shelf];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() =>
      useShelfSelection({
        onSelectionChange,
      }),
    );

    act(() => {
      result.current.handleShelfSelect(shelf, allShelves, mockEvent);
    });

    await waitFor(() => {
      expect(onSelectionChange).toHaveBeenCalled();
    });

    const lastCall =
      onSelectionChange.mock.calls[
        onSelectionChange.mock.calls.length - 1
      ]?.[0];
    expect(lastCall?.has(1)).toBe(true);
  });

  it("should notify parent when selection is cleared", async () => {
    const shelf = createMockShelf(1);
    const allShelves = [shelf];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() =>
      useShelfSelection({
        onSelectionChange,
      }),
    );

    act(() => {
      result.current.handleShelfSelect(shelf, allShelves, mockEvent);
    });

    await waitFor(() => {
      expect(onSelectionChange).toHaveBeenCalled();
    });

    act(() => {
      result.current.clearSelection();
    });

    await waitFor(() => {
      const lastCall =
        onSelectionChange.mock.calls[
          onSelectionChange.mock.calls.length - 1
        ]?.[0];
      expect(lastCall?.size).toBe(0);
    });
  });

  it("should notify parent when shelves are removed", async () => {
    const shelf1 = createMockShelf(1);
    const shelf2 = createMockShelf(2);
    const allShelves = [shelf1, shelf2];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() =>
      useShelfSelection({
        onSelectionChange,
      }),
    );

    act(() => {
      result.current.handleShelfSelect(shelf1, allShelves, mockEvent);
      result.current.handleShelfSelect(shelf2, allShelves, mockEvent);
    });

    await waitFor(() => {
      expect(onSelectionChange).toHaveBeenCalled();
    });

    act(() => {
      result.current.removeFromSelection([1]);
    });

    await waitFor(() => {
      const lastCall =
        onSelectionChange.mock.calls[
          onSelectionChange.mock.calls.length - 1
        ]?.[0];
      expect(lastCall?.size).toBe(1);
      expect(lastCall?.has(2)).toBe(true);
    });
  });

  it("should work without onSelectionChange callback", () => {
    const shelf = createMockShelf(1);
    const allShelves = [shelf];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() => useShelfSelection());

    act(() => {
      result.current.handleShelfSelect(shelf, allShelves, mockEvent);
    });

    expect(result.current.isShelfSelected(1)).toBe(true);
    // Should not throw when callback is undefined
    expect(true).toBe(true);
  });

  it("should update callback when onSelectionChange changes", async () => {
    const shelf = createMockShelf(1);
    const allShelves = [shelf];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const onSelectionChange1 = vi.fn();
    const onSelectionChange2 = vi.fn();

    const { result, rerender } = renderHook(
      ({ onSelectionChange }) =>
        useShelfSelection({
          onSelectionChange,
        }),
      { initialProps: { onSelectionChange: onSelectionChange1 } },
    );

    act(() => {
      result.current.handleShelfSelect(shelf, allShelves, mockEvent);
    });

    await waitFor(() => {
      expect(onSelectionChange1).toHaveBeenCalled();
    });

    rerender({ onSelectionChange: onSelectionChange2 });

    act(() => {
      result.current.clearSelection();
    });

    await waitFor(() => {
      expect(onSelectionChange2).toHaveBeenCalled();
    });
  });

  it("should handle multiple rapid selections", () => {
    const shelf1 = createMockShelf(1);
    const shelf2 = createMockShelf(2);
    const shelf3 = createMockShelf(3);
    const allShelves = [shelf1, shelf2, shelf3];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() => useShelfSelection());

    act(() => {
      result.current.handleShelfSelect(shelf1, allShelves, mockEvent);
      result.current.handleShelfSelect(shelf2, allShelves, mockEvent);
      result.current.handleShelfSelect(shelf3, allShelves, mockEvent);
      result.current.handleShelfSelect(shelf1, allShelves, mockEvent); // Deselect
    });

    expect(result.current.selectedShelfIds.size).toBe(2);
    expect(result.current.isShelfSelected(1)).toBe(false);
    expect(result.current.isShelfSelected(2)).toBe(true);
    expect(result.current.isShelfSelected(3)).toBe(true);
  });

  it("should handle removing non-existent shelf IDs", () => {
    const shelf1 = createMockShelf(1);
    const allShelves = [shelf1];
    const mockEvent = {
      stopPropagation: vi.fn(),
    } as unknown as React.MouseEvent;

    const { result } = renderHook(() => useShelfSelection());

    act(() => {
      result.current.handleShelfSelect(shelf1, allShelves, mockEvent);
    });

    expect(result.current.selectedShelfIds.size).toBe(1);

    act(() => {
      result.current.removeFromSelection([2, 3]); // Non-existent IDs
    });

    expect(result.current.selectedShelfIds.size).toBe(1);
    expect(result.current.isShelfSelected(1)).toBe(true);
  });
});
