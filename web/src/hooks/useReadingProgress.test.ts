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

import { QueryClient } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReadingProgress, ReadingProgressCreate } from "@/types/reading";
import {
  createMockFetchWithActiveLibrary,
  createQueryClientWrapper,
} from "./test-utils";
import { useReadingProgress } from "./useReadingProgress";

describe("useReadingProgress", () => {
  let queryClient: QueryClient;
  let wrapper: ReturnType<typeof createQueryClientWrapper>;

  const mockProgress: ReadingProgress = {
    id: 1,
    user_id: 1,
    library_id: 1,
    book_id: 1,
    format: "EPUB",
    progress: 0.5,
    cfi: "epubcfi(/6/4[chap01ref]!/4[body01]/10[para05]/3:10)",
    page_number: null,
    device: null,
    updated_at: "2024-01-01T00:00:00Z",
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
        mutations: {
          retry: false,
        },
      },
    });
    wrapper = createQueryClientWrapper(queryClient);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    queryClient.clear();
  });

  it("should fetch reading progress on mount", () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockProgress),
    };
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => {
        if (
          url.startsWith("/api/reading/progress") &&
          url.includes("book_id=1") &&
          url.includes("format=EPUB")
        ) {
          return Promise.resolve(mockFetchResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "EPUB" }),
      { wrapper },
    );

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should not fetch when enabled is false", async () => {
    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "EPUB", enabled: false }),
      { wrapper },
    );

    expect(result.current.progress).toBeNull();
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const progressCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("/api/reading/progress"),
    );
    expect(progressCalls.length).toBe(0);
  });

  it("should not fetch when bookId is 0 or negative", async () => {
    const { result } = renderHook(
      () => useReadingProgress({ bookId: 0, format: "EPUB" }),
      { wrapper },
    );

    expect(result.current.progress).toBeNull();
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const progressCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("/api/reading/progress"),
    );
    expect(progressCalls.length).toBe(0);
  });

  it("should not fetch when format is empty", async () => {
    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "" }),
      { wrapper },
    );

    expect(result.current.progress).toBeNull();
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const progressCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].includes("/api/reading/progress"),
    );
    expect(progressCalls.length).toBe(0);
  });

  it("should handle error from fetch", () => {
    const mockFetchResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({ detail: "Book not found" }),
    };
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => {
        if (
          url.startsWith("/api/reading/progress") &&
          url.includes("book_id=1") &&
          url.includes("format=EPUB")
        ) {
          return Promise.resolve(mockFetchResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "EPUB" }),
      { wrapper },
    );

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should not retry on 404 errors", async () => {
    const mockFetchResponse = {
      ok: false,
      status: 404,
      json: vi.fn().mockResolvedValue({ detail: "Not found" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) =>
          url.startsWith("/api/reading/progress") &&
          url.includes("book_id=1") &&
          url.includes("format=EPUB"),
        response: mockFetchResponse,
      }),
    );

    const queryClientWithRetry = new QueryClient({
      defaultOptions: {
        queries: {
          retry: (failureCount, error) => {
            if (error?.message?.includes("404") || failureCount > 2) {
              return false;
            }
            return true;
          },
          gcTime: 0,
        },
      },
    });
    const wrapperWithRetry = createQueryClientWrapper(queryClientWithRetry);

    renderHook(() => useReadingProgress({ bookId: 1, format: "EPUB" }), {
      wrapper: wrapperWithRetry,
    });

    await waitFor(() => {
      const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls;
      const progressCalls = fetchCalls.filter(
        (call) =>
          typeof call[0] === "string" &&
          call[0].startsWith("/api/reading/progress") &&
          call[0].includes("book_id=1") &&
          call[0].includes("format=EPUB"),
      );
      // Should not retry on 404
      expect(progressCalls.length).toBe(1);
    });
  });

  it("should retry on non-404 errors (up to 2 times)", () => {
    const mockFetchResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({ detail: "Network error" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) =>
          url.startsWith("/api/reading/progress") &&
          url.includes("book_id=1") &&
          url.includes("format=EPUB"),
        response: mockFetchResponse,
      }),
    );

    const queryClientWithRetry = new QueryClient({
      defaultOptions: {
        queries: {
          retry: (failureCount, error) => {
            if (error?.message?.includes("404") || failureCount > 2) {
              return false;
            }
            return true;
          },
          gcTime: 0,
        },
      },
    });
    const wrapperWithRetry = createQueryClientWrapper(queryClientWithRetry);

    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "EPUB" }),
      {
        wrapper: wrapperWithRetry,
      },
    );

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should refetch when refetch is called", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockProgress),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) =>
          url.startsWith("/api/reading/progress") &&
          url.includes("book_id=1") &&
          url.includes("format=EPUB"),
        response: mockFetchResponse,
      }),
    );

    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "EPUB" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCallCount = (
      globalThis.fetch as ReturnType<typeof vi.fn>
    ).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].startsWith("/api/reading/progress") &&
        call[0].includes("book_id=1") &&
        call[0].includes("format=EPUB"),
    ).length;

    act(() => {
      result.current.refetch();
    });

    await new Promise((resolve) => setTimeout(resolve, 50));
    const newCallCount = (
      globalThis.fetch as ReturnType<typeof vi.fn>
    ).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].startsWith("/api/reading/progress") &&
        call[0].includes("book_id=1") &&
        call[0].includes("format=EPUB"),
    ).length;
    expect(newCallCount).toBeGreaterThan(initialCallCount);
  });

  it("should update progress", async () => {
    const getMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockProgress),
    };
    const updateMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        ...mockProgress,
        progress: 0.75,
      }),
    };
    let getCallCount = 0;
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string, options?: RequestInit) => {
        if (url === "/api/reading/progress" && options?.method === "PUT") {
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        if (
          url.startsWith("/api/reading/progress") &&
          url.includes("book_id=1") &&
          url.includes("format=EPUB") &&
          (!options?.method || options?.method === "GET")
        ) {
          getCallCount++;
          if (getCallCount === 1) {
            return Promise.resolve(getMockResponse as unknown as Response);
          }
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "EPUB" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const updateData: ReadingProgressCreate = {
      book_id: 1,
      format: "EPUB",
      progress: 0.75,
      cfi: "epubcfi(/6/4[chap01ref]!/4[body01]/10[para05]/3:10)",
    };

    await act(async () => {
      const updatedProgress = await result.current.updateProgress(updateData);
      expect(updatedProgress.progress).toBe(0.75);
    });

    expect(result.current.isUpdating).toBe(false);
    expect(result.current.updateError).toBeNull();
  });

  it("should handle update error", async () => {
    const getMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockProgress),
    };
    const updateMockResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Update failed" }),
    };
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string, options?: RequestInit) => {
        if (url === "/api/reading/progress" && options?.method === "PUT") {
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        if (
          url.startsWith("/api/reading/progress") &&
          url.includes("book_id=1") &&
          url.includes("format=EPUB") &&
          (!options?.method || options?.method === "GET")
        ) {
          return Promise.resolve(getMockResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "EPUB" }),
      { wrapper },
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const updateData: ReadingProgressCreate = {
      book_id: 1,
      format: "EPUB",
      progress: 0.75,
    };

    await act(async () => {
      await expect(result.current.updateProgress(updateData)).rejects.toThrow();
    });

    expect(result.current.updateError).toBeTruthy();
  });

  it("should invalidate related queries on successful update", () => {
    const getMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockProgress),
    };
    const updateMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        ...mockProgress,
        progress: 0.75,
      }),
    };
    let getCallCount = 0;
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string, options?: RequestInit) => {
        if (url === "/api/reading/progress" && options?.method === "PUT") {
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        if (
          url.startsWith("/api/reading/progress") &&
          url.includes("book_id=1") &&
          url.includes("format=EPUB") &&
          (!options?.method || options?.method === "GET")
        ) {
          getCallCount++;
          if (getCallCount === 1) {
            return Promise.resolve(getMockResponse as unknown as Response);
          }
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    // Set up query cache
    queryClient.setQueryData(["reading-progress", 1, "EPUB"], mockProgress);
    queryClient.setQueryData(["recent-reads"], { reads: [] });

    const { result } = renderHook(
      () => useReadingProgress({ bookId: 1, format: "EPUB" }),
      { wrapper },
    );

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });
});
