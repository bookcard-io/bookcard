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

import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Task } from "@/types/tasks";
import { TaskStatus, TaskType } from "@/types/tasks";
import { useTaskPolling } from "./useTaskPolling";

describe("useTaskPolling", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("should return pollTask function", () => {
    const { result } = renderHook(() => useTaskPolling());

    expect(result.current.pollTask).toBeDefined();
    expect(typeof result.current.pollTask).toBe("function");
  });

  it("should poll task until completed with book_ids", async () => {
    const onSuccess = vi.fn();
    const runningTask: Task = {
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

    const completedTask: Task = {
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
      metadata: { book_ids: [1, 2, 3] },
      duration: 1,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue(runningTask),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValue(completedTask),
      });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onSuccess,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toEqual([1, 2, 3]);
    expect(onSuccess).toHaveBeenCalledWith([1, 2, 3]);
  });

  it("should handle completed task with string book_ids", async () => {
    const onSuccess = vi.fn();
    const completedTask: Task = {
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
      metadata: { book_ids: ["1", "2", "3"] },
      duration: 1,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(completedTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onSuccess,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toEqual([1, 2, 3]);
    expect(onSuccess).toHaveBeenCalledWith([1, 2, 3]);
  });

  it("should handle completed task with mixed book_ids", async () => {
    const onSuccess = vi.fn();
    const completedTask: Task = {
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
      metadata: { book_ids: [1, "2", null, "invalid", 3] },
      duration: 1,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(completedTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onSuccess,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toEqual([1, 2, 3]);
  });

  it("should handle completed task without book_ids", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const completedTask: Task = {
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
      metadata: {},
      duration: 1,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(completedTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        maxCompletedRetries: 0,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalled();
    expect(onSetErrorMessage).toHaveBeenCalled();
  });

  it("should handle failed task", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const failedTask: Task = {
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
      error_message: "Upload failed",
      metadata: null,
      duration: 1,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(failedTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalledWith("Upload failed");
    expect(onSetErrorMessage).toHaveBeenCalledWith("Upload failed");
  });

  it("should handle failed task without error_message", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const failedTask: Task = {
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
      error_message: null,
      metadata: null,
      duration: 1,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(failedTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalledWith("Task failed");
    expect(onSetErrorMessage).toHaveBeenCalledWith("Task failed");
  });

  it("should handle cancelled task", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const cancelledTask: Task = {
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

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(cancelledTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalledWith("Task was cancelled");
    expect(onSetErrorMessage).toHaveBeenCalledWith("Task was cancelled");
  });

  it("should handle fetch error", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const mockResponse = {
      ok: false,
      status: 404,
      json: vi.fn().mockResolvedValue({ detail: "Task not found" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalledWith("Task not found");
    expect(onSetErrorMessage).toHaveBeenCalledWith("Task not found");
  });

  it("should handle fetch error without detail", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const mockResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValue({}),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalledWith("Failed to fetch task");
    expect(onSetErrorMessage).toHaveBeenCalledWith("Failed to fetch task");
  });

  it("should handle network error", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const error = new Error("Network error");
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalledWith("Network error");
    expect(onSetErrorMessage).toHaveBeenCalledWith("Network error");
  });

  it("should handle non-Error rejection", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(
      "String error",
    );

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalledWith("Failed to poll task");
    expect(onSetErrorMessage).toHaveBeenCalledWith("Failed to poll task");
  });

  it("should handle max attempts reached", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const runningTask: Task = {
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

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(runningTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 2,
        pollInterval: 10,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalledWith(
      "Upload timed out - task did not complete in time",
    );
    expect(onSetErrorMessage).toHaveBeenCalledWith(
      "Upload timed out - task did not complete in time",
    );
  });

  it("should handle extractBookIds with null metadata", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const completedTask: Task = {
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

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(completedTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        maxCompletedRetries: 0,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalled();
  });

  it("should handle extractBookIds with non-array book_ids", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const completedTask: Task = {
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
      metadata: { book_ids: "not an array" },
      duration: 1,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(completedTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        maxCompletedRetries: 0,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalled();
  });

  it("should handle extractBookIds with empty array", async () => {
    const onError = vi.fn();
    const onSetErrorMessage = vi.fn();
    const completedTask: Task = {
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
      metadata: { book_ids: [] },
      duration: 1,
    };

    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(completedTask),
    });

    const { result } = renderHook(() =>
      useTaskPolling({
        maxAttempts: 10,
        pollInterval: 100,
        maxCompletedRetries: 0,
        onError,
        onSetErrorMessage,
      }),
    );

    const bookIds = await result.current.pollTask(123);

    expect(bookIds).toBeNull();
    expect(onError).toHaveBeenCalled();
  });
});
