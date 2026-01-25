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

/**
 * Custom hook for bulk-cancelling tasks.
 *
 * Follows SRP by focusing solely on the "cancel many tasks" workflow.
 * Follows IOC/DIP by accepting the list and cancel functions as dependencies.
 */

import { useCallback, useMemo, useState } from "react";
import { listAllTasksByStatus } from "@/api/tasks";
import type { Task, TaskType } from "@/types/tasks";
import { TaskStatus } from "@/types/tasks";

export interface BulkCancelState {
  /** Whether a bulk cancel operation is currently running. */
  isCancelling: boolean;
  /** Error message (if any) from the last bulk operation. */
  error: string | null;
  /** Informational notice (if any) from the last bulk operation. */
  notice: string | null;
}

export interface BulkCancelDeps {
  /**
   * Fetch all tasks by status (typically paginated on the backend).
   *
   * Parameters
   * ----------
   * status : TaskStatus
   *     Task status to list.
   * taskType : TaskType | null
   *     Optional task type filter.
   *
   * Returns
   * -------
   * Promise[list[Task]]
   *     All tasks matching the given status and optional type filter.
   */
  listAllByStatus?: (
    status: TaskStatus,
    taskType: TaskType | null,
  ) => Promise<Task[]>;

  /**
   * Cancel a task by ID.
   *
   * Parameters
   * ----------
   * taskId : number
   *     Task ID to cancel.
   *
   * Returns
   * -------
   * Promise[bool]
   *     True if cancelled; otherwise False.
   */
  cancelTask: (taskId: number) => Promise<boolean>;

  /**
   * Refresh callback invoked once after the bulk cancel attempt finishes.
   *
   * Returns
   * -------
   * Promise[None]
   *     Resolves when refresh completes.
   */
  refresh?: () => Promise<void>;
}

export interface UseBulkCancelTasksOptions extends BulkCancelDeps {
  /** Selected status filter from UI. */
  selectedStatus: TaskStatus | null;
  /** Selected task type filter from UI. */
  selectedTaskType: TaskType | null;
  /** Concurrency limit for cancellation requests (default: 10). */
  concurrency?: number;
}

export interface UseBulkCancelTasksResult extends BulkCancelState {
  /** Run the bulk cancel workflow. */
  cancelAll: () => Promise<void>;
  /** Get the count of tasks that would be cancelled. */
  getTaskCount: () => Promise<number>;
  /** Whether the current filter implies no cancellable tasks. */
  isCancellableSelection: boolean;
}

async function mapWithConcurrency<T, R>(
  items: readonly T[],
  concurrency: number,
  mapper: (item: T) => Promise<R>,
): Promise<R[]> {
  if (items.length === 0) {
    return [];
  }

  const limit = Math.max(1, Math.floor(concurrency));
  const results = new Array<R>(items.length);
  let nextIndex = 0;

  await Promise.all(
    Array.from({ length: Math.min(limit, items.length) }).map(async () => {
      while (true) {
        const index = nextIndex;
        nextIndex += 1;
        if (index >= items.length) {
          break;
        }
        results[index] = await mapper(items[index] as T);
      }
    }),
  );

  return results;
}

const CANCELLABLE_STATUSES = new Set<TaskStatus>([
  TaskStatus.PENDING,
  TaskStatus.RUNNING,
]);

/**
 * Hook for bulk cancelling tasks matching the current UI filters.
 *
 * Parameters
 * ----------
 * options : UseBulkCancelTasksOptions
 *     Configuration and injected dependencies.
 *
 * Returns
 * -------
 * UseBulkCancelTasksResult
 *     Bulk cancel function + state for displaying progress/errors/notices.
 */
export function useBulkCancelTasks(
  options: UseBulkCancelTasksOptions,
): UseBulkCancelTasksResult {
  const {
    selectedStatus,
    selectedTaskType,
    cancelTask,
    refresh,
    concurrency = 10,
    listAllByStatus = (status: TaskStatus, taskType: TaskType | null) =>
      listAllTasksByStatus({ status, taskType }),
  } = options;

  const [isCancelling, setIsCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const isCancellableSelection = useMemo(() => {
    if (!selectedStatus) {
      return true;
    }
    return CANCELLABLE_STATUSES.has(selectedStatus);
  }, [selectedStatus]);

  /**
   * Get the count of tasks that would be cancelled.
   *
   * Returns
   * -------
   * Promise[int]
   *     Number of tasks that would be cancelled, or 0 if none.
   */
  const getTaskCount = useCallback(async (): Promise<number> => {
    const statusesToCancel: TaskStatus[] = selectedStatus
      ? [selectedStatus]
      : [TaskStatus.PENDING, TaskStatus.RUNNING];

    // Respect the current status filter: if it's not cancellable, return 0.
    if (statusesToCancel.some((s) => !CANCELLABLE_STATUSES.has(s))) {
      return 0;
    }

    try {
      const taskLists = await Promise.all(
        statusesToCancel.map((s) => listAllByStatus(s, selectedTaskType)),
      );
      return taskLists.flat().length;
    } catch {
      return 0;
    }
  }, [selectedStatus, selectedTaskType, listAllByStatus]);

  const cancelAll = useCallback(async () => {
    if (isCancelling) {
      return;
    }

    setError(null);
    setNotice(null);
    setIsCancelling(true);

    try {
      const statusesToCancel: TaskStatus[] = selectedStatus
        ? [selectedStatus]
        : [TaskStatus.PENDING, TaskStatus.RUNNING];

      // Respect the current status filter: if it's not cancellable, this is a no-op.
      if (statusesToCancel.some((s) => !CANCELLABLE_STATUSES.has(s))) {
        setNotice(
          "No cancellable tasks for the selected status. Only pending/running tasks can be cancelled.",
        );
        return;
      }

      const taskLists = await Promise.all(
        statusesToCancel.map((s) => listAllByStatus(s, selectedTaskType)),
      );

      const tasksToCancel = taskLists.flat();
      if (tasksToCancel.length === 0) {
        setNotice("No tasks to cancel.");
        return;
      }

      const results = await mapWithConcurrency(
        tasksToCancel,
        concurrency,
        async (task) => cancelTask(task.id),
      );

      await refresh?.();

      const failedCount = results.filter((r) => !r).length;
      if (failedCount > 0) {
        setNotice(
          `Cancelled ${
            tasksToCancel.length - failedCount
          } of ${tasksToCancel.length} tasks. Some tasks may have completed before cancellation.`,
        );
      } else {
        setNotice(`Cancelled ${tasksToCancel.length} task(s).`);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to cancel tasks");
    } finally {
      setIsCancelling(false);
    }
  }, [
    isCancelling,
    selectedStatus,
    selectedTaskType,
    listAllByStatus,
    concurrency,
    cancelTask,
    refresh,
  ]);

  return {
    cancelAll,
    getTaskCount,
    isCancelling,
    error,
    notice,
    isCancellableSelection,
  };
}
