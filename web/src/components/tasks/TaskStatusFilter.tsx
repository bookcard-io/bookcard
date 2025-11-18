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

import { TaskStatus } from "@/types/tasks";

export interface TaskStatusFilterProps {
  /**Currently selected status. */
  value: TaskStatus | null;
  /**Callback when status changes. */
  onChange: (status: TaskStatus | null) => void;
  /**HTML id for the select element. */
  id?: string;
}

/**
 * Task status filter component.
 *
 * Displays a dropdown for filtering tasks by status.
 * Follows SRP by handling only status filter UI.
 * Follows IOC by accepting value and onChange as props.
 */
export function TaskStatusFilter({
  value,
  onChange,
  id = "status-filter",
}: TaskStatusFilterProps) {
  return (
    <div className="flex items-center gap-2">
      <label
        htmlFor={id}
        className="font-medium text-gray-700 text-sm dark:text-gray-300"
      >
        Status:
      </label>
      <select
        id={id}
        value={value || ""}
        onChange={(e) =>
          onChange(e.target.value ? (e.target.value as TaskStatus) : null)
        }
        className="rounded-md border border-gray-300 bg-white px-3 py-1 text-gray-900 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
      >
        <option value="">All</option>
        <option value={TaskStatus.PENDING}>Pending</option>
        <option value={TaskStatus.RUNNING}>Running</option>
        <option value={TaskStatus.COMPLETED}>Completed</option>
        <option value={TaskStatus.FAILED}>Failed</option>
        <option value={TaskStatus.CANCELLED}>Cancelled</option>
      </select>
    </div>
  );
}
