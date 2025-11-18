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

import { TaskType } from "@/types/tasks";

export interface TaskTypeFilterProps {
  /**Currently selected task type. */
  value: TaskType | null;
  /**Callback when task type changes. */
  onChange: (taskType: TaskType | null) => void;
  /**HTML id for the select element. */
  id?: string;
}

/**
 * Task type filter component.
 *
 * Displays a dropdown for filtering tasks by type.
 * Follows SRP by handling only task type filter UI.
 * Follows IOC by accepting value and onChange as props.
 */
export function TaskTypeFilter({
  value,
  onChange,
  id = "task-type-filter",
}: TaskTypeFilterProps) {
  return (
    <div className="flex items-center gap-2">
      <label
        htmlFor={id}
        className="font-medium text-gray-700 text-sm dark:text-gray-300"
      >
        Type:
      </label>
      <select
        id={id}
        value={value || ""}
        onChange={(e) =>
          onChange(e.target.value ? (e.target.value as TaskType) : null)
        }
        className="rounded-md border border-gray-300 bg-white px-3 py-1 text-gray-900 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
      >
        <option value="">All</option>
        <option value={TaskType.BOOK_UPLOAD}>Book upload</option>
        <option value={TaskType.BOOK_CONVERT}>Book convert</option>
        <option value={TaskType.EMAIL_SEND}>Email send</option>
        <option value={TaskType.METADATA_BACKUP}>Metadata backup</option>
        <option value={TaskType.THUMBNAIL_GENERATE}>Generate thumbnails</option>
        <option value={TaskType.LIBRARY_SCAN}>Library scan</option>
      </select>
    </div>
  );
}
