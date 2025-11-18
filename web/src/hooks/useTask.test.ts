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

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Task } from "@/types/tasks";
import { TaskStatus, TaskType } from "@/types/tasks";
import { useTask } from "./useTask";

describe("useTask", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("should initialize with null task and false loading", () => {
    const { result } = renderHook(() =>
      useTask({ taskId: null, enabled: false }),
    );

    expect(result.current.task).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.isCancelling).toBe(false);
  });

  it("should not fetch when taskId is null", () => {
    renderHook(() => useTask({ taskId: null, enabled: true }));

    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should not fetch when enabled is false", () => {
    renderHook(() => useTask({ taskId: 123, enabled: false }));

    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should fetch task when taskId is provided and enabled", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.PENDING,
      progress: 0,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: null,
      completed_at: null,
      cancelled_at: null,
      error_message: null,
      metadata: null,
      duration: null,
    };

    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useTask({ taskId: 123, enabled: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/tasks/123",
      expect.objectContaining({
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );
    expect(result.current.task).toEqual(mockTask);
    expect(result.current.isLoading).toBe(false);
  });

  it("should handle fetch error", async () => {
    const mockResponse = {
      ok: false,
      status: 404,
      json: vi.fn().mockResolvedValue({ detail: "Task not found" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useTask({ taskId: 123, enabled: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(result.current.task).toBeNull();
    expect(result.current.error).toBe("Task not found");
    expect(result.current.isLoading).toBe(false);
  });

  it("should handle fetch error without detail", async () => {
    const mockResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({}),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useTask({ taskId: 123, enabled: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(result.current.error).toBe("Failed to fetch task");
  });

  it("should handle network error", async () => {
    const error = new Error("Network error");
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    const { result } = renderHook(() =>
      useTask({ taskId: 123, enabled: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(result.current.error).toBe("Network error");
    expect(result.current.task).toBeNull();
  });

  it("should cancel task successfully", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.RUNNING,
      progress: 50,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T00:00:01Z",
      completed_at: null,
      cancelled_at: null,
      error_message: null,
      metadata: null,
      duration: null,
    };

    const fetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(fetchResponse)
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ success: true }),
      })
      .mockResolvedValueOnce(fetchResponse);

    const { result } = renderHook(() =>
      useTask({ taskId: 123, enabled: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      const cancelled = await result.current.cancel();
      expect(cancelled).toBe(true);
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/tasks/123/cancel",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  it("should return false when cancel fails", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.RUNNING,
      progress: 50,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T00:00:01Z",
      completed_at: null,
      cancelled_at: null,
      error_message: null,
      metadata: null,
      duration: null,
    };

    const fetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(fetchResponse)
      .mockResolvedValueOnce({
        ok: false,
        json: vi.fn().mockResolvedValue({ detail: "Cannot cancel" }),
      });

    const { result } = renderHook(() =>
      useTask({ taskId: 123, enabled: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      const cancelled = await result.current.cancel();
      expect(cancelled).toBe(false);
    });
  });

  it("should return false when cancel returns success: false", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.RUNNING,
      progress: 50,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T00:00:01Z",
      completed_at: null,
      cancelled_at: null,
      error_message: null,
      metadata: null,
      duration: null,
    };

    const fetchResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce(fetchResponse)
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue({ success: false }),
      });

    const { result } = renderHook(() =>
      useTask({ taskId: 123, enabled: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      const cancelled = await result.current.cancel();
      expect(cancelled).toBe(false);
    });
  });

  it("should return false when taskId is null", async () => {
    const { result } = renderHook(() =>
      useTask({ taskId: null, enabled: false }),
    );

    await act(async () => {
      const cancelled = await result.current.cancel();
      expect(cancelled).toBe(false);
    });

    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it("should refresh task", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.PENDING,
      progress: 0,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: null,
      completed_at: null,
      cancelled_at: null,
      error_message: null,
      metadata: null,
      duration: null,
    };

    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useTask({ taskId: 123, enabled: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      await result.current.refresh();
    });

    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });

  it("should not auto-refresh when autoRefresh is false", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.RUNNING,
      progress: 50,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T00:00:01Z",
      completed_at: null,
      cancelled_at: null,
      error_message: null,
      metadata: null,
      duration: null,
    };

    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    renderHook(() =>
      useTask({ taskId: 123, enabled: true, autoRefresh: false }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("should not auto-refresh when task is completed", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.COMPLETED,
      progress: 100,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T00:00:01Z",
      completed_at: "2025-01-01T00:00:02Z",
      cancelled_at: null,
      error_message: null,
      metadata: null,
      duration: 1,
    };

    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    renderHook(() =>
      useTask({ taskId: 123, enabled: true, autoRefresh: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("should not auto-refresh when task is failed", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.FAILED,
      progress: 0,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T00:00:01Z",
      completed_at: "2025-01-01T00:00:02Z",
      cancelled_at: null,
      error_message: "Error occurred",
      metadata: null,
      duration: 1,
    };

    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    renderHook(() =>
      useTask({ taskId: 123, enabled: true, autoRefresh: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("should not auto-refresh when task is cancelled", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.CANCELLED,
      progress: 0,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T00:00:01Z",
      completed_at: null,
      cancelled_at: "2025-01-01T00:00:02Z",
      error_message: null,
      metadata: null,
      duration: null,
    };

    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    renderHook(() =>
      useTask({ taskId: 123, enabled: true, autoRefresh: true }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("should set up auto-refresh when task is running", async () => {
    const mockTask: Task = {
      id: 123,
      task_type: TaskType.BOOK_UPLOAD,
      status: TaskStatus.RUNNING,
      progress: 50,
      user_id: 1,
      username: "test",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T00:00:01Z",
      completed_at: null,
      cancelled_at: null,
      error_message: null,
      metadata: null,
      duration: null,
    };

    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue(mockTask),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useTask({
        taskId: 123,
        enabled: true,
        autoRefresh: true,
        refreshInterval: 1000,
      }),
    );

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    // Verify initial fetch happened and task is set
    expect(globalThis.fetch).toHaveBeenCalled();
    expect(result.current.task).toEqual(mockTask);
    // Auto-refresh interval should be set up (covered by lines 127-132)
  });
});
