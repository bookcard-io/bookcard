import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Book } from "@/types/book";
import { useBook } from "./useBook";

describe("useBook", () => {
  const mockBook: Book = {
    id: 1,
    title: "Test Book",
    authors: ["Author 1"],
    author_sort: "Author 1",
    pubdate: null,
    timestamp: null,
    series: null,
    series_id: null,
    series_index: null,
    isbn: null,
    uuid: "uuid-1",
    thumbnail_url: "/cover.jpg",
    has_cover: true,
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with loading state", () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockBook),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBook({ bookId: 1 }));
    expect(result.current.isLoading).toBe(true);
    expect(result.current.book).toBeNull();
  });

  it("should fetch book successfully", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockBook),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBook({ bookId: 1 }));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.book).toEqual(mockBook);
    expect(result.current.error).toBeNull();
  });

  it("should fetch book with full metadata", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockBook),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    renderHook(() => useBook({ bookId: 1, full: true }));

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining("full=true"),
        expect.any(Object),
      );
    });
  });

  it("should handle fetch error", async () => {
    const mockResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Book not found" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBook({ bookId: 1 }));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Book not found");
    expect(result.current.book).toBeNull();
  });

  it("should not fetch when enabled is false", () => {
    renderHook(() => useBook({ bookId: 1, enabled: false }));
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should refetch book", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockBook),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBook({ bookId: 1 }));

    await waitFor(() => {
      expect(result.current.book).toEqual(mockBook);
    });

    const newBook = { ...mockBook, title: "Updated Title" };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(newBook),
    });

    await result.current.refetch();

    await waitFor(() => {
      expect(result.current.book?.title).toBe("Updated Title");
    });
  });

  it("should update book successfully", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockBook),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBook({ bookId: 1 }));

    await waitFor(() => {
      expect(result.current.book).toEqual(mockBook);
    });

    const updatedBook = { ...mockBook, title: "Updated Title" };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(updatedBook),
    });

    const updateResult = await result.current.updateBook({
      title: "Updated Title",
    });

    await waitFor(() => {
      expect(result.current.book?.title).toBe("Updated Title");
      expect(updateResult?.title).toBe("Updated Title");
      expect(result.current.isUpdating).toBe(false);
    });
  });

  it("should handle update error", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockBook),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useBook({ bookId: 1 }));

    await waitFor(() => {
      expect(result.current.book).toEqual(mockBook);
    });

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Update failed" }),
    });

    const updateResult = await result.current.updateBook({
      title: "Updated Title",
    });

    await waitFor(() => {
      expect(result.current.updateError).toBe("Update failed");
      expect(updateResult).toBeNull();
      expect(result.current.isUpdating).toBe(false);
    });
  });

  it("should return null when updating book with no bookId", async () => {
    const { result } = renderHook(() => useBook({ bookId: 0 }));

    const updateResult = await result.current.updateBook({
      title: "Updated Title",
    });

    expect(updateResult).toBeNull();
  });
});
