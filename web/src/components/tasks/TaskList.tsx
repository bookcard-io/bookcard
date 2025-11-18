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
import { TaskItem } from "@/components/tasks/TaskItem";
import type { Task } from "@/types/tasks";

export interface TaskListProps {
  /**List of tasks to display. */
  tasks: Task[];
  /**Whether data is loading. */
  isLoading?: boolean;
  /**Callback when a task is cancelled. */
  onCancel?: (taskId: number) => Promise<boolean>;
  /**Optional className. */
  className?: string;
}

/**
 * Task list component.
 *
 * Displays a list of tasks with cancellation support.
 * Follows SRP by focusing solely on task list rendering.
 */
export function TaskList({
  tasks,
  isLoading = false,
  onCancel,
  className,
}: TaskListProps) {
  const [cancellingIds, setCancellingIds] = useState<Set<number>>(new Set());

  const handleCancel = useCallback(
    async (taskId: number) => {
      if (cancellingIds.has(taskId) || !onCancel) {
        return;
      }

      setCancellingIds((prev) => new Set(prev).add(taskId));
      try {
        await onCancel(taskId);
      } finally {
        setCancellingIds((prev) => {
          const next = new Set(prev);
          next.delete(taskId);
          return next;
        });
      }
    },
    [onCancel, cancellingIds],
  );

  if (isLoading && tasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500 dark:text-gray-400">Loading tasks...</div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="mb-2 text-gray-500 dark:text-gray-400">No tasks found</p>
        <p className="text-gray-400 text-sm dark:text-gray-500">
          Tasks will appear here when you upload books or perform other
          operations
        </p>
      </div>
    );
  }

  return (
    <div className={className}>
      <div className="space-y-2">
        {tasks.map((task) => (
          <TaskItem
            key={task.id}
            task={task}
            onCancel={handleCancel}
            isCancelling={cancellingIds.has(task.id)}
          />
        ))}
      </div>
    </div>
  );
}
