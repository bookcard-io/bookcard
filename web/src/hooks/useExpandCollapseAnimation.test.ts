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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useExpandCollapseAnimation } from "./useExpandCollapseAnimation";

describe("useExpandCollapseAnimation", () => {
  let mockScrollIntoView: (arg?: boolean | ScrollIntoViewOptions) => void;

  beforeEach(() => {
    vi.useFakeTimers();
    mockScrollIntoView = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should initialize with shouldRender false and isAnimatingOut false", () => {
    const { result } = renderHook(() =>
      useExpandCollapseAnimation({ isExpanded: false }),
    );

    expect(result.current.shouldRender).toBe(false);
    expect(result.current.isAnimatingOut).toBe(false);
    expect(result.current.containerRef).toBeDefined();
  });

  it("should set shouldRender to true when expanded", () => {
    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: false } },
    );

    expect(result.current.shouldRender).toBe(false);

    act(() => {
      rerender({ isExpanded: true });
    });

    expect(result.current.shouldRender).toBe(true);
    expect(result.current.isAnimatingOut).toBe(false);
  });

  it("should scroll to container when expanding", () => {
    const mockElement = document.createElement("div");
    mockElement.scrollIntoView = mockScrollIntoView;

    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: false } },
    );

    // Manually set the ref for testing
    (
      result.current.containerRef as { current: HTMLDivElement | null }
    ).current = mockElement;

    act(() => {
      rerender({ isExpanded: true });
    });

    expect(mockScrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "start",
    });
  });

  it("should set isAnimatingOut to true when collapsing", () => {
    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: true } },
    );

    expect(result.current.shouldRender).toBe(true);
    expect(result.current.isAnimatingOut).toBe(false);

    act(() => {
      rerender({ isExpanded: false });
    });

    expect(result.current.isAnimatingOut).toBe(true);
    expect(result.current.shouldRender).toBe(true);
  });

  it("should scroll to container when collapsing", () => {
    const mockElement = document.createElement("div");
    mockElement.scrollIntoView = mockScrollIntoView;

    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: true } },
    );

    (
      result.current.containerRef as { current: HTMLDivElement | null }
    ).current = mockElement;

    act(() => {
      rerender({ isExpanded: false });
    });

    expect(mockScrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "start",
    });
  });

  it("should set shouldRender to false after animation duration when collapsing", () => {
    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: true } },
    );

    expect(result.current.shouldRender).toBe(true);

    act(() => {
      rerender({ isExpanded: false });
    });

    expect(result.current.isAnimatingOut).toBe(true);
    expect(result.current.shouldRender).toBe(true);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.shouldRender).toBe(false);
    expect(result.current.isAnimatingOut).toBe(false);
  });

  it("should use custom animation duration", () => {
    const { result, rerender } = renderHook(
      ({ isExpanded }) =>
        useExpandCollapseAnimation({ isExpanded, animationDuration: 1000 }),
      { initialProps: { isExpanded: true } },
    );

    act(() => {
      rerender({ isExpanded: false });
    });

    expect(result.current.isAnimatingOut).toBe(true);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    // Should still be animating after 500ms
    expect(result.current.shouldRender).toBe(true);
    expect(result.current.isAnimatingOut).toBe(true);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    // Should be done after 1000ms
    expect(result.current.shouldRender).toBe(false);
    expect(result.current.isAnimatingOut).toBe(false);
  });

  it("should handle containerRef being null when expanding", () => {
    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: false } },
    );

    // Ensure ref is null
    (
      result.current.containerRef as { current: HTMLDivElement | null }
    ).current = null;

    act(() => {
      rerender({ isExpanded: true });
    });

    // Should not throw and should still set shouldRender
    expect(result.current.shouldRender).toBe(true);
    expect(mockScrollIntoView).not.toHaveBeenCalled();
  });

  it("should handle containerRef being null when collapsing", () => {
    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: true } },
    );

    // Ensure ref is null
    (
      result.current.containerRef as { current: HTMLDivElement | null }
    ).current = null;

    act(() => {
      rerender({ isExpanded: false });
    });

    // Should not throw
    expect(result.current.isAnimatingOut).toBe(true);
    expect(mockScrollIntoView).not.toHaveBeenCalled();
  });

  it("should clean up timer on unmount during collapse", () => {
    const { result, rerender, unmount } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: true } },
    );

    act(() => {
      rerender({ isExpanded: false });
    });

    expect(result.current.isAnimatingOut).toBe(true);

    unmount();

    act(() => {
      vi.advanceTimersByTime(500);
    });

    // Should not cause errors
    expect(true).toBe(true);
  });

  it("should not collapse if shouldRender is false", () => {
    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: false } },
    );

    expect(result.current.shouldRender).toBe(false);

    act(() => {
      rerender({ isExpanded: false });
    });

    // Should remain false, no animation triggered
    expect(result.current.shouldRender).toBe(false);
    expect(result.current.isAnimatingOut).toBe(false);
  });

  it("should handle rapid expand/collapse cycles", () => {
    const { result, rerender } = renderHook(
      ({ isExpanded }) => useExpandCollapseAnimation({ isExpanded }),
      { initialProps: { isExpanded: false } },
    );

    // Expand
    act(() => {
      rerender({ isExpanded: true });
    });
    expect(result.current.shouldRender).toBe(true);

    // Collapse
    act(() => {
      rerender({ isExpanded: false });
    });
    expect(result.current.isAnimatingOut).toBe(true);

    // Expand again before collapse completes
    act(() => {
      rerender({ isExpanded: true });
    });
    expect(result.current.shouldRender).toBe(true);
    expect(result.current.isAnimatingOut).toBe(false);

    // Advance time - should not collapse since we expanded again
    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.shouldRender).toBe(true);
    expect(result.current.isAnimatingOut).toBe(false);
  });
});
