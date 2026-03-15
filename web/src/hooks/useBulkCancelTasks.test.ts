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
import { describe, expect, it, vi } from "vitest";
import { TaskStatus, TaskType } from "@/types/tasks";
import { useBulkCancelTasks } from "./useBulkCancelTasks";

describe("useBulkCancelTasks", () => {
  // --- cancelAll ---

  it("cancels all tasks when selectedStatus is null", async () => {
    const bulkCancelTasks = vi
      .fn()
      .mockResolvedValue({ cancelled: 5, message: "Cancelled 5 task(s)" });
    const refresh = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: null,
        selectedTaskType: null,
        bulkCancelTasks,
        refresh,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(bulkCancelTasks).toHaveBeenCalledWith(null, null);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(result.current.error).toBeNull();
    expect(result.current.notice).toContain("Cancelled 5");
  });

  it("passes selectedStatus through to bulk cancel endpoint", async () => {
    const bulkCancelTasks = vi
      .fn()
      .mockResolvedValue({ cancelled: 2, message: "Cancelled 2 task(s)" });

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.RUNNING,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(bulkCancelTasks).toHaveBeenCalledWith(TaskStatus.RUNNING, null);
  });

  it("passes selectedTaskType through to bulk cancel endpoint", async () => {
    const bulkCancelTasks = vi
      .fn()
      .mockResolvedValue({ cancelled: 3, message: "Cancelled 3 task(s)" });

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: TaskType.LIBRARY_SCAN,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(bulkCancelTasks).toHaveBeenCalledWith(
      TaskStatus.PENDING,
      TaskType.LIBRARY_SCAN,
    );
  });

  it("is a no-op with notice when selectedStatus is COMPLETED", async () => {
    const bulkCancelTasks = vi.fn();
    const refresh = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.COMPLETED,
        selectedTaskType: null,
        bulkCancelTasks,
        refresh,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(bulkCancelTasks).not.toHaveBeenCalled();
    expect(refresh).not.toHaveBeenCalled();
    expect(result.current.notice).toContain("Only pending/running");
  });

  it("is a no-op with notice when selectedStatus is FAILED", async () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.FAILED,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(bulkCancelTasks).not.toHaveBeenCalled();
    expect(result.current.notice).toContain("Only pending/running");
  });

  it("is a no-op with notice when selectedStatus is CANCELLED", async () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.CANCELLED,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(bulkCancelTasks).not.toHaveBeenCalled();
    expect(result.current.notice).toContain("Only pending/running");
  });

  it("shows notice when server reports zero tasks cancelled", async () => {
    const bulkCancelTasks = vi.fn().mockResolvedValue({
      cancelled: 0,
      message: "No cancellable tasks found",
    });

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(result.current.notice).toBe("No tasks to cancel.");
  });

  it("ignores subsequent cancelAll calls while already cancelling", async () => {
    let resolveCancel:
      | ((value: { cancelled: number; message: string }) => void)
      | null = null;
    const bulkCancelTasks = vi.fn().mockImplementation(
      () =>
        new Promise<{ cancelled: number; message: string }>((resolve) => {
          resolveCancel = resolve;
        }),
    );

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    let firstPromise: Promise<void> | undefined;

    await act(async () => {
      firstPromise = result.current.cancelAll();
    });

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(bulkCancelTasks).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveCancel?.({ cancelled: 1, message: "Cancelled 1 task(s)" });
      await firstPromise;
    });
  });

  it("sets error when bulk cancel fails with Error", async () => {
    const bulkCancelTasks = vi.fn().mockRejectedValue(new Error("Boom"));

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(result.current.error).toBe("Boom");
    expect(result.current.isCancelling).toBe(false);
  });

  it("sets fallback error when non-Error is thrown", async () => {
    const bulkCancelTasks = vi.fn().mockRejectedValue("string error");

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(result.current.error).toBe("Failed to cancel tasks");
  });

  it("clears previous error and notice on new cancelAll attempt", async () => {
    const bulkCancelTasks = vi
      .fn()
      .mockRejectedValueOnce(new Error("First failure"))
      .mockResolvedValueOnce({ cancelled: 1, message: "Cancelled 1 task(s)" });
    const refresh = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        bulkCancelTasks,
        refresh,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });
    expect(result.current.error).toBe("First failure");

    await act(async () => {
      await result.current.cancelAll();
    });
    expect(result.current.error).toBeNull();
    expect(result.current.notice).toContain("Cancelled 1");
  });

  it("does not call refresh when refresh is not provided", async () => {
    const bulkCancelTasks = vi
      .fn()
      .mockResolvedValue({ cancelled: 1, message: "Cancelled 1 task(s)" });

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: null,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(result.current.notice).toContain("Cancelled 1");
  });

  it("sets isCancelling to true during operation and false after", async () => {
    let resolveCancel:
      | ((value: { cancelled: number; message: string }) => void)
      | null = null;
    const bulkCancelTasks = vi.fn().mockImplementation(
      () =>
        new Promise<{ cancelled: number; message: string }>((resolve) => {
          resolveCancel = resolve;
        }),
    );

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    expect(result.current.isCancelling).toBe(false);

    let promise: Promise<void> | undefined;
    await act(async () => {
      promise = result.current.cancelAll();
    });

    expect(result.current.isCancelling).toBe(true);

    await act(async () => {
      resolveCancel?.({ cancelled: 1, message: "Cancelled 1 task(s)" });
      await promise;
    });

    expect(result.current.isCancelling).toBe(false);
  });

  // --- getTaskCount ---

  it("getTaskCount sums pending and running when no status filter", async () => {
    const countTasks = vi
      .fn()
      .mockResolvedValueOnce(10)
      .mockResolvedValueOnce(3);

    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: null,
        selectedTaskType: null,
        countTasks,
        bulkCancelTasks,
      }),
    );

    let count = 0;
    await act(async () => {
      count = await result.current.getTaskCount();
    });

    expect(count).toBe(13);
    expect(countTasks).toHaveBeenCalledWith(TaskStatus.PENDING, null);
    expect(countTasks).toHaveBeenCalledWith(TaskStatus.RUNNING, null);
  });

  it("getTaskCount uses single status when selectedStatus is cancellable", async () => {
    const countTasks = vi.fn().mockResolvedValue(7);
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.RUNNING,
        selectedTaskType: null,
        countTasks,
        bulkCancelTasks,
      }),
    );

    let count = 0;
    await act(async () => {
      count = await result.current.getTaskCount();
    });

    expect(count).toBe(7);
    expect(countTasks).toHaveBeenCalledTimes(1);
    expect(countTasks).toHaveBeenCalledWith(TaskStatus.RUNNING, null);
  });

  it("getTaskCount passes selectedTaskType to countTasks", async () => {
    const countTasks = vi.fn().mockResolvedValue(4);
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: TaskType.BOOK_UPLOAD,
        countTasks,
        bulkCancelTasks,
      }),
    );

    await act(async () => {
      await result.current.getTaskCount();
    });

    expect(countTasks).toHaveBeenCalledWith(
      TaskStatus.PENDING,
      TaskType.BOOK_UPLOAD,
    );
  });

  it("getTaskCount returns 0 for non-cancellable status", async () => {
    const countTasks = vi.fn();
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.COMPLETED,
        selectedTaskType: null,
        countTasks,
        bulkCancelTasks,
      }),
    );

    let count = 0;
    await act(async () => {
      count = await result.current.getTaskCount();
    });

    expect(count).toBe(0);
    expect(countTasks).not.toHaveBeenCalled();
  });

  it("getTaskCount returns 0 for FAILED status", async () => {
    const countTasks = vi.fn();
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.FAILED,
        selectedTaskType: null,
        countTasks,
        bulkCancelTasks,
      }),
    );

    let count = 0;
    await act(async () => {
      count = await result.current.getTaskCount();
    });

    expect(count).toBe(0);
    expect(countTasks).not.toHaveBeenCalled();
  });

  it("getTaskCount returns 0 when countTasks throws", async () => {
    const countTasks = vi.fn().mockRejectedValue(new Error("Network error"));
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: null,
        selectedTaskType: null,
        countTasks,
        bulkCancelTasks,
      }),
    );

    let count = 999;
    await act(async () => {
      count = await result.current.getTaskCount();
    });

    expect(count).toBe(0);
  });

  // --- isCancellableSelection ---

  it("isCancellableSelection is true when no status filter", () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: null,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    expect(result.current.isCancellableSelection).toBe(true);
  });

  it("isCancellableSelection is true for PENDING status", () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    expect(result.current.isCancellableSelection).toBe(true);
  });

  it("isCancellableSelection is true for RUNNING status", () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.RUNNING,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    expect(result.current.isCancellableSelection).toBe(true);
  });

  it("isCancellableSelection is false for COMPLETED status", () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.COMPLETED,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    expect(result.current.isCancellableSelection).toBe(false);
  });

  it("isCancellableSelection is false for FAILED status", () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.FAILED,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    expect(result.current.isCancellableSelection).toBe(false);
  });

  it("isCancellableSelection is false for CANCELLED status", () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.CANCELLED,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    expect(result.current.isCancellableSelection).toBe(false);
  });

  // --- initial state ---

  it("initial state has no error, no notice, not cancelling", () => {
    const bulkCancelTasks = vi.fn();

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: null,
        selectedTaskType: null,
        bulkCancelTasks,
      }),
    );

    expect(result.current.isCancelling).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.notice).toBeNull();
  });
});
