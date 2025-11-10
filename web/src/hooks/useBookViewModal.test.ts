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

  it("should navigate to next book after loading more books", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2];
    const { result, rerender } = renderHook(
      ({ bookIds: ids }) =>
        useBookViewModal({
          bookIds: ids,
          loadMore,
          hasMore: true,
          isLoading: false,
        }),
      { initialProps: { bookIds } },
    );

    act(() => {
      result.current.handleBookClick({ id: 2 });
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    expect(loadMore).toHaveBeenCalled();
    expect(result.current.viewingBookId).toBe(2); // Still on 2, waiting for load

    // Simulate books being loaded
    rerender({ bookIds: [1, 2, 3] });

    // Should navigate to next book (3)
    expect(result.current.viewingBookId).toBe(3);
  });

  it("should not navigate when currentIndex is not found", () => {
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() => useBookViewModal({ bookIds }));

    act(() => {
      result.current.handleBookClick({ id: 999 }); // ID not in list
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    // Should not navigate
    expect(result.current.viewingBookId).toBe(999);
  });

  it("should not navigate previous when viewingBookId is null", () => {
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() => useBookViewModal({ bookIds }));

    act(() => {
      result.current.handleNavigatePrevious();
    });

    expect(result.current.viewingBookId).toBeNull();
  });

  it("should not navigate next when at last book and hasMore is false", () => {
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() =>
      useBookViewModal({
        bookIds,
        hasMore: false,
        isLoading: false,
      }),
    );

    act(() => {
      result.current.handleBookClick({ id: 3 });
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    expect(result.current.viewingBookId).toBe(3); // Should not change
  });

  it("should not load more when isLoading is true", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2, 3];
    const { result } = renderHook(() =>
      useBookViewModal({
        bookIds,
        hasMore: true,
        isLoading: true,
        loadMore,
      }),
    );

    act(() => {
      result.current.handleBookClick({ id: 3 });
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    // Should not load more when loading, but can still navigate within existing list
    expect(loadMore).not.toHaveBeenCalled();
    // Navigation within existing list is still allowed
    expect(result.current.viewingBookId).toBe(3); // Stays at end since can't load more
  });

  it("should load more when navigating near end with preloadThreshold", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2, 3, 4, 5];
    const { result } = renderHook(() =>
      useBookViewModal({
        bookIds,
        loadMore,
        hasMore: true,
        isLoading: false,
        preloadThreshold: 2,
      }),
    );

    act(() => {
      result.current.handleBookClick({ id: 3 });
    });

    // Should trigger loadMore when within threshold (3 is 2 away from end)
    act(() => {
      result.current.handleNavigateNext();
    });

    expect(loadMore).toHaveBeenCalled();
  });

  it("should navigate to next book after loading more books", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2];
    const { result, rerender } = renderHook(
      ({ bookIds: ids }) =>
        useBookViewModal({
          bookIds: ids,
          loadMore,
          hasMore: true,
          isLoading: false,
        }),
      { initialProps: { bookIds } },
    );

    act(() => {
      result.current.handleBookClick({ id: 2 });
    });

    // Trigger load more by navigating next
    act(() => {
      result.current.handleNavigateNext();
    });

    expect(loadMore).toHaveBeenCalled();
    expect(result.current.viewingBookId).toBe(2); // Still on 2, waiting for load

    // Simulate books being loaded (more than before)
    rerender({ bookIds: [1, 2, 3, 4] });

    // Should navigate to next book (3)
    expect(result.current.viewingBookId).toBe(3);
  });

  it("should not navigate if nextIndex is out of bounds after loading", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2];
    const { result, rerender } = renderHook(
      ({ bookIds: ids }) =>
        useBookViewModal({
          bookIds: ids,
          loadMore,
          hasMore: true,
          isLoading: false,
        }),
      { initialProps: { bookIds } },
    );

    act(() => {
      result.current.handleBookClick({ id: 2 });
    });

    // Trigger load more
    act(() => {
      result.current.handleNavigateNext();
    });

    // Simulate books being loaded but current book is no longer in the list
    rerender({ bookIds: [3, 4, 5] });

    // Should not navigate if currentIndex is not found
    expect(result.current.viewingBookId).toBe(2);
  });

  it("should not navigate previous when bookIds is empty", () => {
    const { result } = renderHook(() => useBookViewModal({ bookIds: [] }));

    act(() => {
      result.current.handleBookClick({ id: 1 });
    });

    act(() => {
      result.current.handleNavigatePrevious();
    });

    // Should not navigate when bookIds is empty
    expect(result.current.viewingBookId).toBe(1);
  });

  it("should handle case where viewingBookId is null when books are loaded", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2];
    const { result, rerender } = renderHook(
      ({ bookIds: ids }) =>
        useBookViewModal({
          bookIds: ids,
          loadMore,
          hasMore: true,
          isLoading: false,
        }),
      { initialProps: { bookIds } },
    );

    // Start navigation to trigger loadMore and set pendingNavigation
    act(() => {
      result.current.handleBookClick({ id: 2 });
    });

    act(() => {
      result.current.handleNavigateNext();
    });

    // Close modal (sets viewingBookId to null)
    act(() => {
      result.current.handleCloseModal();
    });

    // Simulate books being loaded - should not navigate since viewingBookId is null
    // (indexOf(null || -1) = indexOf(-1) = -1, so currentIndex >= 0 is false)
    rerender({ bookIds: [1, 2, 3] });

    // Should remain null
    expect(result.current.viewingBookId).toBeNull();
  });

  it("should navigate to next book when nextIndex is within bounds", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2];
    const { result, rerender } = renderHook(
      ({ bookIds: ids }) =>
        useBookViewModal({
          bookIds: ids,
          loadMore,
          hasMore: true,
          isLoading: false,
        }),
      { initialProps: { bookIds } },
    );

    act(() => {
      result.current.handleBookClick({ id: 1 });
    });

    // Trigger load more
    act(() => {
      result.current.handleNavigateNext();
    });

    // Simulate books being loaded - now book 1 is at index 0, next should be index 1
    rerender({ bookIds: [1, 2, 3] });

    // Should navigate to next book (2) since nextIndex (1) < bookIds.length (3)
    expect(result.current.viewingBookId).toBe(2);
  });

  it("should not navigate when nextIndex equals bookIds.length", () => {
    const loadMore = vi.fn();
    const bookIds = [1, 2];
    const { result, rerender } = renderHook(
      ({ bookIds: ids }) =>
        useBookViewModal({
          bookIds: ids,
          loadMore,
          hasMore: true,
          isLoading: false,
        }),
      { initialProps: { bookIds } },
    );

    act(() => {
      result.current.handleBookClick({ id: 2 });
    });

    // Trigger load more
    act(() => {
      result.current.handleNavigateNext();
    });

    // Simulate books being loaded - book 2 is at index 1, nextIndex would be 2
    // If bookIds.length is 2, nextIndex (2) is not < bookIds.length (2)
    rerender({ bookIds: [1, 2] }); // Same length, so nextIndex would be out of bounds

    // Should not navigate if nextIndex >= bookIds.length
    expect(result.current.viewingBookId).toBe(2);
  });
});
