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

/**Custom hook for task filtering.

Follows SRP by focusing solely on filter state management.
Follows IOC by accepting setter callbacks as dependencies.
*/

import { useCallback, useState } from "react";
import type { TaskStatus, TaskType } from "@/types/tasks";

export interface UseTaskFiltersOptions {
  /**Callback to set status filter in useTasks hook. */
  setStatus: (status: TaskStatus | null) => void;
  /**Callback to set task type filter in useTasks hook. */
  setTaskType: (taskType: TaskType | null) => void;
  /**Callback to reset page to 1 when filter changes. */
  setPage: (page: number) => void;
}

export interface UseTaskFiltersResult {
  /**Currently selected status filter. */
  selectedStatus: TaskStatus | null;
  /**Currently selected task type filter. */
  selectedTaskType: TaskType | null;
  /**Handle status filter change. */
  handleStatusFilter: (status: TaskStatus | null) => void;
  /**Handle task type filter change. */
  handleTaskTypeFilter: (taskType: TaskType | null) => void;
}

/**
 * Hook for managing task filters.
 *
 * Manages filter state and coordinates with useTasks hook.
 * Follows SRP by handling only filter state concerns.
 * Follows IOC by accepting setter callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseTaskFiltersOptions
 *     Configuration including setter callbacks.
 *
 * Returns
 * -------
 * UseTaskFiltersResult
 *     Filter state and handlers.
 */
export function useTaskFilters(
  options: UseTaskFiltersOptions,
): UseTaskFiltersResult {
  const { setStatus, setTaskType, setPage } = options;

  const [selectedStatus, setSelectedStatus] = useState<TaskStatus | null>(null);
  const [selectedTaskType, setSelectedTaskType] = useState<TaskType | null>(
    null,
  );

  const handleStatusFilter = useCallback(
    (status: TaskStatus | null) => {
      setSelectedStatus(status);
      setStatus(status);
      setPage(1);
    },
    [setStatus, setPage],
  );

  const handleTaskTypeFilter = useCallback(
    (taskType: TaskType | null) => {
      setSelectedTaskType(taskType);
      setTaskType(taskType);
      setPage(1);
    },
    [setTaskType, setPage],
  );

  return {
    selectedStatus,
    selectedTaskType,
    handleStatusFilter,
    handleTaskTypeFilter,
  };
}
