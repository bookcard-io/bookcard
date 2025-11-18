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

const mockScrollContainerTo = vi.fn();
vi.mock("@/utils/scroll", () => ({
  scrollContainerTo: (...args: unknown[]) => mockScrollContainerTo(...args),
}));

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useScrollNavigation } from "./useScrollNavigation";

describe("useScrollNavigation", () => {
  let mockContainer: HTMLElement;

  beforeEach(() => {
    mockContainer = document.createElement("div");
    mockContainer.setAttribute("data-page-scroll-container", "true");
    // scrollTop starts at 0, but we'll set it after container is found
    document.body.appendChild(mockContainer);
    mockScrollContainerTo.mockClear();
  });

  afterEach(() => {
    if (document.body.contains(mockContainer)) {
      document.body.removeChild(mockContainer);
    }
    vi.clearAllMocks();
    mockScrollContainerTo.mockClear();
  });

  it("should initialize with default options", () => {
    const { result } = renderHook(() => useScrollNavigation());

    expect(result.current.scrollToTop).toBeDefined();
    expect(result.current.scrollUp).toBeDefined();
    expect(result.current.scrollDown).toBeDefined();
  });

  it("should use custom scroll container selector", () => {
    const customContainer = document.createElement("div");
    customContainer.setAttribute("data-custom-scroll", "true");
    customContainer.scrollTop = 50;
    document.body.appendChild(customContainer);

    const { result } = renderHook(() =>
      useScrollNavigation({
        scrollContainerSelector: '[data-custom-scroll="true"]',
      }),
    );

    act(() => {
      result.current.scrollToTop();
    });

    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      customContainer,
      0,
      "smooth",
    );

    document.body.removeChild(customContainer);
  });

  it("should use custom scroll amount", () => {
    const { result } = renderHook(() =>
      useScrollNavigation({ scrollAmount: 100 }),
    );

    act(() => {
      result.current.scrollUp();
    });

    // First scroll up: 100 - (100 * 1) = 0
    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      mockContainer,
      0,
      "smooth",
    );
  });

  it("should scroll to top and reset counters", () => {
    const { result } = renderHook(() => useScrollNavigation());

    act(() => {
      result.current.scrollToTop();
    });

    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      mockContainer,
      0,
      "smooth",
    );
  });

  it("should scroll up progressively", () => {
    const { result } = renderHook(() => useScrollNavigation());

    act(() => {
      result.current.scrollUp();
    });

    // First scroll: 100 - (325 * 1) = -225, clamped to 0
    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      mockContainer,
      0,
      "smooth",
    );

    vi.clearAllMocks();
    mockScrollContainerTo.mockClear();

    act(() => {
      result.current.scrollUp();
    });

    // Second scroll: still at 100 (scrollTo doesn't actually change scrollTop in test)
    // So: 100 - (325 * 2) = -550, clamped to 0
    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      mockContainer,
      0,
      "smooth",
    );
  });

  it("should scroll down progressively", () => {
    const { result } = renderHook(() => useScrollNavigation());

    // Set initial scrollTop after hook initializes
    act(() => {
      mockContainer.scrollTop = 0;
    });

    act(() => {
      result.current.scrollDown();
    });

    // First scroll: 0 + (325 * 1) = 325
    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      mockContainer,
      325,
      "smooth",
    );

    vi.clearAllMocks();
    mockScrollContainerTo.mockClear();
    // scrollTo doesn't actually update scrollTop in test, so it stays at 0
    act(() => {
      result.current.scrollDown();
    });

    // Second scroll: 0 + (325 * 2) = 650
    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      mockContainer,
      650,
      "smooth",
    );
  });

  it("should reset scroll down counter when scrolling up", () => {
    const { result } = renderHook(() => useScrollNavigation());

    // Scroll down twice to increment counter
    act(() => {
      result.current.scrollDown();
    });
    act(() => {
      result.current.scrollDown();
    });

    vi.clearAllMocks();
    mockScrollContainerTo.mockClear();
    // Set scrollTop to simulate we scrolled up manually (less than previous 100)
    // The lastScrollTopRef was initialized to 100, so we need to set it lower
    mockContainer.scrollTop = 50;
    // Update lastScrollTopRef by triggering scroll event
    act(() => {
      const event = new Event("scroll");
      mockContainer.dispatchEvent(event);
    });

    // Now scroll up - counter should be reset, so first scroll up
    act(() => {
      result.current.scrollUp();
    });

    // Should be first scroll up: 50 - (325 * 1) = -275, clamped to 0
    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      mockContainer,
      0,
      "smooth",
    );
  });

  it("should reset scroll up counter when scrolling down", () => {
    const { result } = renderHook(() => useScrollNavigation());

    // Set initial scrollTop to 0 (default)
    // Scroll up twice to increment counter
    act(() => {
      result.current.scrollUp();
    });
    act(() => {
      result.current.scrollUp();
    });

    vi.clearAllMocks();
    mockScrollContainerTo.mockClear();
    // Set scrollTop to simulate we scrolled down manually (more than previous 0)
    // The lastScrollTopRef was initialized to 0, so we need to set it higher
    mockContainer.scrollTop = 100;
    // Update lastScrollTopRef by triggering scroll event
    act(() => {
      const event = new Event("scroll");
      mockContainer.dispatchEvent(event);
    });

    // Now scroll down - counter should be reset, so first scroll down
    act(() => {
      result.current.scrollDown();
    });

    // Should be first scroll down: 0 + (325 * 1) = 325
    // The scrollTop is read at call time, and it's 0 (not updated by scrollTo in tests)
    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      mockContainer,
      325,
      "smooth",
    );
  });

  it("should handle no scroll container found", () => {
    const { result, unmount } = renderHook(() =>
      useScrollNavigation({
        scrollContainerSelector: '[data-nonexistent="true"]',
      }),
    );

    act(() => {
      result.current.scrollToTop();
      result.current.scrollUp();
      result.current.scrollDown();
    });

    // Should not throw and should not call scrollContainerTo
    expect(mockScrollContainerTo).not.toHaveBeenCalled();
    unmount();
  });

  it("should update scroll container when selector changes", () => {
    const newContainer = document.createElement("div");
    newContainer.setAttribute("data-new-scroll", "true");
    newContainer.scrollTop = 200;
    document.body.appendChild(newContainer);

    const { result, rerender } = renderHook(
      ({ selector }) =>
        useScrollNavigation({ scrollContainerSelector: selector }),
      { initialProps: { selector: '[data-page-scroll-container="true"]' } },
    );

    rerender({ selector: '[data-new-scroll="true"]' });

    act(() => {
      result.current.scrollToTop();
    });

    expect(mockScrollContainerTo).toHaveBeenCalledWith(
      newContainer,
      0,
      "smooth",
    );

    document.body.removeChild(newContainer);
  });
});
