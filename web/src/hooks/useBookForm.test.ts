import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Book, BookUpdate } from "@/types/book";
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

  let updateBook: ReturnType<typeof vi.fn> &
    ((update: BookUpdate) => Promise<Book | null>);

  beforeEach(() => {
    updateBook = vi.fn().mockResolvedValue(mockBook) as ReturnType<
      typeof vi.fn
    > &
      ((update: BookUpdate) => Promise<Book | null>);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize form data from book", () => {
    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.title).toBe("Test Book");
    expect(result.current.formData.author_names).toEqual(["Author 1"]);
    expect(result.current.hasChanges).toBe(false);
  });

  it("should extract date part from ISO string", () => {
    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.pubdate).toBe("2024-01-15");
  });

  it("should handle field changes", () => {
    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
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
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
        onUpdateSuccess,
      }),
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
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
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
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
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
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
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
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
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
      ({ book }) =>
        useBookForm({
          book,
          updateBook: updateBook as (
            update: BookUpdate,
          ) => Promise<Book | null>,
        }),
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
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
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
      useBookForm({
        book: null,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(updateBook).not.toHaveBeenCalled();
  });

  it("should reset showSuccess when book ID changes and not just updated", () => {
    const book1 = { ...mockBook, id: 1 };
    const book2 = { ...mockBook, id: 2 };
    const { result, rerender } = renderHook(
      ({ book }) =>
        useBookForm({
          book,
          updateBook: updateBook as (
            update: BookUpdate,
          ) => Promise<Book | null>,
        }),
      { initialProps: { book: book1 } },
    );

    // Set success state
    act(() => {
      result.current.handleSubmit({
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent);
    });

    // Change to different book ID
    rerender({ book: book2 });

    // showSuccess should be reset
    expect(result.current.showSuccess).toBe(false);
  });

  it("should set language_codes to null when empty array", async () => {
    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    act(() => {
      result.current.handleFieldChange("language_codes", []);
    });

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent);
    });

    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        language_codes: null,
      }),
    );
  });

  it("should set identifiers to null when empty array", async () => {
    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    act(() => {
      result.current.handleFieldChange("identifiers", []);
    });

    await act(async () => {
      await result.current.handleSubmit({
        preventDefault: vi.fn(),
      } as unknown as React.FormEvent);
    });

    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        identifiers: null,
      }),
    );
  });

  it("should handle updateBook returning null", async () => {
    updateBook.mockResolvedValue(null);

    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
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

    expect(updateBook).toHaveBeenCalled();
    expect(result.current.hasChanges).toBe(true); // Should remain true since update failed
    expect(result.current.showSuccess).toBe(false); // Should not show success
  });

  it("should handle book with null pubdate", () => {
    const bookWithNullPubdate = {
      ...mockBook,
      pubdate: null,
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithNullPubdate,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.pubdate).toBeNull();
  });

  it("should handle book with pubdate that doesn't match date pattern", () => {
    const bookWithInvalidPubdate = {
      ...mockBook,
      pubdate: "invalid-date",
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithInvalidPubdate,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    // Should handle gracefully, pubdate might be null or the original value
    expect(result.current.formData.pubdate).toBeDefined();
  });

  it("should handle book with ISO string containing time", () => {
    const bookWithTime = {
      ...mockBook,
      pubdate: "2024-01-15T10:30:00Z",
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithTime,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.pubdate).toBe("2024-01-15");
  });

  it("should not update form when book ID hasn't changed and not just updated", () => {
    const { result, rerender } = renderHook(
      ({ book }) =>
        useBookForm({
          book,
          updateBook: updateBook as (
            update: BookUpdate,
          ) => Promise<Book | null>,
        }),
      { initialProps: { book: mockBook } },
    );

    const initialFormData = { ...result.current.formData };

    // Rerender with same book (same ID)
    rerender({ book: mockBook });

    // Form data should remain the same
    expect(result.current.formData).toEqual(initialFormData);
  });

  it("should handle book update with same ID after successful update", async () => {
    const updatedBook = { ...mockBook, title: "Updated Title" };
    updateBook.mockResolvedValue(updatedBook);

    const { result, rerender } = renderHook(
      ({ book }) =>
        useBookForm({
          book,
          updateBook: updateBook as (
            update: BookUpdate,
          ) => Promise<Book | null>,
        }),
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

    // Rerender with updated book (same ID)
    rerender({ book: updatedBook });

    // Form should reflect the updated book
    expect(result.current.formData.title).toBe("Updated Title");
  });

  it("should handle pubdate that is not a YYYY-MM-DD string on submit", async () => {
    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    act(() => {
      result.current.handleFieldChange("pubdate", "2024-01-15T10:30:00Z");
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    // Should not convert if it's already an ISO string
    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        pubdate: "2024-01-15T10:30:00Z",
      }),
    );
  });

  it("should handle book with all optional fields as null", () => {
    const bookWithNulls: Book = {
      ...mockBook,
      description: null,
      publisher: null,
      languages: undefined,
      rating: null,
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithNulls,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.description).toBeNull();
    expect(result.current.formData.publisher_name).toBeNull();
    expect(result.current.formData.language_codes).toBeNull();
    expect(result.current.formData.rating_value).toBeNull();
  });

  it("should not convert pubdate if it doesn't match YYYY-MM-DD pattern", async () => {
    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    act(() => {
      result.current.handleFieldChange("pubdate", "2024-01-15T10:30:00Z");
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    // Should not convert if it doesn't match the pattern
    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        pubdate: "2024-01-15T10:30:00Z",
      }),
    );
  });

  it("should not convert pubdate if it's null", async () => {
    const bookWithNullPubdate = {
      ...mockBook,
      pubdate: null,
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithNullPubdate,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    act(() => {
      result.current.handleFieldChange("pubdate", null);
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        pubdate: null,
      }),
    );
  });

  it("should handle book with undefined authors", () => {
    const bookWithUndefinedAuthors = {
      ...mockBook,
      authors: [],
    } as Book;

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithUndefinedAuthors,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.author_names).toEqual([]);
  });

  it("should handle book with undefined series", () => {
    const bookWithUndefinedSeries: Book = {
      ...mockBook,
      series: null,
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithUndefinedSeries,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.series_name).toBeNull();
  });

  it("should handle book with undefined series_index", () => {
    const bookWithUndefinedSeriesIndex: Book = {
      ...mockBook,
      series_index: null,
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithUndefinedSeriesIndex,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.series_index).toBeNull();
  });

  it("should handle book with undefined tags", () => {
    const bookWithUndefinedTags = {
      ...mockBook,
      tags: undefined,
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithUndefinedTags,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    expect(result.current.formData.tag_names).toEqual([]);
  });

  it("should set identifiers to null when empty array on submit", async () => {
    const { result } = renderHook(() =>
      useBookForm({
        book: mockBook,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    act(() => {
      result.current.handleFieldChange("identifiers", []);
    });

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        identifiers: null,
      }),
    );
  });

  it("should handle identifiers that is already an empty array in formData", async () => {
    const bookWithEmptyIdentifiers = {
      ...mockBook,
      identifiers: [],
    };

    const { result } = renderHook(() =>
      useBookForm({
        book: bookWithEmptyIdentifiers,
        updateBook: updateBook as (update: BookUpdate) => Promise<Book | null>,
      }),
    );

    const submitEvent = {
      preventDefault: vi.fn(),
    } as unknown as React.FormEvent;

    await act(async () => {
      await result.current.handleSubmit(submitEvent);
    });

    // Should convert empty array to null
    expect(updateBook).toHaveBeenCalledWith(
      expect.objectContaining({
        identifiers: null,
      }),
    );
  });
});
