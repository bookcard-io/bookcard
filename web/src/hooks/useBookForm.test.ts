import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Book } from "@/types/book";
import { useBookForm } from "./useBookForm";

describe("useBookForm", () => {
  const mockBook: Book = {
    id: 1,
    title: "Test Book",
    authors: ["Author 1"],
    author_sort: "Author 1",
    pubdate: "2024-01-15T00:00:00Z",
    timestamp: null,
    series: "Test Series",
    series_id: 1,
    series_index: 1,
    isbn: null,
    uuid: "uuid-1",
    thumbnail_url: null,
    has_cover: false,
    tags: ["tag1"],
    description: "Description",
    publisher: "Publisher",
    languages: ["en"],
    rating: 4,
  };

  let updateBook: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    updateBook = vi.fn().mockResolvedValue(mockBook);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize form data from book", () => {
    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook }),
    );

    expect(result.current.formData.title).toBe("Test Book");
    expect(result.current.formData.author_names).toEqual(["Author 1"]);
    expect(result.current.hasChanges).toBe(false);
  });

  it("should extract date part from ISO string", () => {
    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook }),
    );

    expect(result.current.formData.pubdate).toBe("2024-01-15");
  });

  it("should handle field changes", () => {
    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook }),
    );

    act(() => {
      result.current.handleFieldChange("title", "Updated Title");
    });

    expect(result.current.formData.title).toBe("Updated Title");
    expect(result.current.hasChanges).toBe(true);
  });

  it("should submit form and update book", async () => {
    const onUpdateSuccess = vi.fn();
    const updatedBook = { ...mockBook, title: "Updated Title" };
    updateBook.mockResolvedValue(updatedBook);

    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook, onUpdateSuccess }),
    );

    act(() => {
      result.current.handleFieldChange("title", "Updated Title");
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Updated Title",
        pubdate: "2024-01-15T00:00:00Z",
      }),
    );
    expect(result.current.hasChanges).toBe(false);
    expect(result.current.showSuccess).toBe(true);
    expect(onUpdateSuccess).toHaveBeenCalledWith(updatedBook);
  });

  it("should convert date string to ISO format on submit", async () => {
    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook }),
    );

    act(() => {
      result.current.handleFieldChange("pubdate", "2024-12-25");
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        pubdate: "2024-12-25T00:00:00Z",
      }),
    );
  });

  it("should clean up empty arrays on submit", async () => {
    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook }),
    );

    act(() => {
      result.current.handleFieldChange("author_names", []);
      result.current.handleFieldChange("tag_names", []);
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        author_names: null,
        tag_names: null,
      }),
    );
  });

  it("should reset form to initial state", () => {
    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook }),
    );

    act(() => {
      result.current.handleFieldChange("title", "Changed Title");
    });

    expect(result.current.hasChanges).toBe(true);

    act(() => {
      result.current.resetForm();
    });

    expect(result.current.formData.title).toBe("Test Book");
    expect(result.current.hasChanges).toBe(false);
  });

  it("should not reset if no changes", () => {
    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook }),
    );

    const initialData = { ...result.current.formData };

    act(() => {
      result.current.resetForm();
    });

    expect(result.current.formData).toEqual(initialData);
  });

  it("should handle book update and refresh form", async () => {
    const updatedBook = { ...mockBook, title: "Updated Title" };
    updateBook.mockResolvedValue(updatedBook);

    const { result, rerender } = renderHook(
      ({ book }) => useBookForm({ book, updateBook }),
      { initialProps: { book: mockBook } },
    );

    act(() => {
      result.current.handleFieldChange("title", "Updated Title");
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    rerender({ book: updatedBook });

    // Form should update after rerender
    expect(result.current.formData.title).toBe("Updated Title");
  });

  it("should hide success message after timeout", async () => {
    vi.useFakeTimers();
    const { result } = renderHook(() =>
      useBookForm({ book: mockBook, updateBook }),
    );

    act(() => {
      result.current.handleFieldChange("title", "Updated Title");
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(result.current.showSuccess).toBe(true);

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.showSuccess).toBe(false);

    vi.useRealTimers();
  });

  it("should not submit if book is null", async () => {
    const { result } = renderHook(() =>
      useBookForm({ book: null, updateBook }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(updateBook).not.toHaveBeenCalled();
  });
});
