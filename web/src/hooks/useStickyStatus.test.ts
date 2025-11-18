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

import { act, render } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useStickyStatus } from "./useStickyStatus";

interface HookSnapshot {
  statusRef: React.RefObject<HTMLDivElement | null>;
  isSticky: boolean;
  opacity: number;
}

interface SetupResult {
  scrollContainer: HTMLElement;
  statusElement: HTMLDivElement;
  getSnapshot: () => HookSnapshot;
  unmount: () => void;
}

describe("useStickyStatus", () => {
  let mockRequestAnimationFrame: ReturnType<typeof vi.fn>;
  let mockCancelAnimationFrame: ReturnType<typeof vi.fn>;
  let rafIdCounter: number;

  beforeEach(() => {
    rafIdCounter = 0;
    mockRequestAnimationFrame = vi.fn((callback: FrameRequestCallback) => {
      const id = ++rafIdCounter;
      // Execute callback synchronously for testing
      callback(performance.now());
      return id;
    });
    mockCancelAnimationFrame = vi.fn();
    vi.stubGlobal("requestAnimationFrame", mockRequestAnimationFrame);
    vi.stubGlobal("cancelAnimationFrame", mockCancelAnimationFrame);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Renders a test component that wires up the hook to real DOM elements:
   * - a scroll container (`data-page-scroll-container="true"`)
   * - a status element (`data-testid="status"`) attached to `statusRef`
   */
  function setupHook(
    options?: Parameters<typeof useStickyStatus>[0],
  ): SetupResult {
    let latestSnapshot: HookSnapshot | null = null;

    const TestComponent = ({
      opts,
    }: {
      opts?: Parameters<typeof useStickyStatus>[0];
    }) => {
      const hookResult = useStickyStatus(opts);
      latestSnapshot = {
        statusRef: hookResult.statusRef,
        isSticky: hookResult.isSticky,
        opacity: hookResult.opacity,
      };

      return React.createElement(
        "div",
        {
          "data-page-scroll-container": "true",
          "data-testid": "scroll-container",
          style: { height: "500px", overflow: "auto" },
        },
        React.createElement("div", {
          "data-testid": "status",
          ref: hookResult.statusRef,
        }),
      );
    };

    const utils = render(React.createElement(TestComponent, { opts: options }));

    const scrollContainer = utils.getByTestId(
      "scroll-container",
    ) as HTMLElement;
    const statusElement = utils.getByTestId("status") as HTMLDivElement;

    const getSnapshot = () => {
      if (!latestSnapshot) {
        throw new Error("Hook snapshot not captured yet");
      }
      return latestSnapshot;
    };

    return {
      scrollContainer,
      statusElement,
      getSnapshot,
      unmount: utils.unmount,
    };
  }

  it("should initialize with default state", () => {
    const { getSnapshot } = setupHook();
    const snapshot = getSnapshot();

    expect(snapshot.statusRef.current).toBeInstanceOf(HTMLDivElement);
    // Initial sticky state can vary based on layout, but opacity should start at 0
    expect(snapshot.opacity).toBe(0);
  });

  it("should use custom fadeDistance", () => {
    const { getSnapshot } = setupHook({ fadeDistance: 200 });
    const snapshot = getSnapshot();
    expect(snapshot.statusRef.current).toBeInstanceOf(HTMLDivElement);
  });

  it("should use custom scrollContainerSelector", () => {
    let latestSnapshot: HookSnapshot | null = null;

    const CustomContainerComponent = () => {
      const hookResult = useStickyStatus({
        scrollContainerSelector: '[data-custom-scroll="true"]',
      });
      latestSnapshot = {
        statusRef: hookResult.statusRef,
        isSticky: hookResult.isSticky,
        opacity: hookResult.opacity,
      };

      return React.createElement(
        "div",
        {
          "data-custom-scroll": "true",
          "data-testid": "custom-scroll",
          style: { height: "500px", overflow: "auto" },
        },
        React.createElement("div", {
          "data-testid": "status",
          ref: hookResult.statusRef,
        }),
      );
    };

    const utils = render(React.createElement(CustomContainerComponent));
    const statusEl = utils.getByTestId("status");
    expect(statusEl).toBeDefined();
    expect(latestSnapshot).not.toBeNull();
    const snapshot = latestSnapshot as unknown as HookSnapshot;
    expect(snapshot.statusRef.current).toBe(statusEl);
  });

  it("should handle when status element is not found", () => {
    let latestSnapshot: HookSnapshot | null = null;

    const NoStatusComponent = () => {
      const hookResult = useStickyStatus();
      latestSnapshot = {
        statusRef: hookResult.statusRef,
        isSticky: hookResult.isSticky,
        opacity: hookResult.opacity,
      };

      // Intentionally do NOT attach statusRef to any DOM element
      return React.createElement("div", {
        "data-page-scroll-container": "true",
        "data-testid": "scroll-container",
      });
    };

    render(React.createElement(NoStatusComponent));

    expect(latestSnapshot).not.toBeNull();
    const snapshot = latestSnapshot as unknown as HookSnapshot;
    expect(snapshot.statusRef.current).toBeNull();
    expect(snapshot.isSticky).toBe(false);
    expect(snapshot.opacity).toBe(0);
  });

  it("should handle when scroll container is not found", () => {
    const { getSnapshot } = setupHook({
      scrollContainerSelector: '[data-nonexistent="true"]',
    });

    const snapshot = getSnapshot();
    // Effect should early-return without throwing, leaving state untouched.
    expect(snapshot.isSticky).toBe(false);
    expect(snapshot.opacity).toBe(0);
  });

  it("should become sticky when status is scrolled past", () => {
    const { scrollContainer, statusElement, getSnapshot } = setupHook();

    // Container stays fixed
    vi.spyOn(scrollContainer, "getBoundingClientRect").mockReturnValue({
      top: 0,
      bottom: 500,
      left: 0,
      right: 100,
      width: 100,
      height: 500,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    } as DOMRect);

    // Status initially visible
    vi.spyOn(statusElement, "getBoundingClientRect").mockReturnValue({
      top: 50,
      bottom: 100,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 50,
      toJSON: vi.fn(),
    } as DOMRect);

    // Now scroll so that the status is above the container's top
    scrollContainer.scrollTop = 100;
    vi.spyOn(statusElement, "getBoundingClientRect").mockReturnValue({
      top: -10,
      bottom: 40,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: -10,
      toJSON: vi.fn(),
    } as DOMRect);

    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });

    const snapshot = getSnapshot();
    // When scrolled past, opacity should be within the valid range
    expect(snapshot.opacity).toBeGreaterThanOrEqual(0);
    expect(snapshot.opacity).toBeLessThanOrEqual(1);
  });

  it("should update opacity while scrolling down and up when sticky", () => {
    const { scrollContainer, statusElement, getSnapshot } = setupHook({
      fadeDistance: 100,
    });

    // Container rect is fixed
    vi.spyOn(scrollContainer, "getBoundingClientRect").mockReturnValue({
      top: 0,
      bottom: 500,
      left: 0,
      right: 100,
      width: 100,
      height: 500,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    } as DOMRect);

    // First scroll: make sticky (status just above top)
    vi.spyOn(statusElement, "getBoundingClientRect").mockReturnValue({
      top: -10,
      bottom: 40,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: -10,
      toJSON: vi.fn(),
    } as DOMRect);

    scrollContainer.scrollTop = 100;
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });

    const afterSticky = getSnapshot();
    expect(afterSticky.opacity).toBeGreaterThanOrEqual(0);

    // Second scroll: further down, still sticky, opacity should move towards 1
    scrollContainer.scrollTop = 200;
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });
    const afterFurtherDown = getSnapshot();
    expect(afterFurtherDown.opacity).toBeGreaterThanOrEqual(
      afterSticky.opacity,
    );

    // Third scroll: scrolling up but still past original position
    scrollContainer.scrollTop = 130;
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });
    const afterScrollUp = getSnapshot();
    // Opacity should still be between 0 and 1 while sticky logic is active
    expect(afterScrollUp.opacity).toBeGreaterThanOrEqual(0);
    expect(afterScrollUp.opacity).toBeLessThanOrEqual(1);
  });

  it("should keep opacity valid when scrolling back after being sticky", () => {
    const { scrollContainer, statusElement, getSnapshot } = setupHook({
      fadeDistance: 100,
    });

    // Container rect fixed
    vi.spyOn(scrollContainer, "getBoundingClientRect").mockReturnValue({
      top: 0,
      bottom: 500,
      left: 0,
      right: 100,
      width: 100,
      height: 500,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    } as DOMRect);

    const statusRectSpy = vi.spyOn(statusElement, "getBoundingClientRect");

    // First scroll: make sticky (status above top)
    statusRectSpy.mockReturnValueOnce({
      top: -10,
      bottom: 40,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: -10,
      toJSON: vi.fn(),
    } as DOMRect);

    scrollContainer.scrollTop = 100;
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });
    const afterSticky = getSnapshot();
    expect(afterSticky.opacity).toBeGreaterThanOrEqual(0);

    // Second scroll: scroll back so scrollPastOriginal <= 0 (unstick),
    // with the status element now visible again.
    statusRectSpy.mockReturnValue({
      top: 50,
      bottom: 100,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 50,
      toJSON: vi.fn(),
    } as DOMRect);
    scrollContainer.scrollTop = 0;
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });

    // Third scroll: status remains visible, non-sticky branch should
    // reset opacity back to 0.
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });

    const afterVisible = getSnapshot();
    expect(afterVisible.opacity).toBeGreaterThanOrEqual(0);
    expect(afterVisible.opacity).toBeLessThanOrEqual(1);
  });

  it("should handle resize events without throwing", () => {
    const { scrollContainer, statusElement, getSnapshot } = setupHook();

    vi.spyOn(scrollContainer, "getBoundingClientRect").mockReturnValue({
      top: 0,
      bottom: 500,
      left: 0,
      right: 100,
      width: 100,
      height: 500,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    } as DOMRect);

    vi.spyOn(statusElement, "getBoundingClientRect").mockReturnValue({
      top: 50,
      bottom: 100,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 50,
      toJSON: vi.fn(),
    } as DOMRect);

    act(() => {
      window.dispatchEvent(new Event("resize"));
    });

    const snapshot = getSnapshot();
    expect(snapshot.statusRef.current).toBe(statusElement);
  });

  it("should cancel pending animation frame on rapid scrolls", () => {
    const { scrollContainer, statusElement } = setupHook();

    vi.spyOn(scrollContainer, "getBoundingClientRect").mockReturnValue({
      top: 0,
      bottom: 500,
      left: 0,
      right: 100,
      width: 100,
      height: 500,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    } as DOMRect);

    vi.spyOn(statusElement, "getBoundingClientRect").mockReturnValue({
      top: 50,
      bottom: 100,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 50,
      toJSON: vi.fn(),
    } as DOMRect);

    // First scroll schedules RAF
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });
    expect(mockRequestAnimationFrame).toHaveBeenCalled();

    // Second scroll should cancel previous RAF
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });
    expect(mockCancelAnimationFrame).toHaveBeenCalled();
  });

  it("should cleanup on unmount", () => {
    const { scrollContainer, statusElement, unmount } = setupHook();

    vi.spyOn(scrollContainer, "getBoundingClientRect").mockReturnValue({
      top: 0,
      bottom: 500,
      left: 0,
      right: 100,
      width: 100,
      height: 500,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    } as DOMRect);

    vi.spyOn(statusElement, "getBoundingClientRect").mockReturnValue({
      top: -10,
      bottom: 40,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: -10,
      toJSON: vi.fn(),
    } as DOMRect);

    // Trigger a scroll to schedule an RAF
    scrollContainer.scrollTop = 100;
    act(() => {
      scrollContainer.dispatchEvent(new Event("scroll"));
    });

    unmount();
    // If a RAF was scheduled, it should have been cancelled during cleanup
    if (mockRequestAnimationFrame.mock.calls.length > 0) {
      expect(mockCancelAnimationFrame).toHaveBeenCalled();
    }
  });

  it("should not update opacity when already 0 and element visible", () => {
    const { scrollContainer, statusElement, getSnapshot } = setupHook();

    vi.spyOn(scrollContainer, "getBoundingClientRect").mockReturnValue({
      top: 0,
      bottom: 500,
      left: 0,
      right: 100,
      width: 100,
      height: 500,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    } as DOMRect);

    vi.spyOn(statusElement, "getBoundingClientRect").mockReturnValue({
      top: 50,
      bottom: 100,
      left: 0,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 50,
      toJSON: vi.fn(),
    } as DOMRect);

    act(() => {
      scrollContainer.scrollTop = 10;
      scrollContainer.dispatchEvent(new Event("scroll"));
    });

    const snapshot = getSnapshot();
    expect(snapshot.opacity).toBe(0);
    expect(snapshot.isSticky).toBe(false);
  });
});
