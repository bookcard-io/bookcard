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

import { useCallback, useState } from "react";
import { ScheduledTasksConfig } from "@/components/admin/scheduledtasks/ScheduledTasksConfig";
import { Button } from "@/components/forms/Button";
import { CancelAllTasksConfirmationModal } from "@/components/tasks/CancelAllTasksConfirmationModal";
import { TaskErrorDisplay } from "@/components/tasks/TaskErrorDisplay";
import { TaskFiltersBar } from "@/components/tasks/TaskFiltersBar";
import { TaskList } from "@/components/tasks/TaskList";
import { TaskPagination } from "@/components/tasks/TaskPagination";
import { useBulkCancelTasks } from "@/hooks/useBulkCancelTasks";
import { useTaskCancellation } from "@/hooks/useTaskCancellation";
import { useTaskFilters } from "@/hooks/useTaskFilters";
import { useTasks } from "@/hooks/useTasks";

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

  const bulkCancel = useBulkCancelTasks({
    selectedStatus: filters.selectedStatus,
    selectedTaskType: filters.selectedTaskType,
    cancelTask: (taskId: number) => cancelTask(taskId, { refresh: false }),
    refresh,
  });

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [taskCount, setTaskCount] = useState(0);

  /**
   * Handles opening the confirmation modal.
   * Fetches the task count first, then shows the modal.
   */
  const handleOpenModal = useCallback(async () => {
    const count = await bulkCancel.getTaskCount();
    if (count === 0) {
      // If no tasks to cancel, show notice instead of modal
      return;
    }
    setTaskCount(count);
    setIsModalOpen(true);
  }, [bulkCancel]);

  /**
   * Handles closing the confirmation modal.
   */
  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setTaskCount(0);
  }, []);

  /**
   * Handles confirming the cancellation.
   */
  const handleConfirmCancel = useCallback(async () => {
    try {
      await bulkCancel.cancelAll();
    } finally {
      // Close modal regardless of success/failure
      // Errors will be displayed via bulkCancel.error
      setIsModalOpen(false);
      setTaskCount(0);
    }
  }, [bulkCancel]);

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
            onClick={() => void handleOpenModal()}
            loading={bulkCancel.isCancelling}
            disabled={
              bulkCancel.isCancelling || !bulkCancel.isCancellableSelection
            }
          >
            Cancel all
          </Button>
        </div>

        {error && <TaskErrorDisplay error={error} />}
        {bulkCancel.error && <TaskErrorDisplay error={bulkCancel.error} />}
        {bulkCancel.notice && (
          <div className="mb-4 rounded-lg border border-surface-a20 bg-surface-a10 p-4 text-text-a0">
            {bulkCancel.notice}
          </div>
        )}

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

      <CancelAllTasksConfirmationModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onConfirm={handleConfirmCancel}
        taskCount={taskCount}
        isCancelling={bulkCancel.isCancelling}
        error={bulkCancel.error}
      />
    </div>
  );
}
