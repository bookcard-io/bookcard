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
 * Custom hook for bulk-cancelling tasks via server-side bulk operations.
 *
 * Follows SRP by focusing solely on the "cancel many tasks" workflow.
 * Uses server-side bulk endpoints for O(1) cancellation regardless of task count.
 */

import { useCallback, useMemo, useState } from "react";
import {
  bulkCancelTasks as defaultBulkCancelTasks,
  countTasks as defaultCountTasks,
} from "@/api/tasks";
import type { BulkCancelResponse, TaskStatus, TaskType } from "@/types/tasks";
import { TaskStatus as TaskStatusEnum } from "@/types/tasks";

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
   * Count tasks matching the given filters. Defaults to the API client.
   *
   * Parameters
   * ----------
   * status : TaskStatus | null
   *     Optional status filter.
   * taskType : TaskType | null
   *     Optional task type filter.
   *
   * Returns
   * -------
   * Promise<number>
   *     Count of matching tasks.
   */
  countTasks?: (
    status: TaskStatus | null,
    taskType: TaskType | null,
  ) => Promise<number>;

  /**
   * Bulk-cancel tasks matching the given filters. Defaults to the API client.
   *
   * Parameters
   * ----------
   * status : TaskStatus | null
   *     Optional status filter.
   * taskType : TaskType | null
   *     Optional task type filter.
   *
   * Returns
   * -------
   * Promise<BulkCancelResponse>
   *     Cancellation result.
   */
  bulkCancelTasks?: (
    status: TaskStatus | null,
    taskType: TaskType | null,
  ) => Promise<BulkCancelResponse>;

  /**
   * Refresh callback invoked once after the bulk cancel attempt finishes.
   *
   * Returns
   * -------
   * Promise<void>
   *     Resolves when refresh completes.
   */
  refresh?: () => Promise<void>;
}

export interface UseBulkCancelTasksOptions extends BulkCancelDeps {
  /** Selected status filter from UI. */
  selectedStatus: TaskStatus | null;
  /** Selected task type filter from UI. */
  selectedTaskType: TaskType | null;
}

export interface UseBulkCancelTasksResult extends BulkCancelState {
  /** Run the bulk cancel workflow. */
  cancelAll: () => Promise<void>;
  /** Get the count of tasks that would be cancelled. */
  getTaskCount: () => Promise<number>;
  /** Whether the current filter implies no cancellable tasks. */
  isCancellableSelection: boolean;
}

const CANCELLABLE_STATUSES = new Set<TaskStatus>([
  TaskStatusEnum.PENDING,
  TaskStatusEnum.RUNNING,
]);

/**
 * Hook for bulk cancelling tasks matching the current UI filters.
 *
 * Uses server-side bulk endpoints (POST /tasks/bulk-cancel) for efficient
 * cancellation at any scale, rather than fetching tasks and cancelling
 * them one by one.
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
    refresh,
    countTasks = (status, taskType) => defaultCountTasks({ status, taskType }),
    bulkCancelTasks = (status, taskType) =>
      defaultBulkCancelTasks({ status, taskType }),
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

  const getTaskCount = useCallback(async (): Promise<number> => {
    if (selectedStatus && !CANCELLABLE_STATUSES.has(selectedStatus)) {
      return 0;
    }

    try {
      if (selectedStatus) {
        return await countTasks(selectedStatus, selectedTaskType);
      }
      const [pending, running] = await Promise.all([
        countTasks(TaskStatusEnum.PENDING, selectedTaskType),
        countTasks(TaskStatusEnum.RUNNING, selectedTaskType),
      ]);
      return pending + running;
    } catch {
      return 0;
    }
  }, [selectedStatus, selectedTaskType, countTasks]);

  const cancelAll = useCallback(async () => {
    if (isCancelling) {
      return;
    }

    setError(null);
    setNotice(null);
    setIsCancelling(true);

    try {
      if (selectedStatus && !CANCELLABLE_STATUSES.has(selectedStatus)) {
        setNotice(
          "No cancellable tasks for the selected status. Only pending/running tasks can be cancelled.",
        );
        return;
      }

      const result = await bulkCancelTasks(selectedStatus, selectedTaskType);

      await refresh?.();

      if (result.cancelled === 0) {
        setNotice("No tasks to cancel.");
      } else {
        setNotice(`Cancelled ${result.cancelled} task(s).`);
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
    bulkCancelTasks,
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
