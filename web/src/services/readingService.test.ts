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

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  endSession,
  getProgress,
  getReadingHistory,
  getReadStatus,
  getRecentReads,
  listSessions,
  startSession,
  updateProgress,
  updateReadStatus,
} from "./readingService";

/**
 * Create a mock fetch response.
 */
function createMockResponse(
  ok: boolean,
  jsonData: unknown = {},
  jsonError: Error | null = null,
) {
  return {
    ok,
    json: jsonError
      ? vi.fn().mockRejectedValue(jsonError)
      : vi.fn().mockResolvedValue(jsonData),
  };
}

describe("readingService", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("updateProgress", () => {
    it("should update progress successfully", async () => {
      const mockProgress = {
        book_id: 1,
        format: "EPUB",
        progress: 0.5,
        updated_at: "2025-01-01T00:00:00Z",
      };
      const mockResponse = createMockResponse(true, mockProgress);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const data = {
        book_id: 1,
        format: "EPUB",
        progress: 0.5,
      };

      const result = await updateProgress(data);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/reading/progress", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(data),
      });
      expect(result).toEqual(mockProgress);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Invalid progress value" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const data = {
        book_id: 1,
        format: "EPUB",
        progress: 0.5,
      };

      await expect(updateProgress(data)).rejects.toThrow(
        "Invalid progress value",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const data = {
        book_id: 1,
        format: "EPUB",
        progress: 0.5,
      };

      await expect(updateProgress(data)).rejects.toThrow(
        "Failed to update reading progress",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const data = {
        book_id: 1,
        format: "EPUB",
        progress: 0.5,
      };

      await expect(updateProgress(data)).rejects.toThrow(
        "Failed to update reading progress",
      );
    });
  });

  describe("getProgress", () => {
    it("should get progress successfully", async () => {
      const mockProgress = {
        book_id: 1,
        format: "EPUB",
        progress: 0.5,
        updated_at: "2025-01-01T00:00:00Z",
      };
      const mockResponse = createMockResponse(true, mockProgress);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getProgress(1, "EPUB");

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/reading/progress?book_id=1&format=EPUB",
        {
          method: "GET",
          credentials: "include",
        },
      );
      expect(result).toEqual(mockProgress);
    });

    it("should return null for 404 response", async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        json: vi.fn(),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getProgress(1, "EPUB");

      expect(result).toBeNull();
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to get progress" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getProgress(1, "EPUB")).rejects.toThrow(
        "Failed to get progress",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getProgress(1, "EPUB")).rejects.toThrow(
        "Failed to get reading progress",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getProgress(1, "EPUB")).rejects.toThrow(
        "Failed to get reading progress",
      );
    });
  });

  describe("startSession", () => {
    it("should start session successfully", async () => {
      const mockSession = {
        id: 1,
        book_id: 1,
        format: "EPUB",
        progress_start: 0.0,
        started_at: "2025-01-01T00:00:00Z",
      };
      const mockResponse = createMockResponse(true, mockSession);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const data = {
        book_id: 1,
        format: "EPUB",
        progress_start: 0.0,
      };

      const result = await startSession(data);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/reading/sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(data),
      });
      expect(result).toEqual(mockSession);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to start session" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const data = {
        book_id: 1,
        format: "EPUB",
        progress_start: 0.0,
      };

      await expect(startSession(data)).rejects.toThrow(
        "Failed to start session",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const data = {
        book_id: 1,
        format: "EPUB",
        progress_start: 0.0,
      };

      await expect(startSession(data)).rejects.toThrow(
        "Failed to start reading session",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const data = {
        book_id: 1,
        format: "EPUB",
        progress_start: 0.0,
      };

      await expect(startSession(data)).rejects.toThrow(
        "Failed to start reading session",
      );
    });
  });

  describe("endSession", () => {
    it("should end session successfully", async () => {
      const mockSession = {
        id: 1,
        book_id: 1,
        format: "EPUB",
        progress_start: 0.0,
        progress_end: 0.5,
        started_at: "2025-01-01T00:00:00Z",
        ended_at: "2025-01-01T01:00:00Z",
      };
      const mockResponse = createMockResponse(true, mockSession);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await endSession(1, 0.5);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/reading/sessions/1", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ progress_end: 0.5 }),
      });
      expect(result).toEqual(mockSession);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Session not found" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(endSession(1, 0.5)).rejects.toThrow("Session not found");
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(endSession(1, 0.5)).rejects.toThrow(
        "Failed to end reading session",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(endSession(1, 0.5)).rejects.toThrow(
        "Failed to end reading session",
      );
    });
  });

  describe("listSessions", () => {
    it("should list sessions successfully with default pagination", async () => {
      const mockResponseData = {
        items: [
          {
            id: 1,
            book_id: 1,
            format: "EPUB",
            progress_start: 0.0,
            progress_end: 0.5,
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await listSessions();

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/reading/sessions?page=1&page_size=50",
        {
          method: "GET",
          credentials: "include",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should list sessions with custom pagination", async () => {
      const mockResponseData = {
        items: [],
        total: 0,
        page: 2,
        page_size: 20,
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await listSessions(undefined, 2, 20);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/reading/sessions?page=2&page_size=20",
        {
          method: "GET",
          credentials: "include",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should list sessions filtered by bookId", async () => {
      const mockResponseData = {
        items: [
          {
            id: 1,
            book_id: 1,
            format: "EPUB",
            progress_start: 0.0,
            progress_end: 0.5,
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await listSessions(1);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/reading/sessions?page=1&page_size=50&book_id=1",
        {
          method: "GET",
          credentials: "include",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to list sessions" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(listSessions()).rejects.toThrow("Failed to list sessions");
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(listSessions()).rejects.toThrow(
        "Failed to list reading sessions",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(listSessions()).rejects.toThrow(
        "Failed to list reading sessions",
      );
    });
  });

  describe("getRecentReads", () => {
    it("should get recent reads with default limit", async () => {
      const mockResponseData = {
        items: [
          {
            book_id: 1,
            format: "EPUB",
            last_read_at: "2025-01-01T00:00:00Z",
          },
        ],
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getRecentReads();

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/reading/recent?limit=10",
        {
          method: "GET",
          credentials: "include",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should get recent reads with custom limit", async () => {
      const mockResponseData = {
        items: [],
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getRecentReads(20);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/reading/recent?limit=20",
        {
          method: "GET",
          credentials: "include",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to get recent reads" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getRecentReads()).rejects.toThrow(
        "Failed to get recent reads",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getRecentReads()).rejects.toThrow(
        "Failed to get recent reads",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getRecentReads()).rejects.toThrow(
        "Failed to get recent reads",
      );
    });
  });

  describe("getReadingHistory", () => {
    it("should get reading history with default limit", async () => {
      const mockResponseData = {
        book_id: 1,
        sessions: [
          {
            id: 1,
            progress_start: 0.0,
            progress_end: 0.5,
            started_at: "2025-01-01T00:00:00Z",
            ended_at: "2025-01-01T01:00:00Z",
          },
        ],
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getReadingHistory(1);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/reading/history/1?limit=50",
        {
          method: "GET",
          credentials: "include",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should get reading history with custom limit", async () => {
      const mockResponseData = {
        book_id: 1,
        sessions: [],
      };
      const mockResponse = createMockResponse(true, mockResponseData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getReadingHistory(1, 100);

      expect(globalThis.fetch).toHaveBeenCalledWith(
        "/api/reading/history/1?limit=100",
        {
          method: "GET",
          credentials: "include",
        },
      );
      expect(result).toEqual(mockResponseData);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to get reading history" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getReadingHistory(1)).rejects.toThrow(
        "Failed to get reading history",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getReadingHistory(1)).rejects.toThrow(
        "Failed to get reading history",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getReadingHistory(1)).rejects.toThrow(
        "Failed to get reading history",
      );
    });
  });

  describe("getReadStatus", () => {
    it("should get read status successfully", async () => {
      const mockStatus = {
        book_id: 1,
        status: "read" as const,
        updated_at: "2025-01-01T00:00:00Z",
      };
      const mockResponse = createMockResponse(true, mockStatus);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await getReadStatus(1);

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/reading/status/1", {
        method: "GET",
        credentials: "include",
      });
      expect(result).toEqual(mockStatus);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to get read status" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getReadStatus(1)).rejects.toThrow(
        "Failed to get read status",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getReadStatus(1)).rejects.toThrow(
        "Failed to get read status",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(getReadStatus(1)).rejects.toThrow(
        "Failed to get read status",
      );
    });
  });

  describe("updateReadStatus", () => {
    it("should update read status to read", async () => {
      const mockStatus = {
        book_id: 1,
        status: "read" as const,
        updated_at: "2025-01-01T00:00:00Z",
      };
      const mockResponse = createMockResponse(true, mockStatus);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateReadStatus(1, "read");

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/reading/status/1", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ status: "read" }),
      });
      expect(result).toEqual(mockStatus);
    });

    it("should update read status to not_read", async () => {
      const mockStatus = {
        book_id: 1,
        status: "not_read" as const,
        updated_at: "2025-01-01T00:00:00Z",
      };
      const mockResponse = createMockResponse(true, mockStatus);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      const result = await updateReadStatus(1, "not_read");

      expect(globalThis.fetch).toHaveBeenCalledWith("/api/reading/status/1", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ status: "not_read" }),
      });
      expect(result).toEqual(mockStatus);
    });

    it("should handle error response with detail", async () => {
      const errorData = { detail: "Failed to update read status" };
      const mockResponse = createMockResponse(false, errorData);
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateReadStatus(1, "read")).rejects.toThrow(
        "Failed to update read status",
      );
    });

    it("should handle error response without detail", async () => {
      const mockResponse = createMockResponse(false, {});
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateReadStatus(1, "read")).rejects.toThrow(
        "Failed to update read status",
      );
    });

    it("should handle JSON parse error", async () => {
      const mockResponse = {
        ok: false,
        json: vi.fn().mockRejectedValue(new Error("Invalid JSON")),
      };
      (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
        mockResponse,
      );

      await expect(updateReadStatus(1, "read")).rejects.toThrow(
        "Failed to update read status",
      );
    });
  });
});
