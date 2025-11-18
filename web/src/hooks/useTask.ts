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

/**Custom hook for fetching a single task.

Follows SRP by focusing solely on single task data management.
Follows IOC by accepting callbacks and configuration options.
*/

import { useCallback, useEffect, useState } from "react";
import type { Task } from "@/types/tasks";

export interface UseTaskOptions {
  /**Task ID to fetch. */
  taskId: number | null;
  /**Whether to enable fetching. */
  enabled?: boolean;
  /**Whether to auto-refresh task status. */
  autoRefresh?: boolean;
  /**Refresh interval in milliseconds (default: 1000). */
  refreshInterval?: number;
}

export interface UseTaskResult {
  /**Task data. */
  task: Task | null;
  /**Whether data is loading. */
  isLoading: boolean;
  /**Error message if fetch failed. */
  error: string | null;
  /**Refresh the task data. */
  refresh: () => Promise<void>;
  /**Cancel the task. */
  cancel: () => Promise<boolean>;
  /**Whether cancellation is in progress. */
  isCancelling: boolean;
}

/**
 * Hook for fetching and managing a single task.
 *
 * Parameters
 * ----------
 * options : UseTaskOptions
 *     Configuration options for the hook.
 *
 * Returns
 * -------
 * UseTaskResult
 *     Task data, loading state, and control functions.
 */
export function useTask(options: UseTaskOptions): UseTaskResult {
  const {
    taskId,
    enabled = true,
    autoRefresh = false,
    refreshInterval = 1000,
  } = options;

  const [task, setTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);

  const fetchTask = useCallback(async () => {
    if (!enabled || !taskId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to fetch task");
      }

      const data = (await response.json()) as Task;
      setTask(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setTask(null);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, taskId]);

  useEffect(() => {
    void fetchTask();
  }, [fetchTask]);

  // Auto-refresh if enabled and task is not in terminal state
  useEffect(() => {
    if (
      !autoRefresh ||
      !enabled ||
      !taskId ||
      !task ||
      task.status === "completed" ||
      task.status === "failed" ||
      task.status === "cancelled"
    ) {
      return;
    }

    const interval = setInterval(() => {
      void fetchTask();
    }, refreshInterval);

    return () => {
      clearInterval(interval);
    };
  }, [autoRefresh, enabled, taskId, task, refreshInterval, fetchTask]);

  const cancel = useCallback(async (): Promise<boolean> => {
    if (!taskId) {
      return false;
    }

    setIsCancelling(true);
    try {
      const response = await fetch(`/api/tasks/${taskId}/cancel`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to cancel task");
      }

      const data = (await response.json()) as { success: boolean };
      if (data.success) {
        // Refresh task to get updated status
        await fetchTask();
      }
      return data.success;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      return false;
    } finally {
      setIsCancelling(false);
    }
  }, [taskId, fetchTask]);

  return {
    task,
    isLoading,
    error,
    refresh: fetchTask,
    cancel,
    isCancelling,
  };
}
