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

vi.mock("@/utils/scroll", () => ({
  findScrollableParent: vi.fn(),
  calculateScrollPosition: vi.fn(),
  calculateContainerScrollPosition: vi.fn(),
  scrollWindowTo: vi.fn(),
  scrollContainerTo: vi.fn(),
}));

import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  calculateContainerScrollPosition,
  calculateScrollPosition,
  findScrollableParent,
  scrollContainerTo,
  scrollWindowTo,
} from "@/utils/scroll";
import { useTabScroll } from "./useTabScroll";

describe("useTabScroll", () => {
  beforeEach(() => {
    // Don't stub window in browser environment - use Object.defineProperty if needed
    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: 800,
    });
    vi.stubGlobal("getComputedStyle", vi.fn());

    // Make setTimeout execute immediately (synchronously) for testing
    vi.stubGlobal("setTimeout", (fn: () => void) => {
      fn();
      return 1 as unknown as NodeJS.Timeout;
    });

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should return refs and scrollToBottom function", () => {
    const { result } = renderHook(() => useTabScroll());

    expect(result.current.headerRef).toBeDefined();
    expect(result.current.contentRef).toBeDefined();
    expect(result.current.scrollToBottom).toBeDefined();
  });

  it("should use default options", () => {
    const { result } = renderHook(() => useTabScroll());

    expect(result.current.headerRef.current).toBeNull();
    expect(result.current.contentRef.current).toBeNull();
  });

  it("should accept custom options", () => {
    const { result } = renderHook(() =>
      useTabScroll({
        scrollDelay: 100,
        paddingTop: 30,
        paddingBottom: 30,
        behavior: "auto",
        contentSelector: '[data-custom="true"]',
      }),
    );

    expect(result.current.headerRef).toBeDefined();
    expect(result.current.contentRef).toBeDefined();
    expect(result.current.scrollToBottom).toBeDefined();
  });

  it("should return early when contentRef is null", () => {
    const { result } = renderHook(() => useTabScroll());

    result.current.scrollToBottom();

    expect(findScrollableParent).not.toHaveBeenCalled();
  });

  it("should return early when headerRef is null", () => {
    const { result } = renderHook(() => useTabScroll());

    const mockContent = document.createElement("div");
    result.current.contentRef.current = mockContent as HTMLDivElement;

    result.current.scrollToBottom();

    expect(findScrollableParent).not.toHaveBeenCalled();
  });

  it("should find scrollable parent and scroll container", () => {
    const { result } = renderHook(() => useTabScroll());

    const mockHeader = document.createElement("h1");
    const mockContent = document.createElement("div");
    const mockScrollableParent = document.createElement("div");
    const mockActiveContent = document.createElement("div");
    const mockLastChild = document.createElement("div");

    mockActiveContent.setAttribute("data-tab-content", "true");
    mockActiveContent.appendChild(mockLastChild);
    mockContent.appendChild(mockActiveContent);

    const mockQuerySelector = vi.fn(() => mockActiveContent);
    mockContent.querySelector = mockQuerySelector;

    result.current.headerRef.current = mockHeader as HTMLHeadingElement;
    result.current.contentRef.current = mockContent as HTMLDivElement;

    vi.mocked(findScrollableParent).mockReturnValue(mockScrollableParent);
    vi.mocked(calculateContainerScrollPosition).mockReturnValue(100);
    mockHeader.getBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      bottom: 50,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));
    mockLastChild.getBoundingClientRect = vi.fn(() => ({
      top: 200,
      left: 0,
      bottom: 250,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));

    result.current.scrollToBottom();

    expect(findScrollableParent).toHaveBeenCalledWith(mockContent);
    expect(calculateContainerScrollPosition).toHaveBeenCalled();
    expect(scrollContainerTo).toHaveBeenCalledWith(
      mockScrollableParent,
      100,
      "smooth",
    );
  });

  it("should scroll window when no scrollable parent", () => {
    const { result } = renderHook(() => useTabScroll());

    const mockHeader = document.createElement("h1");
    const mockContent = document.createElement("div");
    const mockActiveContent = document.createElement("div");
    const mockLastChild = document.createElement("div");

    mockActiveContent.setAttribute("data-tab-content", "true");
    mockActiveContent.appendChild(mockLastChild);
    mockContent.appendChild(mockActiveContent);

    const mockQuerySelector = vi.fn(() => mockActiveContent);
    mockContent.querySelector = mockQuerySelector;

    result.current.headerRef.current = mockHeader as HTMLHeadingElement;
    result.current.contentRef.current = mockContent as HTMLDivElement;

    vi.mocked(findScrollableParent).mockReturnValue(null);
    vi.mocked(calculateScrollPosition).mockReturnValue(200);
    mockHeader.getBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      bottom: 50,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));
    mockLastChild.getBoundingClientRect = vi.fn(() => ({
      top: 200,
      left: 0,
      bottom: 250,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));

    result.current.scrollToBottom();

    expect(findScrollableParent).toHaveBeenCalledWith(mockContent);
    expect(calculateScrollPosition).toHaveBeenCalled();
    expect(scrollWindowTo).toHaveBeenCalledWith(200, "smooth");
  });

  it("should return early when active content is not found", () => {
    const { result } = renderHook(() => useTabScroll());

    const mockHeader = document.createElement("h1");
    const mockContent = document.createElement("div");

    result.current.headerRef.current = mockHeader as HTMLHeadingElement;
    result.current.contentRef.current = mockContent as HTMLDivElement;

    result.current.scrollToBottom();

    expect(findScrollableParent).not.toHaveBeenCalled();
  });

  it("should return early when last child is not found", () => {
    const { result } = renderHook(() => useTabScroll());

    const mockHeader = document.createElement("h1");
    const mockContent = document.createElement("div");
    const mockActiveContent = document.createElement("div");

    mockActiveContent.setAttribute("data-tab-content", "true");
    mockContent.appendChild(mockActiveContent);

    result.current.headerRef.current = mockHeader as HTMLHeadingElement;
    result.current.contentRef.current = mockContent as HTMLDivElement;

    result.current.scrollToBottom();

    expect(findScrollableParent).not.toHaveBeenCalled();
  });

  it("should use custom contentSelector", () => {
    const { result } = renderHook(() =>
      useTabScroll({
        contentSelector: '[data-custom="true"]',
      }),
    );

    const mockHeader = document.createElement("h1");
    const mockContent = document.createElement("div");
    const mockActiveContent = document.createElement("div");
    const mockLastChild = document.createElement("div");

    mockActiveContent.setAttribute("data-custom", "true");
    mockActiveContent.appendChild(mockLastChild);
    mockContent.appendChild(mockActiveContent);

    const mockQuerySelector = vi.fn(() => mockActiveContent);
    mockContent.querySelector = mockQuerySelector;

    result.current.headerRef.current = mockHeader as HTMLHeadingElement;
    result.current.contentRef.current = mockContent as HTMLDivElement;

    vi.mocked(findScrollableParent).mockReturnValue(null);
    vi.mocked(calculateScrollPosition).mockReturnValue(200);
    mockHeader.getBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      bottom: 50,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));
    mockLastChild.getBoundingClientRect = vi.fn(() => ({
      top: 200,
      left: 0,
      bottom: 250,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));

    result.current.scrollToBottom();

    expect(mockQuerySelector).toHaveBeenCalledWith('[data-custom="true"]');
  });

  it("should not scroll when calculateContainerScrollPosition returns null", () => {
    const { result } = renderHook(() => useTabScroll());

    const mockHeader = document.createElement("h1");
    const mockContent = document.createElement("div");
    const mockScrollableParent = document.createElement("div");
    const mockActiveContent = document.createElement("div");
    const mockLastChild = document.createElement("div");

    mockActiveContent.setAttribute("data-tab-content", "true");
    mockActiveContent.appendChild(mockLastChild);
    mockContent.appendChild(mockActiveContent);

    const mockQuerySelector = vi.fn(() => mockActiveContent);
    mockContent.querySelector = mockQuerySelector;

    result.current.headerRef.current = mockHeader as HTMLHeadingElement;
    result.current.contentRef.current = mockContent as HTMLDivElement;

    vi.mocked(findScrollableParent).mockReturnValue(mockScrollableParent);
    vi.mocked(calculateContainerScrollPosition).mockReturnValue(null);
    mockHeader.getBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      bottom: 50,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));
    mockLastChild.getBoundingClientRect = vi.fn(() => ({
      top: 200,
      left: 0,
      bottom: 250,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));

    result.current.scrollToBottom();

    expect(scrollContainerTo).not.toHaveBeenCalled();
  });

  it("should not scroll when calculateScrollPosition returns null", () => {
    const { result } = renderHook(() => useTabScroll());

    const mockHeader = document.createElement("h1");
    const mockContent = document.createElement("div");
    const mockActiveContent = document.createElement("div");
    const mockLastChild = document.createElement("div");

    mockActiveContent.setAttribute("data-tab-content", "true");
    mockActiveContent.appendChild(mockLastChild);
    mockContent.appendChild(mockActiveContent);

    const mockQuerySelector = vi.fn(() => mockActiveContent);
    mockContent.querySelector = mockQuerySelector;

    result.current.headerRef.current = mockHeader as HTMLHeadingElement;
    result.current.contentRef.current = mockContent as HTMLDivElement;

    vi.mocked(findScrollableParent).mockReturnValue(null);
    vi.mocked(calculateScrollPosition).mockReturnValue(null);
    mockHeader.getBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      bottom: 50,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));
    mockLastChild.getBoundingClientRect = vi.fn(() => ({
      top: 200,
      left: 0,
      bottom: 250,
      right: 100,
      width: 100,
      height: 50,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));

    result.current.scrollToBottom();

    expect(scrollWindowTo).not.toHaveBeenCalled();
  });
});
