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
import { useAutoSearch } from "./useAutoSearch";

describe("useAutoSearch", () => {
  let startSearch: ReturnType<typeof vi.fn>;
  let setSearchQuery: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    startSearch = vi.fn();
    setSearchQuery = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should not search when enabled is false", () => {
    renderHook(() =>
      useAutoSearch({
        initialQuery: "test",
        startSearch: startSearch as (overrideQuery?: string) => void,
        enabled: false,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(startSearch).not.toHaveBeenCalled();
  });

  it("should not search when initialQuery is null", () => {
    renderHook(() =>
      useAutoSearch({
        initialQuery: null,
        startSearch: startSearch as (overrideQuery?: string) => void,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(startSearch).not.toHaveBeenCalled();
  });

  it("should not search when initialQuery is empty", () => {
    renderHook(() =>
      useAutoSearch({
        initialQuery: "   ",
        startSearch: startSearch as (overrideQuery?: string) => void,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(startSearch).not.toHaveBeenCalled();
  });

  it("should auto-search with initial query", () => {
    renderHook(() =>
      useAutoSearch({
        initialQuery: "test query",
        startSearch: startSearch as (overrideQuery?: string) => void,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(startSearch).toHaveBeenCalledWith("test query");
  });

  it("should update search query if setSearchQuery is provided", () => {
    renderHook(() =>
      useAutoSearch({
        initialQuery: "test query",
        startSearch: startSearch as (overrideQuery?: string) => void,
        setSearchQuery: setSearchQuery as (query: string) => void,
      }),
    );

    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(setSearchQuery).toHaveBeenCalledWith("test query");
    expect(startSearch).toHaveBeenCalledWith("test query");
  });

  it("should only search once even if initialQuery changes", () => {
    const { rerender } = renderHook(
      ({ initialQuery }) =>
        useAutoSearch({
          initialQuery,
          startSearch: startSearch as (overrideQuery?: string) => void,
        }),
      { initialProps: { initialQuery: "query1" } },
    );

    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(startSearch).toHaveBeenCalledTimes(1);

    rerender({ initialQuery: "query2" });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(startSearch).toHaveBeenCalledTimes(1); // Still only once
  });

  it("should use latest startSearch function via ref", () => {
    const startSearch1 = vi.fn();
    const startSearch2 = vi.fn();

    const { rerender } = renderHook(
      ({ startSearch }) =>
        useAutoSearch({
          initialQuery: "test",
          startSearch: startSearch as (overrideQuery?: string) => void,
        }),
      { initialProps: { startSearch: startSearch1 } },
    );

    rerender({ startSearch: startSearch2 });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(startSearch2).toHaveBeenCalledWith("test");
    expect(startSearch1).not.toHaveBeenCalled();
  });

  it("should not search again if hasAutoSearchedRef is true", () => {
    const { rerender } = renderHook(
      ({ initialQuery }) =>
        useAutoSearch({
          initialQuery,
          startSearch: startSearch as (overrideQuery?: string) => void,
        }),
      { initialProps: { initialQuery: "query1" } },
    );

    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(startSearch).toHaveBeenCalledTimes(1);

    // Change query and advance timer - should not search again due to guard
    rerender({ initialQuery: "query2" });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    // Should still be 1 because hasAutoSearchedRef prevents second search
    expect(startSearch).toHaveBeenCalledTimes(1);
  });

  it("should not search if hasAutoSearchedRef becomes true during timeout", () => {
    const startSearch1 = vi.fn();
    const startSearch2 = vi.fn();

    const { rerender } = renderHook(
      ({ startSearch }) =>
        useAutoSearch({
          initialQuery: "test",
          startSearch: startSearch as (overrideQuery?: string) => void,
        }),
      { initialProps: { startSearch: startSearch1 } },
    );

    // Advance timer partway
    act(() => {
      vi.advanceTimersByTime(50);
    });

    // Change startSearch function - this will trigger the effect again
    // but the guard should prevent double search
    rerender({ startSearch: startSearch2 });

    // Advance timer to complete
    act(() => {
      vi.advanceTimersByTime(50);
    });

    // Should only be called once (by startSearch1 or startSearch2, but not both)
    expect(
      startSearch1.mock.calls.length + startSearch2.mock.calls.length,
    ).toBe(1);
  });
});
