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
import type React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Shelf } from "@/types/shelf";
import { useShelfCardClick } from "./useShelfCardClick";

function createMockShelf(id: number, bookCount: number = 0): Shelf {
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
    book_count: bookCount,
  };
}

describe("useShelfCardClick", () => {
  let onShelfClick: ReturnType<typeof vi.fn<(shelfId: number) => void>>;
  let onTriggerAnimation: ReturnType<typeof vi.fn<() => void>>;

  beforeEach(() => {
    onShelfClick = vi.fn<(shelfId: number) => void>();
    onTriggerAnimation = vi.fn<() => void>();
  });

  it("should trigger animation for empty shelf on click", () => {
    const shelf = createMockShelf(1, 0);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const mockEvent = {
      target: document.createElement("div"),
    } as unknown as React.MouseEvent<Element, MouseEvent>;

    result.current.handleClick(mockEvent);

    expect(onTriggerAnimation).toHaveBeenCalledTimes(1);
    expect(onShelfClick).not.toHaveBeenCalled();
  });

  it("should call onShelfClick for non-empty shelf on click", () => {
    const shelf = createMockShelf(1, 5);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const mockEvent = {
      target: document.createElement("div"),
    } as unknown as React.MouseEvent<Element, MouseEvent>;

    result.current.handleClick(mockEvent);

    expect(onShelfClick).toHaveBeenCalledWith(1);
    expect(onTriggerAnimation).not.toHaveBeenCalled();
  });

  it("should not trigger action when clicking checkbox", () => {
    const shelf = createMockShelf(1, 5);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const checkbox = document.createElement("div");
    checkbox.setAttribute("data-shelf-checkbox", "");
    const mockEvent = {
      target: checkbox,
    } as unknown as React.MouseEvent<Element, MouseEvent>;

    result.current.handleClick(mockEvent);

    expect(onShelfClick).not.toHaveBeenCalled();
    expect(onTriggerAnimation).not.toHaveBeenCalled();
  });

  it("should not trigger action when clicking edit button", () => {
    const shelf = createMockShelf(1, 5);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const editButton = document.createElement("div");
    editButton.setAttribute("data-shelf-edit", "");
    const mockEvent = {
      target: editButton,
    } as unknown as React.MouseEvent<Element, MouseEvent>;

    result.current.handleClick(mockEvent);

    expect(onShelfClick).not.toHaveBeenCalled();
    expect(onTriggerAnimation).not.toHaveBeenCalled();
  });

  it("should not trigger action when clicking menu button", () => {
    const shelf = createMockShelf(1, 5);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const menuButton = document.createElement("div");
    menuButton.setAttribute("data-shelf-menu", "");
    const mockEvent = {
      target: menuButton,
    } as unknown as React.MouseEvent<Element, MouseEvent>;

    result.current.handleClick(mockEvent);

    expect(onShelfClick).not.toHaveBeenCalled();
    expect(onTriggerAnimation).not.toHaveBeenCalled();
  });

  it("should not trigger action when clicking child of checkbox", () => {
    const shelf = createMockShelf(1, 5);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const checkbox = document.createElement("div");
    checkbox.setAttribute("data-shelf-checkbox", "");
    const child = document.createElement("span");
    checkbox.appendChild(child);

    const mockEvent = {
      target: child,
    } as unknown as React.MouseEvent<Element, MouseEvent>;

    // Mock closest to return the checkbox
    vi.spyOn(child, "closest").mockReturnValue(checkbox);

    result.current.handleClick(mockEvent);

    expect(onShelfClick).not.toHaveBeenCalled();
    expect(onTriggerAnimation).not.toHaveBeenCalled();
  });

  it("should trigger animation for empty shelf on Enter key", () => {
    const shelf = createMockShelf(1, 0);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const mockEvent = {
      key: "Enter",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent;

    result.current.handleKeyDown(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(onTriggerAnimation).toHaveBeenCalledTimes(1);
    expect(onShelfClick).not.toHaveBeenCalled();
  });

  it("should trigger animation for empty shelf on Space key", () => {
    const shelf = createMockShelf(1, 0);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const mockEvent = {
      key: " ",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent;

    result.current.handleKeyDown(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(onTriggerAnimation).toHaveBeenCalledTimes(1);
    expect(onShelfClick).not.toHaveBeenCalled();
  });

  it("should call onShelfClick for non-empty shelf on Enter key", () => {
    const shelf = createMockShelf(1, 5);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const mockEvent = {
      key: "Enter",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent;

    result.current.handleKeyDown(mockEvent);

    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(onShelfClick).toHaveBeenCalledWith(1);
    expect(onTriggerAnimation).not.toHaveBeenCalled();
  });

  it("should not trigger action for other keys", () => {
    const shelf = createMockShelf(1, 5);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onShelfClick,
        onTriggerAnimation,
      }),
    );

    const mockEvent = {
      key: "Escape",
      preventDefault: vi.fn(),
    } as unknown as React.KeyboardEvent;

    result.current.handleKeyDown(mockEvent);

    expect(mockEvent.preventDefault).not.toHaveBeenCalled();
    expect(onShelfClick).not.toHaveBeenCalled();
    expect(onTriggerAnimation).not.toHaveBeenCalled();
  });

  it("should work without onShelfClick callback", () => {
    const shelf = createMockShelf(1, 5);
    const { result } = renderHook(() =>
      useShelfCardClick({
        shelf,
        onTriggerAnimation,
      }),
    );

    const mockEvent = {
      target: document.createElement("div"),
    } as unknown as React.MouseEvent<Element, MouseEvent>;

    result.current.handleClick(mockEvent);

    // Should not throw, but also not call anything since shelf has books
    expect(onTriggerAnimation).not.toHaveBeenCalled();
  });

  it("should update behavior when shelf book_count changes", () => {
    const shelf = createMockShelf(1, 0);
    const { result, rerender } = renderHook(
      ({ shelf }) =>
        useShelfCardClick({
          shelf,
          onShelfClick,
          onTriggerAnimation,
        }),
      { initialProps: { shelf } },
    );

    const mockEvent = {
      target: document.createElement("div"),
    } as unknown as React.MouseEvent<Element, MouseEvent>;

    result.current.handleClick(mockEvent);
    expect(onTriggerAnimation).toHaveBeenCalledTimes(1);

    // Update shelf to have books
    const updatedShelf = createMockShelf(1, 5);
    rerender({ shelf: updatedShelf });

    result.current.handleClick(mockEvent);
    expect(onShelfClick).toHaveBeenCalledWith(1);
    expect(onTriggerAnimation).toHaveBeenCalledTimes(1); // Still 1, not 2
  });
});
