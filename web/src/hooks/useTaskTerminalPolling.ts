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

/**
 * Custom hook for polling task status until a terminal state.
 *
 * Polls a task by ID until it reaches a terminal state (completed/failed/cancelled)
 * or until max attempts are reached.
 *
 * Follows SRP by focusing solely on generic task terminal polling.
 * Uses IOC by accepting configuration and callbacks.
 */

import { useCallback } from "react";
import type { Task } from "@/types/tasks";

export interface UseTaskTerminalPollingOptions {
  /** Maximum number of polling attempts. */
  maxAttempts?: number;
  /** Polling interval in milliseconds. */
  pollInterval?: number;
  /** Request timeout in milliseconds. */
  requestTimeout?: number;
  /** Callback invoked when a task reaches a terminal state. */
  onTerminal?: (task: Task) => void;
  /** Callback invoked on polling errors (including timeouts). */
  onError?: (error: string) => void;
}

export interface UseTaskTerminalPollingResult {
  /**
   * Poll a task until it reaches a terminal state.
   *
   * Parameters
   * ----------
   * taskId : number
   *     Task ID to poll.
   *
   * Returns
   * -------
   * Promise<Task | null>
   *     The terminal task if reached; otherwise null (e.g., timeout/max attempts).
   */
  pollToTerminal: (taskId: number) => Promise<Task | null>;
}

/**
 * Hook for polling task status until it reaches a terminal state.
 *
 * Parameters
 * ----------
 * options : UseTaskTerminalPollingOptions, optional
 *     Polling configuration and callbacks.
 *
 * Returns
 * -------
 * UseTaskTerminalPollingResult
 *     Polling function.
 */
export function useTaskTerminalPolling(
  options: UseTaskTerminalPollingOptions = {},
): UseTaskTerminalPollingResult {
  const {
    maxAttempts = 300,
    pollInterval = 1500,
    requestTimeout = 10000,
    onTerminal,
    onError,
  } = options;

  const delay = useCallback(
    (ms: number) =>
      new Promise<void>((resolve) => {
        setTimeout(() => resolve(), ms);
      }),
    [],
  );

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

  const pollToTerminal = useCallback(
    async (taskId: number): Promise<Task | null> => {
      let attempts = 0;

      while (attempts < maxAttempts) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(
            () => controller.abort(),
            requestTimeout,
          );

          const task = await fetchTask(taskId, controller.signal);
          clearTimeout(timeoutId);

          if (
            task.status === "completed" ||
            task.status === "failed" ||
            task.status === "cancelled"
          ) {
            onTerminal?.(task);
            return task;
          }

          await delay(pollInterval);
          attempts++;
        } catch (err) {
          if (err instanceof Error && err.name === "AbortError") {
            const msg = "Request timeout while polling task";
            onError?.(msg);
            return null;
          }

          const msg =
            err instanceof Error ? err.message : "Failed to poll task";
          onError?.(msg);
          return null;
        }
      }

      const msg = "Task did not complete in time";
      onError?.(msg);
      return null;
    },
    [
      delay,
      fetchTask,
      maxAttempts,
      onError,
      onTerminal,
      pollInterval,
      requestTimeout,
    ],
  );

  return { pollToTerminal };
}
