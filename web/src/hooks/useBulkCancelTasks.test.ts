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
import type { Task } from "@/types/tasks";
import { TaskStatus, TaskType } from "@/types/tasks";
import { useBulkCancelTasks } from "./useBulkCancelTasks";

function makeTask(id: number, status: TaskStatus): Task {
  return {
    id,
    task_type: TaskType.BOOK_UPLOAD,
    status,
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
}

describe("useBulkCancelTasks", () => {
  it("cancels pending and running tasks when selectedStatus is null", async () => {
    const listAllByStatus = vi
      .fn()
      .mockResolvedValueOnce([makeTask(1, TaskStatus.PENDING)])
      .mockResolvedValueOnce([makeTask(2, TaskStatus.RUNNING)]);
    const cancelTask = vi.fn().mockResolvedValue(true);
    const refresh = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: null,
        selectedTaskType: null,
        listAllByStatus,
        cancelTask,
        refresh,
        concurrency: 2,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(listAllByStatus).toHaveBeenCalledWith(TaskStatus.PENDING, null);
    expect(listAllByStatus).toHaveBeenCalledWith(TaskStatus.RUNNING, null);
    expect(cancelTask).toHaveBeenCalledTimes(2);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(result.current.error).toBeNull();
    expect(result.current.notice).toContain("Cancelled 2");
  });

  it("respects selectedStatus when it is running", async () => {
    const listAllByStatus = vi
      .fn()
      .mockResolvedValueOnce([makeTask(2, TaskStatus.RUNNING)]);
    const cancelTask = vi.fn().mockResolvedValue(true);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.RUNNING,
        selectedTaskType: null,
        listAllByStatus,
        cancelTask,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(listAllByStatus).toHaveBeenCalledTimes(1);
    expect(listAllByStatus).toHaveBeenCalledWith(TaskStatus.RUNNING, null);
    expect(cancelTask).toHaveBeenCalledTimes(1);
  });

  it("is a no-op with notice when selectedStatus is not cancellable", async () => {
    const listAllByStatus = vi.fn();
    const cancelTask = vi.fn().mockResolvedValue(true);
    const refresh = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.COMPLETED,
        selectedTaskType: null,
        listAllByStatus,
        cancelTask,
        refresh,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(listAllByStatus).not.toHaveBeenCalled();
    expect(cancelTask).not.toHaveBeenCalled();
    expect(refresh).not.toHaveBeenCalled();
    expect(result.current.notice).toContain("Only pending/running");
  });

  it('sets a "No tasks to cancel." notice when listing returns empty', async () => {
    const listAllByStatus = vi.fn().mockResolvedValueOnce([]);
    const cancelTask = vi.fn().mockResolvedValue(true);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        listAllByStatus,
        cancelTask,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(cancelTask).not.toHaveBeenCalled();
    expect(result.current.notice).toBe("No tasks to cancel.");
  });

  it("ignores subsequent cancelAll calls while already cancelling", async () => {
    let resolveList: ((value: Task[]) => void) | null = null;
    const listAllByStatus = vi.fn().mockImplementation(
      () =>
        new Promise<Task[]>((resolve) => {
          resolveList = resolve;
        }),
    );
    const cancelTask = vi.fn().mockResolvedValue(true);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        listAllByStatus,
        cancelTask,
      }),
    );

    let firstPromise: Promise<void> | undefined;

    // Kick off first cancelAll but keep it pending.
    await act(async () => {
      firstPromise = result.current.cancelAll();
    });

    // After the state update flushes, a second call should be ignored.
    await act(async () => {
      await result.current.cancelAll();
    });

    expect(listAllByStatus).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveList?.([makeTask(1, TaskStatus.PENDING)]);
      await firstPromise;
    });
  });

  it("reports partial failures in the notice", async () => {
    const listAllByStatus = vi
      .fn()
      .mockResolvedValueOnce([
        makeTask(1, TaskStatus.PENDING),
        makeTask(2, TaskStatus.PENDING),
      ]);
    const cancelTask = vi
      .fn()
      .mockResolvedValueOnce(true)
      .mockResolvedValueOnce(false);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        listAllByStatus,
        cancelTask,
        concurrency: 2,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(result.current.notice).toContain("Cancelled 1 of 2");
  });

  it("sets error when listing tasks fails", async () => {
    const listAllByStatus = vi.fn().mockRejectedValue(new Error("Boom"));
    const cancelTask = vi.fn().mockResolvedValue(true);

    const { result } = renderHook(() =>
      useBulkCancelTasks({
        selectedStatus: TaskStatus.PENDING,
        selectedTaskType: null,
        listAllByStatus,
        cancelTask,
      }),
    );

    await act(async () => {
      await result.current.cancelAll();
    });

    expect(result.current.error).toBe("Boom");
  });
});
