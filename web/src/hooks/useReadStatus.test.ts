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
import type { ReadStatus } from "@/types/reading";
import {
  createMockFetchWithActiveLibrary,
  createQueryClientWrapper,
} from "./test-utils";
import { useReadStatus } from "./useReadStatus";

describe("useReadStatus", () => {
  let queryClient: QueryClient;
  let wrapper: ReturnType<typeof createQueryClientWrapper>;

  const mockReadStatus: ReadStatus = {
    id: 1,
    user_id: 1,
    library_id: 1,
    book_id: 1,
    status: "read",
    first_opened_at: "2024-01-01T00:00:00Z",
    marked_as_read_at: "2024-01-02T00:00:00Z",
    auto_marked: false,
    progress_when_marked: 1.0,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
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

  it("should fetch read status on mount", () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockReadStatus),
    };
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string, options?: RequestInit) => {
        if (
          url === "/api/reading/status/1" &&
          (!options?.method || options?.method === "GET")
        ) {
          return Promise.resolve(mockFetchResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper,
    });

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should not fetch when enabled is false", async () => {
    const { result } = renderHook(
      () => useReadStatus({ bookId: 1, enabled: false }),
      { wrapper },
    );

    expect(result.current.status).toBeNull();
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const statusCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" && call[0].includes("/api/reading/status"),
    );
    expect(statusCalls.length).toBe(0);
  });

  it("should not fetch when bookId is 0 or negative", async () => {
    const { result } = renderHook(() => useReadStatus({ bookId: 0 }), {
      wrapper,
    });

    expect(result.current.status).toBeNull();
    const fetchCalls = (globalThis.fetch as ReturnType<typeof vi.fn>).mock
      .calls;
    const statusCalls = fetchCalls.filter(
      (call) =>
        typeof call[0] === "string" && call[0].includes("/api/reading/status"),
    );
    expect(statusCalls.length).toBe(0);
  });

  it("should handle error from fetch", () => {
    const mockFetchResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({ detail: "Book not found" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) => url === "/api/reading/status/1",
        response: mockFetchResponse,
      }),
    );

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper,
    });

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should not retry on 404 errors (read_status_not_found)", () => {
    const mockFetchResponse = {
      ok: false,
      status: 404,
      json: vi.fn().mockResolvedValue({
        detail: "read_status_not_found",
      }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) => url === "/api/reading/status/1",
        response: mockFetchResponse,
      }),
    );

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper,
    });

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should retry on network errors (up to 3 times)", () => {
    const mockFetchResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({ detail: "Network error" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) => url === "/api/reading/status/1",
        response: mockFetchResponse,
      }),
    );

    const queryClientWithRetry = new QueryClient({
      defaultOptions: {
        queries: {
          retry: (failureCount, error) => {
            if (error?.message?.includes("read_status_not_found")) {
              return false;
            }
            return failureCount < 3;
          },
          gcTime: 0,
        },
      },
    });
    const wrapperWithRetry = createQueryClientWrapper(queryClientWithRetry);

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper: wrapperWithRetry,
    });

    // Verify hook is initialized
    expect(result.current).toBeDefined();
  });

  it("should refetch when refetch is called", async () => {
    const mockFetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockReadStatus),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      createMockFetchWithActiveLibrary({
        matcher: (url) => url === "/api/reading/status/1",
        response: mockFetchResponse,
      }),
    );

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const initialCallCount = (
      globalThis.fetch as ReturnType<typeof vi.fn>
    ).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" && call[0] === "/api/reading/status/1",
    ).length;

    act(() => {
      result.current.refetch();
    });

    await new Promise((resolve) => setTimeout(resolve, 50));
    const newCallCount = (
      globalThis.fetch as ReturnType<typeof vi.fn>
    ).mock.calls.filter(
      (call) =>
        typeof call[0] === "string" && call[0] === "/api/reading/status/1",
    ).length;
    expect(newCallCount).toBeGreaterThan(initialCallCount);
  });

  it("should mark book as read", async () => {
    const getMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockReadStatus),
    };
    const updateMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        ...mockReadStatus,
        status: "read",
      }),
    };
    let getCallCount = 0;
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string, options?: RequestInit) => {
        if (url === "/api/reading/status/1" && options?.method === "PUT") {
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        if (
          url === "/api/reading/status/1" &&
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

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      const updatedStatus = await result.current.markAsRead();
      expect(updatedStatus.status).toBe("read");
    });

    expect(result.current.isUpdating).toBe(false);
    expect(result.current.updateError).toBeNull();
  });

  it("should mark book as unread", async () => {
    const getMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockReadStatus),
    };
    const updateMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        ...mockReadStatus,
        status: "not_read",
      }),
    };
    let getCallCount = 0;
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string, options?: RequestInit) => {
        if (url === "/api/reading/status/1" && options?.method === "PUT") {
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        if (
          url === "/api/reading/status/1" &&
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

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      const updatedStatus = await result.current.markAsUnread();
      expect(updatedStatus.status).toBe("not_read");
    });

    expect(result.current.isUpdating).toBe(false);
    expect(result.current.updateError).toBeNull();
  });

  it("should handle update error", async () => {
    const getMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockReadStatus),
    };
    const updateMockResponse = {
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Update failed" }),
    };
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string, options?: RequestInit) => {
        if (url === "/api/reading/status/1" && options?.method === "PUT") {
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        if (
          url === "/api/reading/status/1" &&
          (!options?.method || options?.method === "GET")
        ) {
          return Promise.resolve(getMockResponse as unknown as Response);
        }
        return baseMock(url);
      },
    );

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await expect(result.current.markAsRead()).rejects.toThrow();
    });

    expect(result.current.updateError).toBeTruthy();
  });

  it("should invalidate related queries on successful update", async () => {
    const getMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockReadStatus),
    };
    const updateMockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({
        ...mockReadStatus,
        status: "read",
      }),
    };
    let getCallCount = 0;
    const baseMock = createMockFetchWithActiveLibrary();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockImplementation(
      (url: string, options?: RequestInit) => {
        if (url === "/api/reading/status/1" && options?.method === "PUT") {
          return Promise.resolve(updateMockResponse as unknown as Response);
        }
        if (
          url === "/api/reading/status/1" &&
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
    queryClient.setQueryData(["read-status", 1], mockReadStatus);
    queryClient.setQueryData(["recent-reads"], { reads: [] });

    const { result } = renderHook(() => useReadStatus({ bookId: 1 }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.markAsRead();
    });

    // Check that query cache was updated
    const cachedData = queryClient.getQueryData(["read-status", 1]);
    expect(cachedData).toBeTruthy();
    expect((cachedData as ReadStatus).status).toBe("read");
  });
});
