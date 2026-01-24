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

"use client";

import { useState, useCallback } from "react";
import { ScheduledTasksConfig } from "@/components/admin/scheduledtasks/ScheduledTasksConfig";
import { TaskErrorDisplay } from "@/components/tasks/TaskErrorDisplay";
import { TaskFiltersBar } from "@/components/tasks/TaskFiltersBar";
import { TaskList } from "@/components/tasks/TaskList";
import { TaskPagination } from "@/components/tasks/TaskPagination";
import { useTaskCancellation } from "@/hooks/useTaskCancellation";
import { useTaskFilters } from "@/hooks/useTaskFilters";
import { useTasks } from "@/hooks/useTasks";
import { Button } from "@/components/forms/Button";
import { TaskStatus } from "@/types/tasks";

/**
 * Scheduled Tasks tab component for admin panel.
 *
 * Displays scheduled tasks with filtering, pagination, and cancellation.
 * Follows SRP by orchestrating specialized components and hooks.
 * Follows IOC by using dependency injection via hooks.
 * Follows SOC by separating concerns into focused components.
 * Follows DRY by reusing extracted components and hooks.
 */
export function ScheduledTasksTab() {
  const {
    tasks,
    total,
    page,
    pageSize,
    totalPages,
    isLoading,
    error,
    refresh,
    nextPage,
    previousPage,
    setPage,
    setStatus,
    setTaskType,
  } = useTasks({
    page: 1,
    pageSize: 50,
    status: null,
    taskType: null,
    autoRefresh: true,
    refreshInterval: 2000,
    enabled: true,
  });

  const filters = useTaskFilters({
    setStatus,
    setTaskType,
    setPage,
  });

  const { cancelTask } = useTaskCancellation({
    onRefresh: refresh,
  });

  const [isBulkCancelling, setIsBulkCancelling] = useState(false);

  /**
   * Handles bulk cancellation of all pending and running tasks.
   */
  const handleCancelAll = useCallback(async () => {
    const tasksToCancel = tasks.filter(
      (t) => t.status === TaskStatus.PENDING || t.status === TaskStatus.RUNNING
    );

    if (tasksToCancel.length === 0) return;

    if (!window.confirm(`Are you sure you want to cancel all ${tasksToCancel.length} pending/running tasks?`)) {
      return;
    }

    setIsBulkCancelling(true);
    try {
      // Send cancellation requests for all filtered tasks in parallel
      await Promise.allSettled(tasksToCancel.map((t) => cancelTask(t.id)));
      
      // Add a 1-second delay to allow the server enough time to 
      // update the task statuses in the database before refetching
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Refresh the task list to reflect the updated statuses in the UI
      await refresh();
    } finally {
      setIsBulkCancelling(false);
    }
  }, [tasks, cancelTask, refresh]);

  return (
    <div className="flex flex-col gap-6">
      <ScheduledTasksConfig />

      <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
        <h2 className="mb-4 font-semibold text-text-a0 text-xl">
          Scheduled Tasks
        </h2>

        <div className="mb-4 flex items-center justify-between gap-4">
          <div className="flex-grow">
            <TaskFiltersBar
              status={filters.selectedStatus}
              taskType={filters.selectedTaskType}
              onStatusChange={filters.handleStatusFilter}
              onTaskTypeChange={filters.handleTaskTypeFilter}
              onRefresh={() => void refresh()}
            />
          </div>
          <Button
            variant="danger"
            size="small"
            onClick={handleCancelAll}
            loading={isBulkCancelling}
            disabled={isBulkCancelling || !tasks.some(t => t.status === TaskStatus.PENDING || t.status === TaskStatus.RUNNING)}
          >
            Cancel All
          </Button>
        </div>

        {error && <TaskErrorDisplay error={error} />}

        <TaskList tasks={tasks} isLoading={isLoading} onCancel={cancelTask} />

        <TaskPagination
          page={page}
          pageSize={pageSize}
          total={total}
          totalPages={totalPages}
          onPreviousPage={previousPage}
          onNextPage={nextPage}
        />
      </div>
    </div>
  );
}