import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useBookCoverFromUrl } from "./useBookCoverFromUrl";

// Mock the dependencies
vi.mock("./useCoverFromUrl", () => ({
  useCoverFromUrl: vi.fn(),
}));

vi.mock("./useCoverUrlInput", () => ({
  useCoverUrlInput: vi.fn(),
}));

import { useCoverFromUrl } from "./useCoverFromUrl";
import { useCoverUrlInput } from "./useCoverUrlInput";

describe("useBookCoverFromUrl", () => {
  let mockDownloadCover: ReturnType<typeof vi.fn>;
  let mockClearError: ReturnType<typeof vi.fn>;
  let mockUrlInput: {
    isVisible: boolean;
    value: string;
    show: () => void;
    hide: () => void;
    handleChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  };

  beforeEach(() => {
    mockDownloadCover = vi.fn().mockResolvedValue(undefined);
    mockClearError = vi.fn();
    mockUrlInput = {
      isVisible: false,
      value: "",
      show: vi.fn(),
      hide: vi.fn(),
      handleChange: vi.fn(),
    };

    (useCoverFromUrl as ReturnType<typeof vi.fn>).mockReturnValue({
      isLoading: false,
      error: null,
      downloadCover: mockDownloadCover,
      clearError: mockClearError,
    });

    (useCoverUrlInput as ReturnType<typeof vi.fn>).mockReturnValue(
      mockUrlInput,
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return loading and error from useCoverFromUrl", () => {
    (useCoverFromUrl as ReturnType<typeof vi.fn>).mockReturnValue({
      isLoading: true,
      error: "Test error",
      downloadCover: mockDownloadCover,
      clearError: mockClearError,
    });

    const { result } = renderHook(() => useBookCoverFromUrl({ bookId: 1 }));

    expect(result.current.isLoading).toBe(true);
    expect(result.current.error).toBe("Test error");
  });

  it("should handle URL change", () => {
    const { result } = renderHook(() => useBookCoverFromUrl({ bookId: 1 }));

    const event = {
      target: { value: "https://example.com/cover.jpg" },
    } as React.ChangeEvent<HTMLInputElement>;

    act(() => {
      result.current.handleUrlChange(event);
    });

    expect(mockUrlInput.handleChange).toHaveBeenCalledWith(event);
    expect(mockClearError).toHaveBeenCalled();
  });

  it("should show input when clicking set from URL button", () => {
    const { result } = renderHook(() => useBookCoverFromUrl({ bookId: 1 }));

    act(() => {
      result.current.handleSetFromUrlClick();
    });

    expect(mockUrlInput.show).toHaveBeenCalled();
  });

  it("should submit URL when input has value and is visible", async () => {
    mockUrlInput.isVisible = true;
    mockUrlInput.value = "https://example.com/cover.jpg";

    const { result } = renderHook(() => useBookCoverFromUrl({ bookId: 1 }));

    await act(async () => {
      result.current.handleSetFromUrlClick();
    });

    await waitFor(() => {
      expect(mockDownloadCover).toHaveBeenCalledWith(
        "https://example.com/cover.jpg",
      );
    });
  });

  it("should hide input when clicking button and input is empty", () => {
    mockUrlInput.isVisible = true;
    mockUrlInput.value = "";

    const { result } = renderHook(() => useBookCoverFromUrl({ bookId: 1 }));

    act(() => {
      result.current.handleSetFromUrlClick();
    });

    expect(mockUrlInput.hide).toHaveBeenCalled();
  });

  it("should call onCoverSaved when cover is downloaded", async () => {
    const onCoverSaved = vi.fn();
    const { result } = renderHook(() =>
      useBookCoverFromUrl({ bookId: 1, onCoverSaved }),
    );

    await act(async () => {
      await result.current.downloadCover("https://example.com/cover.jpg");
    });

    await waitFor(() => {
      expect(mockDownloadCover).toHaveBeenCalled();
    });
  });

  it("should call onUrlInputVisibilityChange when visibility changes", () => {
    const onUrlInputVisibilityChange = vi.fn();
    (useCoverUrlInput as ReturnType<typeof vi.fn>).mockImplementation(
      (options) => {
        return {
          ...mockUrlInput,
          show: () => {
            mockUrlInput.isVisible = true;
            options?.onVisibilityChange?.(true);
          },
        };
      },
    );

    const { result } = renderHook(() =>
      useBookCoverFromUrl({
        bookId: 1,
        onUrlInputVisibilityChange,
      }),
    );

    // Trigger visibility change
    act(() => {
      result.current.urlInput.show();
    });

    expect(onUrlInputVisibilityChange).toHaveBeenCalledWith(true);
  });

  it("should not download when already loading", async () => {
    (useCoverFromUrl as ReturnType<typeof vi.fn>).mockReturnValue({
      isLoading: true,
      error: null,
      downloadCover: mockDownloadCover,
      clearError: mockClearError,
    });

    const { result } = renderHook(() => useBookCoverFromUrl({ bookId: 1 }));

    await act(async () => {
      await result.current.downloadCover("https://example.com/cover.jpg");
    });

    expect(mockDownloadCover).not.toHaveBeenCalled();
  });

  it("should call onCoverSaved when cover is downloaded", async () => {
    const onCoverSaved = vi.fn().mockResolvedValue(undefined);
    (useCoverFromUrl as ReturnType<typeof vi.fn>).mockImplementation(
      (options) => {
        return {
          isLoading: false,
          error: null,
          downloadCover: vi.fn().mockImplementation(async () => {
            await options?.onSuccess?.();
          }),
          clearError: vi.fn(),
        };
      },
    );

    const { result } = renderHook(() =>
      useBookCoverFromUrl({
        bookId: 1,
        onCoverSaved,
      }),
    );

    await act(async () => {
      await result.current.downloadCover("https://example.com/cover.jpg");
    });

    await waitFor(() => {
      expect(onCoverSaved).toHaveBeenCalled();
    });
  });
});
