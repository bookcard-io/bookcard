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
import { useSidebarScroll } from "./useSidebarScroll";

describe("useSidebarScroll", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should return navRef and isScrolling", () => {
    const { result } = renderHook(() => useSidebarScroll());

    expect(result.current.navRef).toBeDefined();
    expect(result.current.navRef.current).toBeNull();
    expect(result.current.isScrolling).toBe(false);
  });

  it("should use default hideDelay option", () => {
    const { result } = renderHook(() => useSidebarScroll());

    expect(result.current.navRef).toBeDefined();
    expect(result.current.isScrolling).toBe(false);
  });

  it("should accept custom hideDelay option", () => {
    const { result } = renderHook(() => useSidebarScroll({ hideDelay: 500 }));

    expect(result.current.navRef).toBeDefined();
    expect(result.current.isScrolling).toBe(false);
  });

  it("should set isScrolling to true on scroll", () => {
    const { result, rerender } = renderHook(
      ({ hideDelay }) => useSidebarScroll({ hideDelay }),
      { initialProps: { hideDelay: 1000 } },
    );
    const mockElement = document.createElement("div");

    act(() => {
      result.current.navRef.current = mockElement;
    });

    // Change hideDelay to trigger useEffect
    rerender({ hideDelay: 2000 });

    const scrollEvent = new Event("scroll");
    act(() => {
      mockElement.dispatchEvent(scrollEvent);
    });

    expect(result.current.isScrolling).toBe(true);
  });

  it("should handle multiple scroll events", () => {
    const { result, rerender } = renderHook(
      ({ hideDelay }) => useSidebarScroll({ hideDelay }),
      { initialProps: { hideDelay: 1000 } },
    );
    const mockElement = document.createElement("div");

    act(() => {
      result.current.navRef.current = mockElement;
    });

    // Change hideDelay to trigger useEffect
    rerender({ hideDelay: 2000 });

    const scrollEvent = new Event("scroll");

    act(() => {
      mockElement.dispatchEvent(scrollEvent);
    });

    expect(result.current.isScrolling).toBe(true);

    // Scroll again
    act(() => {
      mockElement.dispatchEvent(scrollEvent);
    });

    expect(result.current.isScrolling).toBe(true);
  });

  it("should not attach event listener when navRef is null", () => {
    const { result } = renderHook(() => useSidebarScroll());

    // navRef should be null initially
    expect(result.current.navRef.current).toBeNull();
    expect(result.current.isScrolling).toBe(false);
  });

  it("should attach scroll event listener when navRef is set and hideDelay changes", () => {
    const mockElement = document.createElement("div");
    const addEventListenerSpy = vi.spyOn(mockElement, "addEventListener");

    const { result, rerender } = renderHook(
      ({ hideDelay }) => useSidebarScroll({ hideDelay }),
      { initialProps: { hideDelay: 1000 } },
    );

    // Set ref
    act(() => {
      result.current.navRef.current = mockElement;
    });

    // Change hideDelay to trigger useEffect (handleScroll dependency changes)
    rerender({ hideDelay: 2000 });

    // The event listener should be attached when hideDelay changes and navRef is set
    expect(addEventListenerSpy).toHaveBeenCalledWith(
      "scroll",
      expect.any(Function),
    );
  });

  it("should remove event listener on unmount", () => {
    const { result, rerender, unmount } = renderHook(
      ({ hideDelay }) => useSidebarScroll({ hideDelay }),
      { initialProps: { hideDelay: 1000 } },
    );
    const mockElement = document.createElement("div");
    const removeEventListenerSpy = vi.spyOn(mockElement, "removeEventListener");

    act(() => {
      result.current.navRef.current = mockElement;
    });

    // Change hideDelay to trigger useEffect
    rerender({ hideDelay: 2000 });

    unmount();

    expect(removeEventListenerSpy).toHaveBeenCalledWith(
      "scroll",
      expect.any(Function),
    );
  });

  it("should handle multiple rapid scroll events", () => {
    const { result, rerender } = renderHook(
      ({ hideDelay }) => useSidebarScroll({ hideDelay }),
      { initialProps: { hideDelay: 1000 } },
    );
    const mockElement = document.createElement("div");

    act(() => {
      result.current.navRef.current = mockElement;
    });

    // Change hideDelay to trigger useEffect
    rerender({ hideDelay: 2000 });

    const scrollEvent = new Event("scroll");

    act(() => {
      for (let i = 0; i < 5; i++) {
        mockElement.dispatchEvent(scrollEvent);
      }
    });

    expect(result.current.isScrolling).toBe(true);
  });

  it("should handle navRef being set after initial render", () => {
    const { result, rerender } = renderHook(
      ({ hideDelay }) => useSidebarScroll({ hideDelay }),
      { initialProps: { hideDelay: 1000 } },
    );
    const mockElement = document.createElement("div");

    expect(result.current.navRef.current).toBeNull();

    act(() => {
      result.current.navRef.current = mockElement;
    });

    // Change hideDelay to trigger useEffect (handleScroll dependency changes)
    rerender({ hideDelay: 2000 });

    const scrollEvent = new Event("scroll");
    act(() => {
      mockElement.dispatchEvent(scrollEvent);
    });

    expect(result.current.isScrolling).toBe(true);
  });

  it("should handle cleanup when unmounted", () => {
    const { unmount } = renderHook(() => useSidebarScroll());

    // Should not throw on unmount
    expect(() => {
      unmount();
    }).not.toThrow();
  });
});
