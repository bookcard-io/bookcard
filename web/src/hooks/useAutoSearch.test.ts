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
        startSearch,
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
        startSearch,
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
        startSearch,
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
        startSearch,
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
        startSearch,
        setSearchQuery,
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
          startSearch,
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
          startSearch,
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
});
