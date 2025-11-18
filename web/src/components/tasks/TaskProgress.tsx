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

import { cn } from "@/libs/utils";

export interface TaskProgressProps {
  /**Progress value (0.0 to 1.0). */
  progress: number;
  /**Task status. */
  status: string;
  /**Optional className. */
  className?: string;
}

/**
 * Task progress bar component.
 *
 * Displays a progress bar with status-based styling.
 * Follows SRP by focusing solely on progress visualization.
 */
export function TaskProgress({
  progress,
  status,
  className,
}: TaskProgressProps) {
  const percentage = Math.round(progress * 100);

  const getStatusColor = () => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "cancelled":
        return "bg-gray-500";
      case "running":
        return "bg-blue-500";
      default:
        return "bg-gray-300";
    }
  };

  return (
    <div className={cn("w-full", className)}>
      <div className="mb-0.5 flex items-center justify-between">
        <span className="text-gray-600 text-xs dark:text-gray-400">
          {percentage}%
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className={cn(
            "h-full transition-all duration-300 ease-out",
            getStatusColor(),
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
