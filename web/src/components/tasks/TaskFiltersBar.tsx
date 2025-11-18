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

import { Button } from "@/components/forms/Button";
import type { TaskStatus, TaskType } from "@/types/tasks";
import { TaskStatusFilter } from "./TaskStatusFilter";
import { TaskTypeFilter } from "./TaskTypeFilter";

export interface TaskFiltersBarProps {
  /**Currently selected status filter. */
  status: TaskStatus | null;
  /**Currently selected task type filter. */
  taskType: TaskType | null;
  /**Callback when status filter changes. */
  onStatusChange: (status: TaskStatus | null) => void;
  /**Callback when task type filter changes. */
  onTaskTypeChange: (taskType: TaskType | null) => void;
  /**Callback when refresh button is clicked. */
  onRefresh: () => void;
}

/**
 * Task filters bar component.
 *
 * Displays filter controls and refresh button.
 * Follows SRP by handling only filter bar UI.
 * Follows IOC by accepting callbacks as props.
 * Follows DRY by composing reusable filter components.
 */
export function TaskFiltersBar({
  status,
  taskType,
  onStatusChange,
  onTaskTypeChange,
  onRefresh,
}: TaskFiltersBarProps) {
  return (
    <div className="mb-4 flex flex-wrap gap-3">
      <TaskStatusFilter value={status} onChange={onStatusChange} />
      <TaskTypeFilter value={taskType} onChange={onTaskTypeChange} />
      <Button variant="secondary" size="small" onClick={onRefresh}>
        Refresh
      </Button>
    </div>
  );
}
