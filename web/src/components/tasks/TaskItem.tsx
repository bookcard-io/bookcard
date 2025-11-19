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

import { useCallback } from "react";
import { Button } from "@/components/forms/Button";
import { cn } from "@/libs/utils";
import { type Task, TaskStatus } from "@/types/tasks";

export interface TaskItemProps {
  /**Task data. */
  task: Task;
  /**Callback when task is cancelled. */
  onCancel?: (taskId: number) => void;
  /**Whether cancellation is in progress. */
  isCancelling?: boolean;
  /**Optional className. */
  className?: string;
}

/**
 * Task item component for displaying task details in a list.
 *
 * Displays task information, progress, and cancellation button.
 * Follows SRP by focusing solely on task item rendering.
 */
export function TaskItem({
  task,
  onCancel,
  isCancelling = false,
  className,
}: TaskItemProps) {
  const handleCancel = useCallback(() => {
    if (
      task.status !== TaskStatus.PENDING &&
      task.status !== TaskStatus.RUNNING
    ) {
      return;
    }
    onCancel?.(task.id);
  }, [task.id, task.status, onCancel]);

  const getTaskTypeLabel = (type: string) => {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) {
      return "-";
    }
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    if (seconds < 3600) {
      return `${Math.round(seconds / 60)}m`;
    }
    return `${Math.round(seconds / 3600)}h`;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) {
      return "-";
    }
    return new Date(dateString).toLocaleString();
  };

  const formatMetadata = (metadata: Record<string, unknown> | null) => {
    if (!metadata || typeof metadata !== "object") {
      return null;
    }
    const entries = Object.entries(metadata)
      .filter(([_, value]) => value != null)
      .map(([key, value]) => {
        const formattedValue =
          typeof value === "object" ? JSON.stringify(value) : String(value);
        return `${key}: ${formattedValue}`;
      });
    return entries.length > 0 ? entries.join(" • ") : null;
  };

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.COMPLETED:
        return "pi-check-circle";
      case TaskStatus.CANCELLED:
        return "pi-stop-circle";
      case TaskStatus.RUNNING:
        return "pi-bolt";
      case TaskStatus.FAILED:
        return "pi-times-circle";
      case TaskStatus.PENDING:
        return "pi-hourglass";
      default:
        return null;
    }
  };

  const canCancel =
    task.status === TaskStatus.PENDING || task.status === TaskStatus.RUNNING;

  return (
    <div
      className={cn(
        "rounded border border-gray-200 bg-white p-2 dark:border-gray-700 dark:bg-gray-800",
        className,
      )}
    >
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <h3 className="truncate font-medium text-gray-900 text-sm dark:text-gray-100">
            {getTaskTypeLabel(task.task_type)}
          </h3>
          <span
            className={cn(
              "flex shrink-0 items-center gap-1 rounded px-1.5 py-0.5 text-xs capitalize",
              task.status === TaskStatus.COMPLETED &&
                "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
              task.status === TaskStatus.FAILED &&
                "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
              task.status === TaskStatus.CANCELLED &&
                "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200",
              task.status === TaskStatus.RUNNING &&
                "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
              task.status === TaskStatus.PENDING &&
                "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
            )}
          >
            {getStatusIcon(task.status) && (
              <i
                className={cn("pi", getStatusIcon(task.status))}
                aria-hidden="true"
              />
            )}
            {task.status}
          </span>
        </div>
        {canCancel && (
          <Button
            variant="danger"
            size="xsmall"
            onClick={handleCancel}
            disabled={isCancelling}
            loading={isCancelling}
          >
            Cancel
          </Button>
        )}
      </div>

      {formatMetadata(task.metadata) && (
        <p className="mb-1.5 truncate text-gray-600 text-xs dark:text-gray-400">
          {formatMetadata(task.metadata)}
        </p>
      )}

      {task.error_message && (
        <div className="mt-1.5 rounded border border-red-200 bg-red-50 p-1.5 text-red-800 text-xs dark:border-red-800 dark:bg-red-900/20 dark:text-red-200">
          {task.error_message}
        </div>
      )}

      <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-gray-500 text-xs dark:text-gray-400">
        {task.username && (
          <span>
            <span className="font-medium">User:</span> {task.username}
          </span>
        )}
        <span>
          <span className="font-medium">Created:</span>{" "}
          {formatDate(task.created_at)}
        </span>
        {task.started_at && (
          <span>
            <span className="font-medium">Started:</span>{" "}
            {formatDate(task.started_at)}
          </span>
        )}
        {task.completed_at && (
          <span>
            <span className="font-medium">Completed:</span>{" "}
            {formatDate(task.completed_at)}
          </span>
        )}
        {task.duration !== null && (
          <span>
            <span className="font-medium">Duration:</span>{" "}
            {formatDuration(task.duration)}
          </span>
        )}
      </div>
    </div>
  );
}
