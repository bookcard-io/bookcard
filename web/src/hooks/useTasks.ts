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

/**Custom hook for fetching and managing tasks.

Follows SRP by focusing solely on task data management.
Follows IOC by accepting callbacks and configuration options.
*/

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  Task,
  TaskListResponse,
  TaskStatus,
  TaskType,
} from "@/types/tasks";

export interface UseTasksOptions {
  /**Page number (1-indexed). */
  page?: number;
  /**Number of items per page. */
  pageSize?: number;
  /**Filter by task status. */
  status?: TaskStatus | null;
  /**Filter by task type. */
  taskType?: TaskType | null;
  /**Whether to auto-refresh tasks. */
  autoRefresh?: boolean;
  /**Refresh interval in milliseconds (default: 2000). */
  refreshInterval?: number;
  /**Whether to enable fetching. */
  enabled?: boolean;
}

export interface UseTasksResult {
  /**List of tasks. */
  tasks: Task[];
  /**Total number of tasks. */
  total: number;
  /**Current page number. */
  page: number;
  /**Number of items per page. */
  pageSize: number;
  /**Total number of pages. */
  totalPages: number;
  /**Whether data is loading. */
  isLoading: boolean;
  /**Error message if fetch failed. */
  error: string | null;
  /**Refresh the tasks list. */
  refresh: () => Promise<void>;
  /**Go to next page. */
  nextPage: () => void;
  /**Go to previous page. */
  previousPage: () => void;
  /**Set page number. */
  setPage: (page: number) => void;
  /**Set status filter. */
  setStatus: (status: TaskStatus | null) => void;
  /**Set task type filter. */
  setTaskType: (taskType: TaskType | null) => void;
}

/**
 * Hook for fetching and managing tasks.
 *
 * Parameters
 * ----------
 * options : UseTasksOptions
 *     Configuration options for the hook.
 *
 * Returns
 * -------
 * UseTasksResult
 *     Tasks data, loading state, and control functions.
 */
export function useTasks(options: UseTasksOptions = {}): UseTasksResult {
  const {
    page: initialPage = 1,
    pageSize: initialPageSize = 50,
    status: initialStatus = null,
    taskType: initialTaskType = null,
    autoRefresh = false,
    refreshInterval = 2000,
    enabled = true,
  } = options;

  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(initialPage);
  const [pageSize, _setPageSize] = useState(initialPageSize);
  const [status, setStatus] = useState<TaskStatus | null>(initialStatus);
  const [taskType, setTaskType] = useState<TaskType | null>(initialTaskType);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track if we're in auto-refresh mode to avoid jitters
  const isAutoRefreshingRef = useRef(false);
  const hasInitialLoadRef = useRef(false);

  const fetchTasks = useCallback(async () => {
    if (!enabled) {
      return;
    }

    // Don't show loading state during auto-refresh to avoid jitters
    const isAutoRefresh =
      isAutoRefreshingRef.current && hasInitialLoadRef.current;
    if (!isAutoRefresh) {
      setIsLoading(true);
    }

    // Only clear error on manual refresh, not auto-refresh
    if (!isAutoRefresh) {
      setError(null);
    }

    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (status) {
        params.append("status", status);
      }
      if (taskType) {
        params.append("task_type", taskType);
      }

      const response = await fetch(`/api/tasks?${params.toString()}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to fetch tasks");
      }

      const data = (await response.json()) as TaskListResponse;

      // Update tasks - always update to ensure UI reflects latest state
      setTasks((prevTasks) => {
        // If list length changed, definitely update
        if (prevTasks.length !== data.items.length) {
          return data.items;
        }

        // Quick check: compare tasks by ID to handle reordering
        const prevTaskMap = new Map(prevTasks.map((t) => [t.id, t]));
        let hasChanges = false;

        for (const newTask of data.items) {
          const oldTask = prevTaskMap.get(newTask.id);

          // New task or task removed
          if (!oldTask) {
            hasChanges = true;
            break;
          }

          // Check if any relevant fields changed
          if (
            oldTask.status !== newTask.status ||
            oldTask.progress !== newTask.progress ||
            oldTask.error_message !== newTask.error_message ||
            oldTask.completed_at !== newTask.completed_at ||
            oldTask.started_at !== newTask.started_at ||
            oldTask.duration !== newTask.duration ||
            oldTask.cancelled_at !== newTask.cancelled_at
          ) {
            hasChanges = true;
            break;
          }
        }

        // No changes detected, return previous state (no-op)
        if (!hasChanges) {
          return prevTasks;
        }

        // Data changed, return new data
        return data.items;
      });

      setTotal((prevTotal) => {
        // Only update if total actually changed
        return data.total !== prevTotal ? data.total : prevTotal;
      });

      hasInitialLoadRef.current = true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      // Only set error if it's not during auto-refresh
      if (!isAutoRefresh) {
        setError(message);
        setTasks([]);
      }
    } finally {
      if (!isAutoRefresh) {
        setIsLoading(false);
      }
    }
  }, [enabled, page, pageSize, status, taskType]);

  useEffect(() => {
    void fetchTasks();
  }, [fetchTasks]);

  // Auto-refresh if enabled
  useEffect(() => {
    if (!autoRefresh || !enabled) {
      isAutoRefreshingRef.current = false;
      return;
    }

    isAutoRefreshingRef.current = true;
    const interval = setInterval(() => {
      void fetchTasks();
    }, refreshInterval);

    return () => {
      clearInterval(interval);
      isAutoRefreshingRef.current = false;
    };
  }, [autoRefresh, enabled, refreshInterval, fetchTasks]);

  const nextPage = useCallback(() => {
    setPage((prev) => prev + 1);
  }, []);

  const previousPage = useCallback(() => {
    setPage((prev) => Math.max(1, prev - 1));
  }, []);

  const totalPages = Math.ceil(total / pageSize) || 0;

  return {
    tasks,
    total,
    page,
    pageSize,
    totalPages,
    isLoading,
    error,
    refresh: fetchTasks,
    nextPage,
    previousPage,
    setPage,
    setStatus,
    setTaskType,
  };
}
