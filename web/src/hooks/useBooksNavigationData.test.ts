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
import { describe, expect, it, vi } from "vitest";
import { useBooksNavigationData } from "./useBooksNavigationData";

describe("useBooksNavigationData", () => {
  it("should call onBooksDataChange on first render", () => {
    const onBooksDataChange = vi.fn();
    const bookIds = [1, 2, 3];

    renderHook(() =>
      useBooksNavigationData({
        bookIds,
        isLoading: false,
        onBooksDataChange,
      }),
    );

    expect(onBooksDataChange).toHaveBeenCalledWith({
      bookIds,
      loadMore: undefined,
      hasMore: undefined,
      isLoading: false,
    });
  });

  it("should call onBooksDataChange when bookIds change", () => {
    const onBooksDataChange = vi.fn();
    const { rerender } = renderHook(
      ({ bookIds }) =>
        useBooksNavigationData({
          bookIds,
          isLoading: false,
          onBooksDataChange,
        }),
      {
        initialProps: { bookIds: [1, 2, 3] },
      },
    );

    onBooksDataChange.mockClear();

    rerender({ bookIds: [1, 2, 3, 4] });

    expect(onBooksDataChange).toHaveBeenCalledWith({
      bookIds: [1, 2, 3, 4],
      loadMore: undefined,
      hasMore: undefined,
      isLoading: false,
    });
  });

  it("should call onBooksDataChange when bookIds order changes", () => {
    const onBooksDataChange = vi.fn();
    const { rerender } = renderHook(
      ({ bookIds }) =>
        useBooksNavigationData({
          bookIds,
          isLoading: false,
          onBooksDataChange,
        }),
      {
        initialProps: { bookIds: [1, 2, 3] },
      },
    );

    onBooksDataChange.mockClear();

    rerender({ bookIds: [3, 2, 1] });

    expect(onBooksDataChange).toHaveBeenCalledWith({
      bookIds: [3, 2, 1],
      loadMore: undefined,
      hasMore: undefined,
      isLoading: false,
    });
  });

  it("should call onBooksDataChange when hasMore changes", () => {
    const onBooksDataChange = vi.fn();
    const { rerender } = renderHook(
      ({ hasMore }) =>
        useBooksNavigationData({
          bookIds: [1, 2, 3],
          isLoading: false,
          hasMore,
          onBooksDataChange,
        }),
      {
        initialProps: { hasMore: false },
      },
    );

    onBooksDataChange.mockClear();

    rerender({ hasMore: true });

    expect(onBooksDataChange).toHaveBeenCalledWith({
      bookIds: [1, 2, 3],
      loadMore: undefined,
      hasMore: true,
      isLoading: false,
    });
  });

  it("should call onBooksDataChange when isLoading changes", () => {
    const onBooksDataChange = vi.fn();
    const { rerender } = renderHook(
      ({ isLoading }) =>
        useBooksNavigationData({
          bookIds: [1, 2, 3],
          isLoading,
          onBooksDataChange,
        }),
      {
        initialProps: { isLoading: false },
      },
    );

    onBooksDataChange.mockClear();

    rerender({ isLoading: true });

    expect(onBooksDataChange).toHaveBeenCalledWith({
      bookIds: [1, 2, 3],
      loadMore: undefined,
      hasMore: undefined,
      isLoading: true,
    });
  });

  it("should not call onBooksDataChange when data unchanged", () => {
    const onBooksDataChange = vi.fn();
    const { rerender } = renderHook(
      ({ bookIds }) =>
        useBooksNavigationData({
          bookIds,
          isLoading: false,
          onBooksDataChange,
        }),
      {
        initialProps: { bookIds: [1, 2, 3] },
      },
    );

    onBooksDataChange.mockClear();

    rerender({ bookIds: [1, 2, 3] });

    expect(onBooksDataChange).not.toHaveBeenCalled();
  });

  it("should handle undefined onBooksDataChange", () => {
    const { rerender } = renderHook(
      ({ bookIds }) =>
        useBooksNavigationData({
          bookIds,
          isLoading: false,
        }),
      {
        initialProps: { bookIds: [1, 2, 3] },
      },
    );

    // Should not throw
    rerender({ bookIds: [1, 2, 3, 4] });
  });

  it("should update callback ref when onBooksDataChange changes", () => {
    const onBooksDataChange1 = vi.fn();
    const onBooksDataChange2 = vi.fn();
    const { rerender } = renderHook(
      ({ callback, bookIds }) =>
        useBooksNavigationData({
          bookIds,
          isLoading: false,
          onBooksDataChange: callback,
        }),
      {
        initialProps: { callback: onBooksDataChange1, bookIds: [1, 2, 3] },
      },
    );

    onBooksDataChange1.mockClear();

    rerender({ callback: onBooksDataChange2, bookIds: [1, 2, 3] });

    // Trigger a data change to verify new callback is used
    rerender({ callback: onBooksDataChange2, bookIds: [1, 2, 3, 4] });
    expect(onBooksDataChange2).toHaveBeenCalled();
  });
});
