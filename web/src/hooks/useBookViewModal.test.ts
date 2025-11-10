import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useBookViewModal } from "./useBookViewModal";

describe("useBookViewModal", () => {
  it("should initialize with null viewingBookId", () => {
    const { result } = renderHook(() => useBookViewModal());
    expect(result.current.viewingBookId).toBeNull();
  });

  it("should open modal with book ID", () => {
    const { result } = renderHook(() => useBookViewModal());
    act(() => {
      result.current.handleBookClick({ id: 123 });
    });
    expect(result.current.viewingBookId).toBe(123);
  });

  it("should close modal", () => {
    const { result } = renderHook(() => useBookViewModal());
    act(() => {
      result.current.handleBookClick({ id: 123 });
    });
    act(() => {
      result.current.handleCloseModal();
    });
    expect(result.current.viewingBookId).toBeNull();
  });

  it("should navigate to previous book", () => {
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() => useBookViewModal({ bookIds }));

    act(() => {
      result.current.handleBookClick({ id: 2 });
    });

    act(() => {
      result.current.handleNavigatePrevious();
    });

    expect(result.current.viewingBookId).toBe(1);
  });

  it("should navigate to next book", () => {
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() => useBookViewModal({ bookIds }));

    act(() => {
      result.current.handleBookClick({ id: 2 });
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    expect(result.current.viewingBookId).toBe(3);
  });

  it("should not navigate previous when at first book", () => {
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() => useBookViewModal({ bookIds }));

    act(() => {
      result.current.handleBookClick({ id: 1 });
    });

    act(() => {
      result.current.handleNavigatePrevious();
    });

    expect(result.current.viewingBookId).toBe(1); // Should not change
  });

  it("should not navigate next when at last book and no more to load", () => {
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() => useBookViewModal({ bookIds }));

    act(() => {
      result.current.handleBookClick({ id: 3 });
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    expect(result.current.viewingBookId).toBe(3); // Should not change
  });

  it("should load more books when navigating near end", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() =>
      useBookViewModal({
        bookIds,
        loadMore,
        hasMore: true,
        isLoading: false,
        preloadThreshold: 3,
      }),
    );

    act(() => {
      result.current.handleBookClick({ id: 1 });
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    expect(loadMore).toHaveBeenCalled();
  });

  it("should load more books when at end and hasMore is true", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() =>
      useBookViewModal({
        bookIds,
        loadMore,
        hasMore: true,
        isLoading: false,
      }),
    );

    act(() => {
      result.current.handleBookClick({ id: 3 });
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    expect(loadMore).toHaveBeenCalled();
  });

  it("should not navigate when bookIds is empty", () => {
    const { result } = renderHook(() => useBookViewModal({ bookIds: [] }));

    act(() => {
      result.current.handleNavigateNext();
    });

    expect(result.current.viewingBookId).toBeNull();
  });

  it("should not navigate when viewingBookId is null", () => {
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() => useBookViewModal({ bookIds }));

    act(() => {
      result.current.handleNavigateNext();
    });

    expect(result.current.viewingBookId).toBeNull();
  });
});
