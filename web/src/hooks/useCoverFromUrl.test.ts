import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useCoverFromUrl } from "./useCoverFromUrl";

describe("useCoverFromUrl", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with loading false and no error", () => {
    const { result } = renderHook(() => useCoverFromUrl({ bookId: 1 }));
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("should download cover successfully", async () => {
    const onSuccess = vi.fn();
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        temp_url: "/temp/cover.jpg",
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useCoverFromUrl({ bookId: 1, onSuccess }),
    );

    await act(async () => {
      await result.current.downloadCover("https://example.com/cover.jpg");
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/books/1/cover-from-url",
      expect.objectContaining({
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: "https://example.com/cover.jpg" }),
      }),
    );
    expect(onSuccess).toHaveBeenCalled();
  });

  it("should handle error response", async () => {
    const mockResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({
        detail: "Failed to download cover",
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useCoverFromUrl({ bookId: 1 }));

    await act(async () => {
      try {
        await result.current.downloadCover("https://example.com/cover.jpg");
      } catch {
        // Expected to throw
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBe("Failed to download cover");
      expect(result.current.isLoading).toBe(false);
    });
  });

  it("should not download if URL is empty", async () => {
    const { result } = renderHook(() => useCoverFromUrl({ bookId: 1 }));

    await act(async () => {
      await result.current.downloadCover("");
    });

    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should not download if already loading", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        temp_url: "/temp/cover.jpg",
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useCoverFromUrl({ bookId: 1 }));

    act(() => {
      void result.current.downloadCover("https://example.com/cover1.jpg");
    });

    await act(async () => {
      await result.current.downloadCover("https://example.com/cover2.jpg");
    });

    // Should only be called once
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("should clear error", () => {
    const { result } = renderHook(() => useCoverFromUrl({ bookId: 1 }));
    act(() => {
      result.current.clearError();
    });
    expect(result.current.error).toBeNull();
  });

  it("should trim URL before sending", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        temp_url: "/temp/cover.jpg",
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useCoverFromUrl({ bookId: 1 }));

    await act(async () => {
      await result.current.downloadCover("  https://example.com/cover.jpg  ");
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/books/1/cover-from-url",
      expect.objectContaining({
        body: JSON.stringify({ url: "https://example.com/cover.jpg" }),
      }),
    );
  });
});
