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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useFlyoutIntent } from "./useFlyoutIntent";

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
 * HTMLElement
 *     Mock element.
 */
function createMockElement(rect: DOMRect): HTMLElement {
  const element = document.createElement("div");
  element.getBoundingClientRect = vi.fn(() => rect);
  return element;
}

/**
 * Creates a mock PointerEvent.
 *
 * Parameters
 * ----------
 * clientX : number
 *     X coordinate.
 * clientY : number
 *     Y coordinate.
 *
 * Returns
 * -------
 * PointerEvent
 *     Mock pointer event.
 */
function createPointerEvent(clientX: number, clientY: number): PointerEvent {
  return new PointerEvent("pointermove", {
    clientX,
    clientY,
    bubbles: true,
  });
}

describe("useFlyoutIntent", () => {
  let mockRequestAnimationFrame: ReturnType<typeof vi.fn>;
  let mockCancelAnimationFrame: ReturnType<typeof vi.fn>;
  let mockAddEventListener: ReturnType<typeof vi.fn>;
  let mockRemoveEventListener: ReturnType<typeof vi.fn>;
  let rafCallbacks: Array<() => void>;

  beforeEach(() => {
    rafCallbacks = [];
    mockRequestAnimationFrame = vi.fn((callback: () => void) => {
      rafCallbacks.push(callback);
      callback();
      return 1;
    });
    mockCancelAnimationFrame = vi.fn();
    mockAddEventListener = vi.fn();
    mockRemoveEventListener = vi.fn();

    Object.defineProperty(window, "requestAnimationFrame", {
      writable: true,
      configurable: true,
      value: mockRequestAnimationFrame,
    });
    Object.defineProperty(window, "cancelAnimationFrame", {
      writable: true,
      configurable: true,
      value: mockCancelAnimationFrame,
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

  it("should not set up listeners when isOpen is false", () => {
    const parentItemRef = { current: null };
    const menuRef = { current: null };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: false,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    expect(mockAddEventListener).not.toHaveBeenCalled();
  });

  it("should set up event listeners when isOpen is true", () => {
    const parentItemRef = { current: document.createElement("div") };
    const menuRef = { current: document.createElement("div") };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    expect(mockAddEventListener).toHaveBeenCalledWith(
      "pointermove",
      expect.any(Function),
      { passive: true },
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

  it("should remove event listeners on cleanup", () => {
    const parentItemRef = { current: document.createElement("div") };
    const menuRef = { current: document.createElement("div") };
    const onClose = vi.fn();

    const { unmount } = renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];

    unmount();

    expect(mockRemoveEventListener).toHaveBeenCalledWith(
      "pointermove",
      handlePointerMove,
      { passive: true },
    );
    expect(mockRemoveEventListener).toHaveBeenCalledWith(
      "scroll",
      handlePointerMove,
      true,
    );
    expect(mockRemoveEventListener).toHaveBeenCalledWith(
      "resize",
      handlePointerMove,
    );
  });

  it("should cancel animation frame on cleanup if pending", () => {
    const parentItemRef = { current: document.createElement("div") };
    const menuRef = { current: document.createElement("div") };
    const onClose = vi.fn();

    const rafId = 123;
    mockRequestAnimationFrame.mockImplementation(() => {
      return rafId;
    });

    const { unmount } = renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    // Trigger a pointer move to set up the RAF
    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    const event = createPointerEvent(50, 50);
    handlePointerMove(event);

    unmount();

    expect(mockCancelAnimationFrame).toHaveBeenCalledWith(123);
  });

  it.each([
    { x: 50, y: 50, inside: true },
    { x: 40, y: 40, inside: true },
    { x: 110, y: 110, inside: true },
    { x: 5, y: 5, inside: false },
    { x: 165, y: 115, inside: false },
    { x: 60, y: 35, inside: false },
    { x: 60, y: 115, inside: false },
  ])("should call onClose when pointer is outside padded union (x: $x, y: $y)", ({
    x,
    y,
    inside,
  }) => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
        padding: 10,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;
    const event = createPointerEvent(x, y);
    handlePointerMove(event);

    if (inside) {
      expect(onClose).not.toHaveBeenCalled();
    } else {
      expect(onClose).toHaveBeenCalled();
    }
  });

  it("should use default padding of 10", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;
    const event = createPointerEvent(5, 5);
    handlePointerMove(event);

    expect(onClose).toHaveBeenCalled();
  });

  it("should use custom padding", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
        padding: 20,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;
    // With padding 20, union is (30, 30) to (170, 120). Point (30, 30) is on the boundary, so inside
    const event = createPointerEvent(30, 30);
    handlePointerMove(event);

    expect(onClose).not.toHaveBeenCalled();
  });

  it("should call onClose when parent element is null", () => {
    const menuEl = createMockElement(new DOMRect(100, 50, 50, 50));
    const parentItemRef = { current: null };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    const event = createPointerEvent(50, 50);
    handlePointerMove(event);

    expect(onClose).toHaveBeenCalled();
  });

  it("should call onClose when menu element is null", () => {
    const parentEl = createMockElement(new DOMRect(50, 50, 50, 50));
    const parentItemRef = { current: parentEl };
    const menuRef = { current: null };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;
    const event = createPointerEvent(50, 50);
    handlePointerMove(event);

    expect(onClose).toHaveBeenCalled();
  });

  it("should not process non-PointerEvent events", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;
    const event = new Event("scroll");
    handlePointerMove(event);

    expect(onClose).not.toHaveBeenCalled();
  });

  it("should queue pointer events and process in requestAnimationFrame", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    const rafCallbacks: Array<() => void> = [];
    mockRequestAnimationFrame.mockImplementation((callback: () => void) => {
      rafCallbacks.push(callback);
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;
    const event1 = createPointerEvent(5, 5);
    const event2 = createPointerEvent(60, 60);

    handlePointerMove(event1);
    expect(onClose).not.toHaveBeenCalled();

    handlePointerMove(event2);
    expect(onClose).not.toHaveBeenCalled();

    for (const cb of rafCallbacks) {
      cb();
    }

    expect(onClose).not.toHaveBeenCalled();
  });

  it("should close when pointer is stationary outside parent and menu", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    const rafCallbacks: Array<() => void> = [];
    mockRequestAnimationFrame.mockImplementation((callback: () => void) => {
      rafCallbacks.push(callback);
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
        minMovementPx: 10,
        idleTimeMs: 100,
        padding: 10,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;

    // First event - inside corridor but outside parent and menu
    // Corridor: (40, 40) to (160, 110)
    // Parent: (50, 50) to (100, 100), Menu: (100, 50) to (150, 100)
    // Point (45, 80) is inside corridor, left of parent, outside both
    const event1 = createPointerEvent(45, 80);
    Object.defineProperty(event1, "timeStamp", { value: 1000, writable: true });
    handlePointerMove(event1);

    // Process RAF callbacks
    for (const cb of rafCallbacks) {
      cb();
    }
    rafCallbacks.length = 0;

    expect(onClose).not.toHaveBeenCalled(); // Not stationary yet

    // Second event - still outside, but stationary (small movement, enough time)
    const event2 = createPointerEvent(47, 82); // Small movement (< 10px)
    Object.defineProperty(event2, "timeStamp", {
      value: 1200, // 200ms later (>= 100ms)
      writable: true,
    });
    handlePointerMove(event2);

    // Process RAF callbacks
    for (const cb of rafCallbacks) {
      cb();
    }

    expect(onClose).toHaveBeenCalled();
  });

  it("should not close when pointer is moving with intent", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    const rafCallbacks: Array<() => void> = [];
    mockRequestAnimationFrame.mockImplementation((callback: () => void) => {
      rafCallbacks.push(callback);
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
        minMovementPx: 10,
        idleTimeMs: 100,
        padding: 10,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;

    // First event - inside corridor but outside parent and menu
    const event1 = createPointerEvent(45, 80);
    Object.defineProperty(event1, "timeStamp", { value: 1000, writable: true });
    handlePointerMove(event1);

    // Process RAF callbacks
    for (const cb of rafCallbacks) {
      cb();
    }
    rafCallbacks.length = 0;

    // Second event - moving with intent (large movement)
    const event2 = createPointerEvent(60, 80); // Large movement (>= 10px)
    Object.defineProperty(event2, "timeStamp", {
      value: 1200,
      writable: true,
    });
    handlePointerMove(event2);

    // Process RAF callbacks
    for (const cb of rafCallbacks) {
      cb();
    }

    expect(onClose).not.toHaveBeenCalled(); // Moving with intent
  });

  it("should not close when pointer is stationary but not enough time passed", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    const rafCallbacks: Array<() => void> = [];
    mockRequestAnimationFrame.mockImplementation((callback: () => void) => {
      rafCallbacks.push(callback);
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
        minMovementPx: 10,
        idleTimeMs: 100,
        padding: 10,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;

    // First event - inside corridor but outside parent and menu
    const event1 = createPointerEvent(45, 80);
    Object.defineProperty(event1, "timeStamp", { value: 1000, writable: true });
    handlePointerMove(event1);

    // Process RAF callbacks
    for (const cb of rafCallbacks) {
      cb();
    }
    rafCallbacks.length = 0;

    // Second event - stationary but not enough time (< 100ms)
    const event2 = createPointerEvent(47, 82);
    Object.defineProperty(event2, "timeStamp", {
      value: 1050, // Only 50ms later (< 100ms)
      writable: true,
    });
    handlePointerMove(event2);

    // Process RAF callbacks
    for (const cb of rafCallbacks) {
      cb();
    }

    expect(onClose).not.toHaveBeenCalled(); // Not enough time passed
  });

  it("should not close when pointer is inside parent", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    const rafCallbacks: Array<() => void> = [];
    mockRequestAnimationFrame.mockImplementation((callback: () => void) => {
      rafCallbacks.push(callback);
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
        minMovementPx: 10,
        idleTimeMs: 100,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;

    // Event inside parent
    const event = createPointerEvent(75, 75); // Inside parent rect
    Object.defineProperty(event, "timeStamp", { value: 1000, writable: true });
    handlePointerMove(event);

    // Process RAF callbacks
    for (const cb of rafCallbacks) {
      cb();
    }

    expect(onClose).not.toHaveBeenCalled(); // Inside parent
  });

  it("should not close when pointer is inside menu", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    const rafCallbacks: Array<() => void> = [];
    mockRequestAnimationFrame.mockImplementation((callback: () => void) => {
      rafCallbacks.push(callback);
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
        minMovementPx: 10,
        idleTimeMs: 100,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;

    // Event inside menu
    const event = createPointerEvent(125, 75); // Inside menu rect
    Object.defineProperty(event, "timeStamp", { value: 1000, writable: true });
    handlePointerMove(event);

    // Process RAF callbacks
    for (const cb of rafCallbacks) {
      cb();
    }

    expect(onClose).not.toHaveBeenCalled(); // Inside menu
  });

  it("should reset lastEventRef when closing due to stationary detection", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    const rafCallbacks: Array<() => void> = [];
    mockRequestAnimationFrame.mockImplementation((callback: () => void) => {
      rafCallbacks.push(callback);
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
        minMovementPx: 10,
        idleTimeMs: 100,
        padding: 10,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;

    // First event - inside corridor but outside parent and menu
    const event1 = createPointerEvent(45, 80);
    Object.defineProperty(event1, "timeStamp", { value: 1000, writable: true });
    handlePointerMove(event1);

    for (const cb of rafCallbacks) {
      cb();
    }
    rafCallbacks.length = 0;

    // Second event - stationary
    const event2 = createPointerEvent(47, 82);
    Object.defineProperty(event2, "timeStamp", {
      value: 1200,
      writable: true,
    });
    handlePointerMove(event2);

    for (const cb of rafCallbacks) {
      cb();
    }

    expect(onClose).toHaveBeenCalledTimes(1);

    // Third event after close - should not trigger again immediately
    // Since lastEventRef was reset, this should not trigger close
    const event3 = createPointerEvent(49, 84);
    Object.defineProperty(event3, "timeStamp", {
      value: 1300,
      writable: true,
    });
    handlePointerMove(event3);

    rafCallbacks.length = 0;
    for (const cb of rafCallbacks) {
      cb();
    }

    // Should only be called once (from previous stationary detection)
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("should skip processing if requestAnimationFrame is already pending", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    mockRequestAnimationFrame.mockImplementation(() => {
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;
    const event1 = createPointerEvent(5, 5);
    const event2 = createPointerEvent(10, 10);

    handlePointerMove(event1);
    handlePointerMove(event2);

    expect(mockRequestAnimationFrame).toHaveBeenCalledTimes(1);
  });

  it("should handle scroll events", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[1]?.[1];
    if (!handlePointerMove) return;
    const scrollEvent = new Event("scroll");
    handlePointerMove(scrollEvent);

    expect(mockRequestAnimationFrame).toHaveBeenCalled();
  });

  it("should handle resize events", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[2]?.[1];
    if (!handlePointerMove) return;
    const resizeEvent = new Event("resize");
    handlePointerMove(resizeEvent);

    expect(mockRequestAnimationFrame).toHaveBeenCalled();
  });

  it("should not call onClose when pending event is null", () => {
    const parentRect = new DOMRect(50, 50, 50, 50);
    const menuRect = new DOMRect(100, 50, 50, 50);
    const parentEl = createMockElement(parentRect);
    const menuEl = createMockElement(menuRect);
    const parentItemRef = { current: parentEl };
    const menuRef = { current: menuEl };
    const onClose = vi.fn();

    const rafCallbacks: Array<() => void> = [];
    mockRequestAnimationFrame.mockImplementation((callback: () => void) => {
      rafCallbacks.push(callback);
      return 1;
    });

    renderHook(() =>
      useFlyoutIntent({
        isOpen: true,
        parentItemRef,
        menuRef,
        onClose,
      }),
    );

    const handlePointerMove = mockAddEventListener.mock.calls[0]?.[1];
    if (!handlePointerMove) return;
    const scrollEvent = new Event("scroll");
    handlePointerMove(scrollEvent);

    for (const cb of rafCallbacks) {
      cb();
    }

    expect(onClose).not.toHaveBeenCalled();
  });
});
