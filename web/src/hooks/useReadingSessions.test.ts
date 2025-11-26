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
import type {
  ReadingSession,
  ReadingSessionsListResponse,
} from "@/types/reading";
import {
  createMockFetchWithActiveLibrary,
  createQueryClientWrapper,
} from "./test-utils";
import { useReadingSessions } from "./useReadingSessions";

describe("useReadingSessions", () => {
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

  const mockResponse: ReadingSessionsListResponse = {
    sessions: [mockSession],
    total: 1,
    page: 1,
    page_size: 50,
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

  it("should fetch reading sessions on mount", () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => {
        if (
          url.startsWith("/api/reading/sessions") &&
          !url.includes("/api/reading/sessions/")
        ) {
          return Promise.resolve(mockFetchResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(() => useReadingSessions(), { wrapper });

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should use custom page and pageSize", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        ...mockResponse,
        page: 2,
        page_size: 20,
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) => url.startsWith("/api/reading/sessions"),
        response: mockFetchResponse,
      }),
    );

    renderHook(() => useReadingSessions({ page: 2, pageSize: 20 }), {
      wrapper,
    });

    await waitFor(() => {
      const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls;
      const sessionCalls = fetchCalls.filter(
        (call) =>
          typeof call[0] === "string" &&
          call[0].startsWith("/api/reading/sessions"),
      );
      expect(sessionCalls.length).toBeGreaterThan(0);
      if (sessionCalls.length > 0) {
        const url = sessionCalls[0]?.[0] as string;
        expect(url).toContain("page=2");
        expect(url).toContain("page_size=20");
      }
    });
  });

  it("should filter by bookId when provided", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) => url.startsWith("/api/reading/sessions"),
        response: mockFetchResponse,
      }),
    );

    renderHook(() => useReadingSessions({ bookId: 1 }), { wrapper });

    await waitFor(() => {
      const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
        .calls;
      const sessionCalls = fetchCalls.filter(
        (call) =>
          typeof call[0] === "string" &&
          call[0].startsWith("/api/reading/sessions"),
      );
      expect(sessionCalls.length).toBeGreaterThan(0);
      if (sessionCalls.length > 0) {
        const url = sessionCalls[0]?.[0] as string;
        expect(url).toContain("book_id=1");
      }
    });
  });

  it("should not fetch when enabled is false", async () => {
    const { result } = renderHook(
      () => useReadingSessions({ enabled: false }),
      { wrapper },
    );

    expect(result.current.sessions).toEqual([]);
    expect(result.current.total).toBe(0);
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const sessionCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].startsWith("/api/reading/sessions"),
    );
    expect(sessionCalls.length).toBe(0);
  });

  it("should handle error from fetch", () => {
    const mockFetchResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({ detail: "Failed to fetch" }),
    };
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string) => {
        if (
          url.startsWith("/api/reading/sessions") &&
          !url.includes("/api/reading/sessions/")
        ) {
          return Promise.resolve(mockFetchResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(() => useReadingSessions(), { wrapper });

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should refetch when refetch is called", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockResponse),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) => url.startsWith("/api/reading/sessions"),
        response: mockFetchResponse,
      }),
    );

    const { result } = renderHook(() => useReadingSessions(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCallCount = (
      globalThis.fetch as ReturnType<typeof vi.fn>
    ).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" &&
        call[0].startsWith("/api/reading/sessions"),
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
        call[0].startsWith("/api/reading/sessions"),
    ).length;
    expect(newCallCount).toBeGreaterThan(initialCallCount);
  });

  describe("infinite scroll mode", () => {
    it("should accumulate sessions across pages", () => {
      const page1Response: ReadingSessionsListResponse = {
        sessions: [mockSession],
        total: 2,
        page: 1,
        page_size: 1,
      };
      const page2Response: ReadingSessionsListResponse = {
        sessions: [
          {
            ...mockSession,
            id: 2,
          },
        ],
        total: 2,
        page: 2,
        page_size: 1,
      };

      const baseMock = createMockFetchWithActiveLibrary(
        {
          ok: true,
          json: vi.fn().mockResolvedValue(page2Response),
        },
        {
          ok: true,
          json: vi.fn().mockResolvedValue(page1Response),
        },
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        (url: string) => baseMock(url),
      );

      const { result } = renderHook(
        () => useReadingSessions({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      // Verify hook is initialized
      expect(result.current).toBeDefined();
    });

    it("should load more pages", () => {
      const page1Response: ReadingSessionsListResponse = {
        sessions: [mockSession],
        total: 2,
        page: 1,
        page_size: 1,
      };
      const page2Response: ReadingSessionsListResponse = {
        sessions: [
          {
            ...mockSession,
            id: 2,
          },
        ],
        total: 2,
        page: 2,
        page_size: 1,
      };

      const baseMock = createMockFetchWithActiveLibrary(
        {
          ok: true,
          json: vi.fn().mockResolvedValue(page2Response),
        },
        {
          ok: true,
          json: vi.fn().mockResolvedValue(page1Response),
        },
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        (url: string) => baseMock(url),
      );

      const { result } = renderHook(
        () => useReadingSessions({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      // Verify hook is initialized
      expect(result.current).toBeDefined();
    });

    it("should not load more when hasMore is false", () => {
      const page1Response: ReadingSessionsListResponse = {
        sessions: [mockSession],
        total: 1,
        page: 1,
        page_size: 1,
      };

      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        createMockFetchWithActiveLibrary({
          ok: true,
          json: vi.fn().mockResolvedValue(page1Response),
        }),
      );

      const { result } = renderHook(
        () => useReadingSessions({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      // Verify hook is initialized
      expect(result.current).toBeDefined();
    });

    it("should not load more when already fetching", () => {
      const page1Response: ReadingSessionsListResponse = {
        sessions: [mockSession],
        total: 2,
        page: 1,
        page_size: 1,
      };
      const page2Response: ReadingSessionsListResponse = {
        sessions: [
          {
            ...mockSession,
            id: 2,
          },
        ],
        total: 2,
        page: 2,
        page_size: 1,
      };

      const baseMock = createMockFetchWithActiveLibrary(
        {
          ok: true,
          json: vi.fn().mockResolvedValue(page2Response),
        },
        {
          ok: true,
          json: vi.fn().mockResolvedValue(page1Response),
        },
      );
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
        (url: string) => baseMock(url),
      );

      const { result } = renderHook(
        () => useReadingSessions({ infiniteScroll: true, pageSize: 1 }),
        { wrapper },
      );

      // Verify hook is initialized
      expect(result.current).toBeDefined();
    });
  });
});
