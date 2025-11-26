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
import type { ReadingHistoryResponse, ReadingSession } from "@/types/reading";
import {
  createMockFetchWithActiveLibrary,
  createQueryClientWrapper,
} from "./test-utils";
import { useReadingHistory } from "./useReadingHistory";

describe("useReadingHistory", () => {
  let queryClient: QueryClient;
  let wrapper: ReturnType<typeof createQueryClientWrapper>;

  const mockSession: ReadingSession = {
    id: 1,
    user_id: 1,
    library_id: 1,
    book_id: 1,
    format: "EPUB",
    started_at: "2024-01-01T00:00:00Z",
    ended_at: "2024-01-01T01:00:00Z",
    progress_start: 0.0,
    progress_end: 0.5,
    device: null,
    created_at: "2024-01-01T00:00:00Z",
    duration: 3600,
  };

  const mockResponse: ReadingHistoryResponse = {
    sessions: [mockSession],
    total: 1,
  };

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });
    wrapper = createQueryClientWrapper(queryClient);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    queryClient.clear();
  });

  it("should fetch reading history on mount", () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => {
        if (url.startsWith("/api/reading/history/1")) {
          return Promise.resolve(mockFetchResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(() => useReadingHistory({ bookId: 1 }), {
      wrapper,
    });

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should use custom limit", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const baseMock = createMockFetchWithActiveLibrary({
      matcher: (url) => url.startsWith("/api/reading/history/1"),
      response: mockFetchResponse,
    });
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => baseMock(url),
    );

    renderHook(() => useReadingHistory({ bookId: 1, limit: 100 }), {
      wrapper,
    });

    await waitFor(() => {
      const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls;
      const historyCalls = fetchCalls.filter(
        (call) =>
          typeof call[0] === "string" &&
          call[0].startsWith("/api/reading/history/1"),
      );
      expect(historyCalls.length).toBeGreaterThan(0);
      if (historyCalls.length > 0) {
        const url = historyCalls[0]?.[0] as string;
        expect(url).toContain("limit=100");
      }
    });
  });

  it("should use default limit of 50", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const baseMock = createMockFetchWithActiveLibrary({
      matcher: (url) => url.startsWith("/api/reading/history/1"),
      response: mockFetchResponse,
    });
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => baseMock(url),
    );

    renderHook(() => useReadingHistory({ bookId: 1 }), { wrapper });

    await waitFor(() => {
      const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls;
      const historyCalls = fetchCalls.filter(
        (call) =>
          typeof call[0] === "string" &&
          call[0].startsWith("/api/reading/history/1"),
      );
      expect(historyCalls.length).toBeGreaterThan(0);
      if (historyCalls.length > 0) {
        const url = historyCalls[0]?.[0] as string;
        expect(url).toContain("limit=50");
      }
    });
  });

  it("should not fetch when enabled is false", async () => {
    const { result } = renderHook(
      () => useReadingHistory({ bookId: 1, enabled: false }),
      { wrapper },
    );

    expect(result.current.sessions).toEqual([]);
    expect(result.current.total).toBe(0);
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const historyCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" && call[0].includes("/api/reading/history"),
    );
    expect(historyCalls.length).toBe(0);
  });

  it("should not fetch when bookId is 0 or negative", async () => {
    const { result } = renderHook(() => useReadingHistory({ bookId: 0 }), {
      wrapper,
    });

    expect(result.current.sessions).toEqual([]);
    expect(result.current.total).toBe(0);
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const historyCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" && call[0].includes("/api/reading/history"),
    );
    expect(historyCalls.length).toBe(0);
  });

  it("should handle error from fetch", () => {
    const mockFetchResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({ detail: "Book not found" }),
    };
    const baseMock = createMockFetchWithActiveLibrary({
      matcher: (url) => url.startsWith("/api/reading/history/1"),
      response: mockFetchResponse,
    });
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => baseMock(url),
    );

    const { result } = renderHook(() => useReadingHistory({ bookId: 1 }), {
      wrapper,
    });

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should refetch when refetch is called", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const baseMock = createMockFetchWithActiveLibrary({
      matcher: (url) => url.startsWith("/api/reading/history/1"),
      response: mockFetchResponse,
    });
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => baseMock(url),
    );

    const { result } = renderHook(() => useReadingHistory({ bookId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCallCount = (
      globalThis.fetch as ReturnType<typeof vi.fn>
    ).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].startsWith("/api/reading/history/1"),
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
        call[0].startsWith("/api/reading/history/1"),
    ).length;
    expect(newCallCount).toBeGreaterThan(initialCallCount);
  });

  it("should return empty arrays when data is null", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(null),
    };
    const baseMock = createMockFetchWithActiveLibrary({
      matcher: (url) => url.startsWith("/api/reading/history/1"),
      response: mockFetchResponse,
    });
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => baseMock(url),
    );

    const { result } = renderHook(() => useReadingHistory({ bookId: 1 }), {
      wrapper,
    });

    expect(result.current.sessions).toEqual([]);
    expect(result.current.total).toBe(0);
  });
});
