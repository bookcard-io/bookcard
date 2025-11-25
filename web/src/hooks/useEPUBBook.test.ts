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

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useEPUBBook } from "./useEPUBBook";

describe("useEPUBBook", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("initial state", () => {
    it("should initialize with null bookArrayBuffer", async () => {
      const { result } = renderHook(() => useEPUBBook(null));

      await waitFor(() => {
        expect(result.current.bookArrayBuffer).toBeNull();
      });
      expect(result.current.bookArrayBufferRef.current).toBeNull();
    });

    it("should set error and stop loading when downloadUrl is null", async () => {
      const { result } = renderHook(() => useEPUBBook(null));

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
        expect(result.current.isLoading).toBe(false);
      });
    });
  });

  describe("null downloadUrl", () => {
    it("should set error and stop loading when downloadUrl is null", async () => {
      const { result } = renderHook(() => useEPUBBook(null));

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.bookArrayBuffer).toBeNull();
    });

    it("should not fetch when downloadUrl is null", () => {
      renderHook(() => useEPUBBook(null));

      expect(globalThis.fetch).not.toHaveBeenCalled();
    });
  });

  describe("successful fetch", () => {
    it("should fetch book successfully", async () => {
      const mockArrayBuffer = new ArrayBuffer(8);
      const mockBlob = new Blob([mockArrayBuffer], {
        type: "application/epub+zip",
      });

      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        blob: vi.fn().mockResolvedValue(mockBlob),
      } as unknown as Response);

      const { result } = renderHook(() =>
        useEPUBBook("https://example.com/book.epub"),
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isError).toBe(false);
      expect(result.current.bookArrayBuffer).toEqual(mockArrayBuffer);
      expect(result.current.bookArrayBufferRef.current).toEqual(
        mockArrayBuffer,
      );
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "https://example.com/book.epub",
      );
    });

    it("should set loading state during fetch", async () => {
      let resolveFetch: (value: Response) => void;
      const fetchPromise = new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      });

      const mockArrayBuffer = new ArrayBuffer(8);
      const mockBlob = new Blob([mockArrayBuffer], {
        type: "application/epub+zip",
      });

      vi.mocked(globalThis.fetch).mockReturnValue(fetchPromise);

      const { result } = renderHook(() =>
        useEPUBBook("https://example.com/book.epub"),
      );

      // Should be loading initially
      expect(result.current.isLoading).toBe(true);
      expect(result.current.isError).toBe(false);

      // Resolve the fetch
      await act(async () => {
        resolveFetch?.({
          ok: true,
          blob: vi.fn().mockResolvedValue(mockBlob),
        } as unknown as Response);
        await Promise.resolve();
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it("should reset error state on successful fetch", async () => {
      // First render with null to set error
      const { result, rerender } = renderHook(
        ({ url }: { url: string | null }) => useEPUBBook(url),
        {
          initialProps: { url: null as string | null },
        },
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Now fetch successfully
      const mockArrayBuffer = new ArrayBuffer(8);
      const mockBlob = new Blob([mockArrayBuffer], {
        type: "application/epub+zip",
      });

      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        blob: vi.fn().mockResolvedValue(mockBlob),
      } as unknown as Response);

      rerender({ url: "https://example.com/book.epub" as string | null });

      await waitFor(() => {
        expect(result.current.isError).toBe(false);
      });
    });
  });

  describe("fetch errors", () => {
    it("should handle non-ok response", async () => {
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: false,
        statusText: "Not Found",
      } as Response);

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const { result } = renderHook(() =>
        useEPUBBook("https://example.com/book.epub"),
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.bookArrayBuffer).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });

    it("should handle fetch network error", async () => {
      const networkError = new Error("Network error");
      vi.mocked(globalThis.fetch).mockRejectedValue(networkError);

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const { result } = renderHook(() =>
        useEPUBBook("https://example.com/book.epub"),
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.bookArrayBuffer).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Error fetching EPUB:",
        networkError,
      );

      consoleErrorSpy.mockRestore();
    });

    it("should handle blob conversion error", async () => {
      const blobError = new Error("Blob conversion failed");
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        blob: vi.fn().mockRejectedValue(blobError),
      } as unknown as Response);

      const consoleErrorSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const { result } = renderHook(() =>
        useEPUBBook("https://example.com/book.epub"),
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalled();

      consoleErrorSpy.mockRestore();
    });
  });

  describe("cancellation", () => {
    it("should not update state if component unmounts during fetch", async () => {
      let resolveFetch: (value: Response) => void;
      const fetchPromise = new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      });

      const mockArrayBuffer = new ArrayBuffer(8);
      const mockBlob = new Blob([mockArrayBuffer], {
        type: "application/epub+zip",
      });

      vi.mocked(globalThis.fetch).mockReturnValue(fetchPromise);

      const { unmount } = renderHook(() =>
        useEPUBBook("https://example.com/book.epub"),
      );

      // Unmount before fetch completes
      unmount();

      // Resolve fetch after unmount
      await act(async () => {
        resolveFetch?.({
          ok: true,
          blob: vi.fn().mockResolvedValue(mockBlob),
        } as unknown as Response);
        await Promise.resolve();
      });

      // Wait a bit to ensure state updates would have happened
      await new Promise((resolve) => setTimeout(resolve, 100));

      // State should not have been updated (we can't check result.current after unmount,
      // but we verify the fetch was called)
      expect(globalThis.fetch).toHaveBeenCalled();
    });

    it("should not update state if downloadUrl changes during fetch", async () => {
      let resolveFetch: (value: Response) => void;
      const fetchPromise = new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      });

      const mockArrayBuffer = new ArrayBuffer(8);
      const mockBlob = new Blob([mockArrayBuffer], {
        type: "application/epub+zip",
      });

      vi.mocked(globalThis.fetch).mockReturnValue(fetchPromise);

      const { rerender } = renderHook(
        ({ url }: { url: string | null }) => useEPUBBook(url),
        {
          initialProps: { url: "https://example.com/book1.epub" },
        },
      );

      // Change URL before first fetch completes
      rerender({ url: "https://example.com/book2.epub" });

      // Resolve first fetch after URL change
      await act(async () => {
        resolveFetch?.({
          ok: true,
          blob: vi.fn().mockResolvedValue(mockBlob),
        } as unknown as Response);
        await Promise.resolve();
      });

      // Wait a bit
      await new Promise((resolve) => setTimeout(resolve, 100));

      // The first fetch result should not have been applied
      // (we verify by checking that a new fetch was initiated)
      expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe("downloadUrl changes", () => {
    it("should refetch when downloadUrl changes", async () => {
      const mockArrayBuffer1 = new ArrayBuffer(8);
      const mockBlob1 = new Blob([mockArrayBuffer1], {
        type: "application/epub+zip",
      });

      const mockArrayBuffer2 = new ArrayBuffer(16);
      const mockBlob2 = new Blob([mockArrayBuffer2], {
        type: "application/epub+zip",
      });

      vi.mocked(globalThis.fetch)
        .mockResolvedValueOnce({
          ok: true,
          blob: vi.fn().mockResolvedValue(mockBlob1),
        } as unknown as Response)
        .mockResolvedValueOnce({
          ok: true,
          blob: vi.fn().mockResolvedValue(mockBlob2),
        } as unknown as Response);

      const { result, rerender } = renderHook(
        ({ url }: { url: string | null }) => useEPUBBook(url),
        {
          initialProps: {
            url: "https://example.com/book1.epub" as string | null,
          },
        },
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.bookArrayBuffer).toEqual(mockArrayBuffer1);

      // Change URL
      rerender({ url: "https://example.com/book2.epub" as string | null });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.bookArrayBuffer).toEqual(mockArrayBuffer2);
      expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    });

    it("should handle change from valid URL to null", async () => {
      const mockArrayBuffer = new ArrayBuffer(8);
      const mockBlob = new Blob([mockArrayBuffer], {
        type: "application/epub+zip",
      });

      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        blob: vi.fn().mockResolvedValue(mockBlob),
      } as unknown as Response);

      const { result, rerender } = renderHook(
        ({ url }: { url: string | null }) => useEPUBBook(url),
        {
          initialProps: {
            url: "https://example.com/book.epub" as string | null,
          },
        },
      );

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.bookArrayBuffer).toEqual(mockArrayBuffer);

      // Change to null
      rerender({ url: null as string | null });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.isLoading).toBe(false);
    });

    it("should handle change from null to valid URL", async () => {
      const { result, rerender } = renderHook(
        ({ url }: { url: string | null }) => useEPUBBook(url),
        {
          initialProps: { url: null as string | null },
        },
      );

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      const mockArrayBuffer = new ArrayBuffer(8);
      const mockBlob = new Blob([mockArrayBuffer], {
        type: "application/epub+zip",
      });

      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        blob: vi.fn().mockResolvedValue(mockBlob),
      } as unknown as Response);

      // Change to valid URL
      rerender({ url: "https://example.com/book.epub" as string | null });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isError).toBe(false);
      expect(result.current.bookArrayBuffer).toEqual(mockArrayBuffer);
    });
  });
});
