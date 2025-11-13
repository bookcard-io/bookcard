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
import type React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useFlyoutPosition } from "./useFlyoutPosition";

/**
 * Creates a mock element with getBoundingClientRect.
 *
 * Parameters
 * ----------
 * rect : DOMRect
 *     Bounding rectangle.
 *
 * Returns
 * -------
 * HTMLDivElement
 *     Mock element.
 */
function createMockElement(rect: DOMRect): HTMLDivElement {
  const element = document.createElement("div");
  element.getBoundingClientRect = vi.fn(() => rect);
  return element;
}

describe("useFlyoutPosition", () => {
  let mockAddEventListener: ReturnType<typeof vi.fn>;
  let mockRemoveEventListener: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockAddEventListener = vi.fn();
    mockRemoveEventListener = vi.fn();

    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1000,
    });
    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: 800,
    });

    Object.defineProperty(window, "addEventListener", {
      writable: true,
      configurable: true,
      value: mockAddEventListener,
    });
    Object.defineProperty(window, "removeEventListener", {
      writable: true,
      configurable: true,
      value: mockRemoveEventListener,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should return default position when not open", () => {
    const parentItemRef = { current: document.createElement("div") };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: false,
        parentItemRef,
        mounted: true,
      }),
    );

    expect(result.current.position).toEqual({ top: 0 });
    expect(result.current.direction).toBe("right");
    expect(result.current.menuRef).toBeDefined();
  });

  it("should return default position when parent ref is null", () => {
    const parentItemRef = { current: null };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    expect(result.current.position).toEqual({ top: 0 });
    expect(result.current.direction).toBe("right");
  });

  it("should return default position when not mounted", () => {
    const parentItemRef = { current: document.createElement("div") };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: false,
      }),
    );

    expect(result.current.position).toEqual({ top: 0 });
    expect(result.current.direction).toBe("right");
  });

  it("should calculate position flying right when space available", () => {
    const parentRect = new DOMRect(100, 100, 150, 50);
    const menuRect = new DOMRect(0, 0, 200, 300);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    result.current.menuRef.current = menuEl;

    // Trigger position update manually
    const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
    if (!updatePosition) {
      throw new Error("updatePosition not found");
    }
    act(() => {
      updatePosition();
    });

    expect(result.current.direction).toBe("right");
    expect(result.current.position.top).toBe(100);
    expect(result.current.position.left).toBe(250 - 2);
    expect(result.current.position.right).toBeUndefined();
  });

  it("should calculate position flying left when space on right is insufficient", () => {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 400,
    });

    const parentRect = new DOMRect(250, 100, 150, 50);
    const menuRect = new DOMRect(0, 0, 200, 300);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    result.current.menuRef.current = menuEl;

    // Trigger position update manually
    const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
    if (!updatePosition) {
      throw new Error("updatePosition not found");
    }
    act(() => {
      updatePosition();
    });

    expect(result.current.direction).toBe("left");
    expect(result.current.position.top).toBe(100);
    expect(result.current.position.right).toBe(400 - 250 - 2);
    expect(result.current.position.left).toBeUndefined();
  });

  it("should adjust top position when menu would overflow bottom", () => {
    const parentRect = new DOMRect(100, 700, 150, 50);
    const menuRect = new DOMRect(0, 0, 200, 300);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    result.current.menuRef.current = menuEl;

    // Trigger position update manually
    const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
    if (!updatePosition) {
      throw new Error("updatePosition not found");
    }
    act(() => {
      updatePosition();
    });

    expect(result.current.position.top).toBe(750 - 300);
  });

  it("should not adjust top position below 0 when overflowing", () => {
    const parentRect = new DOMRect(100, 50, 150, 50);
    const menuRect = new DOMRect(0, 0, 200, 800);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    result.current.menuRef.current = menuEl;

    // Trigger position update manually
    const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
    if (!updatePosition) {
      throw new Error("updatePosition not found");
    }
    act(() => {
      updatePosition();
    });

    expect(result.current.position.top).toBe(0);
  });

  it("should set up scroll and resize listeners when open", () => {
    const parentItemRef = { current: document.createElement("div") };

    renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    expect(mockAddEventListener).toHaveBeenCalledWith(
      "scroll",
      expect.any(Function),
      true,
    );
    expect(mockAddEventListener).toHaveBeenCalledWith(
      "resize",
      expect.any(Function),
    );
  });

  it("should remove scroll and resize listeners on cleanup", () => {
    const parentItemRef = { current: document.createElement("div") };

    const { unmount } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
    if (!updatePosition) {
      throw new Error("updatePosition not found");
    }

    unmount();

    expect(mockRemoveEventListener).toHaveBeenCalledWith(
      "scroll",
      updatePosition,
      true,
    );
    expect(mockRemoveEventListener).toHaveBeenCalledWith(
      "resize",
      updatePosition,
    );
  });

  it("should update position on scroll", () => {
    const parentRect = new DOMRect(100, 100, 150, 50);
    const menuRect = new DOMRect(0, 0, 200, 300);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    result.current.menuRef.current = menuEl;

    const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
    if (!updatePosition) {
      throw new Error("updatePosition not found");
    }

    const newParentRect = new DOMRect(200, 200, 150, 50);
    parentEl.getBoundingClientRect = vi.fn(() => newParentRect);

    act(() => {
      updatePosition();
    });

    expect(result.current.position.top).toBe(200);
  });

  it("should update position on resize", () => {
    const parentRect = new DOMRect(250, 100, 150, 50);
    const menuRect = new DOMRect(0, 0, 200, 300);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    result.current.menuRef.current = menuEl;

    // Initial position should be right
    const updatePosition1 = mockAddEventListener.mock.calls[0]?.[1];
    if (!updatePosition1) {
      throw new Error("updatePosition1 not found");
    }
    act(() => {
      updatePosition1();
    });
    expect(result.current.direction).toBe("right");

    // Resize viewport to be smaller
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 300,
    });

    const updatePosition2 = mockAddEventListener.mock.calls[1]?.[1];
    if (!updatePosition2) {
      throw new Error("updatePosition2 not found");
    }
    act(() => {
      updatePosition2();
    });

    expect(result.current.direction).toBe("left");
  });

  it("should not update position when menu ref is null", () => {
    const parentRect = new DOMRect(100, 100, 150, 50);
    const parentEl = createMockElement(parentRect);
    const parentItemRef = { current: parentEl };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    result.current.menuRef.current = null;

    const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
    if (updatePosition) {
      updatePosition();
    }

    expect(result.current.position.top).toBe(0);
  });

  it("should not update position when parent ref becomes null", () => {
    const parentRect = new DOMRect(100, 100, 150, 50);
    const menuRect = new DOMRect(0, 0, 200, 300);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef: React.RefObject<HTMLElement | null> = {
      current: parentEl,
    };

    const { result } = renderHook(() =>
      useFlyoutPosition({
        isOpen: true,
        parentItemRef,
        mounted: true,
      }),
    );

    result.current.menuRef.current = menuEl;
    parentItemRef.current = null;

    const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
    if (updatePosition) {
      updatePosition();
    }

    expect(result.current.position.top).toBe(0);
  });

  it.each([
    {
      expectedDirection: "right",
    },
    {
      expectedDirection: "right",
    },
    {
      expectedDirection: "left",
      viewportWidth: 400,
      parentLeft: 250,
    },
  ])(
    "should choose direction based on available space",
    ({ expectedDirection, viewportWidth, parentLeft }) => {
      if (viewportWidth !== undefined && parentLeft !== undefined) {
        Object.defineProperty(window, "innerWidth", {
          writable: true,
          configurable: true,
          value: viewportWidth,
        });
      }

      const parentRect = new DOMRect(parentLeft ?? 100, 100, 150, 50);
      const menuRect = new DOMRect(0, 0, 200, 300);
      const parentEl = createMockElement(parentRect);
      const menuEl = createMockElement(menuRect);
      const parentItemRef = { current: parentEl };

      const { result } = renderHook(() =>
        useFlyoutPosition({
          isOpen: true,
          parentItemRef,
          mounted: true,
        }),
      );

      result.current.menuRef.current = menuEl;

      // Trigger position update manually
      const updatePosition = mockAddEventListener.mock.calls[0]?.[1];
      if (!updatePosition) {
        throw new Error("updatePosition not found");
      }
      act(() => {
        updatePosition();
      });

      expect(result.current.direction).toBe(expectedDirection);
    },
  );
});
