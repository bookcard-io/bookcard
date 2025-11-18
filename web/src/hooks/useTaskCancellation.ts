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

/**Custom hook for task cancellation.

Follows SRP by focusing solely on task cancellation concerns.
Follows IOC by accepting refresh callback as dependency.
*/

import { useCallback } from "react";

export interface UseTaskCancellationOptions {
  /**Callback to refresh tasks list after cancellation. */
  onRefresh?: () => Promise<void>;
}

export interface UseTaskCancellationResult {
  /**Cancel a task by ID. */
  cancelTask: (taskId: number) => Promise<boolean>;
}

/**
 * Hook for cancelling tasks.
 *
 * Handles task cancellation API calls and refreshes the task list on success.
 * Follows SRP by handling only cancellation logic.
 * Follows IOC by accepting refresh callback as dependency.
 *
 * Parameters
 * ----------
 * options : UseTaskCancellationOptions
 *     Configuration including refresh callback.
 *
 * Returns
 * -------
 * UseTaskCancellationResult
 *     Cancellation function.
 */
export function useTaskCancellation(
  options: UseTaskCancellationOptions = {},
): UseTaskCancellationResult {
  const { onRefresh } = options;

  const cancelTask = useCallback(
    async (taskId: number): Promise<boolean> => {
      try {
        const response = await fetch(`/api/tasks/${taskId}/cancel`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          const errorData = (await response.json()) as { detail?: string };
          throw new Error(errorData.detail || "Failed to cancel task");
        }

        const data = (await response.json()) as { success: boolean };
        if (data.success && onRefresh) {
          await onRefresh();
        }
        return data.success;
      } catch {
        return false;
      }
    },
    [onRefresh],
  );

  return {
    cancelTask,
  };
}
