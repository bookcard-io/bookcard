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

/**Custom hook for polling task status.

Follows SRP by focusing solely on task polling logic.
Follows IOC by accepting callbacks as dependencies.
*/

import { useCallback } from "react";
import type { Task } from "@/types/tasks";

export interface UseTaskPollingOptions {
  /**Maximum number of polling attempts. */
  maxAttempts?: number;
  /**Polling interval in milliseconds. */
  pollInterval?: number;
  /**Maximum retries when task is completed but book_id missing. */
  maxCompletedRetries?: number;
  /**Request timeout in milliseconds. */
  requestTimeout?: number;
  /**Callback when task completes successfully with book IDs. */
  onSuccess?: (bookIds: number[]) => void;
  /**Callback when task fails or is cancelled. */
  onError?: (error: string) => void;
  /**Callback to set error message for display. */
  onSetErrorMessage?: (message: string) => void;
  /**Callback to set success message for display. */
  onSetSuccessMessage?: (message: string) => void;
}

export interface UseTaskPollingResult {
  /**Poll a task until completion and extract book IDs. */
  pollTask: (taskId: number) => Promise<number[] | null>;
}

/**
 * Hook for polling task status until completion.
 *
 * Polls a task and extracts book_ids from metadata when complete.
 * Follows SRP by handling only polling logic.
 * Follows IOC by accepting callbacks as dependencies.
 *
 * Parameters
 * ----------
 * options : UseTaskPollingOptions
 *     Configuration including callbacks and timing options.
 *
 * Returns
 * -------
 * UseTaskPollingResult
 *     Polling function.
 */
export function useTaskPolling(
  options: UseTaskPollingOptions = {},
): UseTaskPollingResult {
  const {
    maxAttempts = 300,
    pollInterval = 1500,
    maxCompletedRetries = 3,
    requestTimeout = 10000,
    onSuccess,
    onError,
    onSetErrorMessage,
  } = options;

  /**
   * Delay helper that yields to event loop.
   */
  const delay = useCallback(
    (ms: number) =>
      new Promise<void>((resolve) => {
        if (typeof window !== "undefined" && "requestIdleCallback" in window) {
          window.requestIdleCallback(
            () => {
              setTimeout(() => resolve(), ms);
            },
            { timeout: ms },
          );
        } else {
          setTimeout(() => resolve(), ms);
        }
      }),
    [],
  );

  /**
   * Yield to event loop.
   */
  const yieldToEventLoop = useCallback(
    () =>
      new Promise<void>((resolve) => {
        if (typeof window !== "undefined" && "requestIdleCallback" in window) {
          window.requestIdleCallback(() => resolve(), { timeout: 0 });
        } else {
          setTimeout(() => resolve(), 0);
        }
      }),
    [],
  );

  /**
   * Extract book IDs from task metadata.
   */
  const extractBookIds = useCallback((metadata: unknown): number[] | null => {
    if (!metadata || typeof metadata !== "object") {
      return null;
    }

    if ("book_ids" in metadata) {
      const value = metadata.book_ids;
      if (Array.isArray(value)) {
        return value
          .map((id) => {
            if (typeof id === "number") {
              return id;
            }
            if (typeof id === "string") {
              const parsed = parseInt(id, 10);
              return Number.isNaN(parsed) ? null : parsed;
            }
            return null;
          })
          .filter((id): id is number => id !== null);
      }
    }

    return null;
  }, []);

  /**
   * Fetch task from API.
   */
  const fetchTask = useCallback(
    async (taskId: number, signal: AbortSignal): Promise<Task> => {
      const response = await fetch(`/api/tasks/${taskId}?t=${Date.now()}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        cache: "no-store",
        signal,
      });

      if (!response.ok) {
        const errorData = (await response.json()) as { detail?: string };
        throw new Error(errorData.detail || "Failed to fetch task");
      }

      return (await response.json()) as Task;
    },
    [],
  );

  const pollTask = useCallback(
    async (taskId: number): Promise<number[] | null> => {
      let attempts = 0;
      let completedRetryCount = 0;

      while (attempts < maxAttempts) {
        try {
          await yieldToEventLoop();

          const controller = new AbortController();
          const timeoutId = setTimeout(
            () => controller.abort(),
            requestTimeout,
          );

          const task = await fetchTask(taskId, controller.signal);
          clearTimeout(timeoutId);

          // Task completed successfully
          if (task.status === "completed") {
            const bookIds = extractBookIds(task.metadata);

            if (bookIds && bookIds.length > 0) {
              // Don't show message here - let the orchestrator handle it
              onSuccess?.(bookIds);
              return bookIds;
            }

            // Retry if book_ids not found (race condition handling)
            if (completedRetryCount < maxCompletedRetries) {
              completedRetryCount++;
              await delay(500);
              attempts++;
              continue;
            }

            // Max retries reached
            const errorMsg = `Task completed but book_id not found. Metadata: ${JSON.stringify(task.metadata)}`;
            onSetErrorMessage?.(errorMsg);
            onError?.(errorMsg);
            return null;
          }

          // Task failed or cancelled
          if (task.status === "failed" || task.status === "cancelled") {
            const errorMsg =
              task.error_message ||
              `Task ${task.status === "failed" ? "failed" : "was cancelled"}`;
            onSetErrorMessage?.(errorMsg);
            onError?.(errorMsg);
            return null;
          }

          // Task still running, continue polling
          await delay(pollInterval);
          attempts++;
        } catch (error) {
          // Handle abort errors
          if (error instanceof Error && error.name === "AbortError") {
            const errorMsg = "Request timeout while polling task";
            onSetErrorMessage?.(errorMsg);
            onError?.(errorMsg);
            return null;
          }

          // Other errors
          const errorMsg =
            error instanceof Error ? error.message : "Failed to poll task";
          onSetErrorMessage?.(errorMsg);
          onError?.(errorMsg);
          return null;
        }
      }

      // Max attempts reached
      const errorMsg = "Upload timed out - task did not complete in time";
      onSetErrorMessage?.(errorMsg);
      onError?.(errorMsg);
      return null;
    },
    [
      maxAttempts,
      pollInterval,
      maxCompletedRetries,
      requestTimeout,
      yieldToEventLoop,
      fetchTask,
      extractBookIds,
      delay,
      onSuccess,
      onError,
      onSetErrorMessage,
    ],
  );

  return {
    pollTask,
  };
}
