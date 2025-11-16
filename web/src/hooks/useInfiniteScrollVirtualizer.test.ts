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

import type { Virtualizer } from "@tanstack/react-virtual";
import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useInfiniteScrollVirtualizer } from "./useInfiniteScrollVirtualizer";

describe("useInfiniteScrollVirtualizer", () => {
  let mockVirtualizer: Virtualizer<Element, Element>;
  let mockLoadMore: ReturnType<typeof vi.fn<() => void>>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockLoadMore = vi.fn<() => void>();

    mockVirtualizer = {
      getVirtualItems: vi.fn(() => []),
    } as unknown as Virtualizer<Element, Element>;
  });

  it("should not load more when hasMore is false", () => {
    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: false,
        isLoading: false,
        loadMore: mockLoadMore,
      }),
    );

    expect(mockLoadMore).not.toHaveBeenCalled();
  });

  it("should not load more when loadMore is not provided", () => {
    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: true,
        isLoading: false,
      }),
    );

    expect(mockLoadMore).not.toHaveBeenCalled();
  });

  it("should not load more when isLoading is true", () => {
    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: true,
        isLoading: true,
        loadMore: mockLoadMore,
      }),
    );

    expect(mockLoadMore).not.toHaveBeenCalled();
  });

  it("should not load more when there are no virtual items", () => {
    vi.mocked(mockVirtualizer.getVirtualItems).mockReturnValue([]);

    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: true,
        isLoading: false,
        loadMore: mockLoadMore,
      }),
    );

    expect(mockLoadMore).not.toHaveBeenCalled();
  });

  it("should load more when within threshold of the end", () => {
    const virtualItems = [
      { index: 0, start: 0, end: 100 },
      { index: 1, start: 100, end: 200 },
      { index: 8, start: 800, end: 900 }, // Last item, index 8 out of 10 items (0-9)
    ];

    vi.mocked(mockVirtualizer.getVirtualItems).mockReturnValue(
      virtualItems as unknown as ReturnType<
        typeof mockVirtualizer.getVirtualItems
      >,
    );

    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: true,
        isLoading: false,
        loadMore: mockLoadMore,
        threshold: 5,
      }),
    );

    // index 8 >= 10 - 5 = 5, so should load more
    expect(mockLoadMore).toHaveBeenCalled();
  });

  it("should not load more when not within threshold", () => {
    const virtualItems = [
      { index: 0, start: 0, end: 100 },
      { index: 1, start: 100, end: 200 },
      { index: 3, start: 300, end: 400 }, // index 3, not within threshold of 10
    ];

    vi.mocked(mockVirtualizer.getVirtualItems).mockReturnValue(
      virtualItems as unknown as ReturnType<
        typeof mockVirtualizer.getVirtualItems
      >,
    );

    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: true,
        isLoading: false,
        loadMore: mockLoadMore,
        threshold: 5,
      }),
    );

    // index 3 < 10 - 5 = 5, so should not load more
    expect(mockLoadMore).not.toHaveBeenCalled();
  });

  it("should use default threshold of 5", () => {
    const virtualItems = [
      { index: 0, start: 0, end: 100 },
      { index: 5, start: 500, end: 600 }, // index 5, at threshold for 10 items
    ];

    vi.mocked(mockVirtualizer.getVirtualItems).mockReturnValue(
      virtualItems as unknown as ReturnType<
        typeof mockVirtualizer.getVirtualItems
      >,
    );

    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: true,
        isLoading: false,
        loadMore: mockLoadMore,
        // threshold not provided, should default to 5
      }),
    );

    // index 5 >= 10 - 5 = 5, so should load more
    expect(mockLoadMore).toHaveBeenCalled();
  });

  it("should handle custom threshold", () => {
    const virtualItems = [
      { index: 0, start: 0, end: 100 },
      { index: 7, start: 700, end: 800 }, // index 7
    ];

    vi.mocked(mockVirtualizer.getVirtualItems).mockReturnValue(
      virtualItems as unknown as ReturnType<
        typeof mockVirtualizer.getVirtualItems
      >,
    );

    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: true,
        isLoading: false,
        loadMore: mockLoadMore,
        threshold: 2,
      }),
    );

    // index 7 >= 10 - 2 = 8? No, so should not load more
    expect(mockLoadMore).not.toHaveBeenCalled();

    // But if we're at index 8 with threshold 2, should load
    const virtualItems2 = [
      { index: 0, start: 0, end: 100 },
      { index: 8, start: 800, end: 900 },
    ];

    vi.mocked(mockVirtualizer.getVirtualItems).mockReturnValue(
      virtualItems2 as unknown as ReturnType<
        typeof mockVirtualizer.getVirtualItems
      >,
    );

    const { rerender } = renderHook(
      ({ threshold }) =>
        useInfiniteScrollVirtualizer({
          virtualizer: mockVirtualizer,
          itemCount: 10,
          hasMore: true,
          isLoading: false,
          loadMore: mockLoadMore,
          threshold,
        }),
      { initialProps: { threshold: 2 } },
    );

    rerender({ threshold: 2 });

    // index 8 >= 10 - 2 = 8, so should load more
    expect(mockLoadMore).toHaveBeenCalled();
  });

  it("should not load more when virtual items array is empty", () => {
    // Empty array means no virtual items, so lastItem check is not reached
    vi.mocked(mockVirtualizer.getVirtualItems).mockReturnValue(
      [] as unknown as ReturnType<typeof mockVirtualizer.getVirtualItems>,
    );

    renderHook(() =>
      useInfiniteScrollVirtualizer({
        virtualizer: mockVirtualizer,
        itemCount: 10,
        hasMore: true,
        isLoading: false,
        loadMore: mockLoadMore,
      }),
    );

    // Should not load more when there are no virtual items
    expect(mockLoadMore).not.toHaveBeenCalled();
  });
});
