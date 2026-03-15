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
 * Task API client utilities.
 *
 * This module centralizes `/api/tasks` HTTP interactions for reuse across hooks
 * and components. It is intentionally small and dependency-injected (via the
 * optional `fetchImpl`) to keep consumers testable and reduce UI-layer coupling
 * to transport details.
 */

import type {
  BulkCancelResponse,
  Task,
  TaskCountResponse,
  TaskListResponse,
  TaskStatus,
  TaskType,
} from "@/types/tasks";

export interface ListTasksParams {
  /** Page number (1-indexed). */
  page: number;
  /** Number of items per page. */
  pageSize: number;
  /** Filter by task status. */
  status?: TaskStatus | null;
  /** Filter by task type. */
  taskType?: TaskType | null;
}

export interface ListAllTasksByStatusParams {
  /** Task status to list. */
  status: TaskStatus;
  /** Optional filter by task type. */
  taskType?: TaskType | null;
  /** Page size per request (default: 200). */
  pageSize?: number;
}

export interface TaskApiDeps {
  /** Fetch implementation (defaults to global `fetch`). */
  fetchImpl?: typeof fetch;
}

async function getErrorDetail(response: Response): Promise<string | null> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    return typeof data.detail === "string" && data.detail.trim().length > 0
      ? data.detail
      : null;
  } catch {
    return null;
  }
}

function buildListTasksQuery(params: ListTasksParams): string {
  const search = new URLSearchParams({
    page: params.page.toString(),
    page_size: params.pageSize.toString(),
  });

  if (params.status) {
    search.append("status", params.status);
  }
  if (params.taskType) {
    search.append("task_type", params.taskType);
  }

  return search.toString();
}

/**
 * List tasks with pagination and optional filters.
 *
 * Parameters
 * ----------
 * params : ListTasksParams
 *     Paging and filter parameters.
 * deps : TaskApiDeps, optional
 *     Dependency injection for the HTTP client.
 *
 * Returns
 * -------
 * Promise<TaskListResponse>
 *     Task listing response.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails.
 */
export async function listTasks(
  params: ListTasksParams,
  deps: TaskApiDeps = {},
): Promise<TaskListResponse> {
  const fetchImpl = deps.fetchImpl ?? fetch;
  const query = buildListTasksQuery(params);
  const response = await fetchImpl(`/api/tasks?${query}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const detail = await getErrorDetail(response);
    throw new Error(detail || "Failed to fetch tasks");
  }

  return (await response.json()) as TaskListResponse;
}

/**
 * List all tasks for a status (fetching all pages).
 *
 * Parameters
 * ----------
 * params : ListAllTasksByStatusParams
 *     Status and optional filters.
 * deps : TaskApiDeps, optional
 *     Dependency injection for the HTTP client.
 *
 * Returns
 * -------
 * Promise[list[Task]]
 *     All tasks matching the filters.
 *
 * Raises
 * ------
 * Error
 *     If any API request fails.
 */
export async function listAllTasksByStatus(
  params: ListAllTasksByStatusParams,
  deps: TaskApiDeps = {},
): Promise<Task[]> {
  const pageSize = Math.min(params.pageSize ?? 100, 100);
  const tasks: Task[] = [];
  let page = 1;

  while (true) {
    const data = await listTasks(
      {
        page,
        pageSize,
        status: params.status,
        taskType: params.taskType ?? null,
      },
      deps,
    );

    tasks.push(...data.items);

    if (page >= data.total_pages) {
      break;
    }
    page += 1;
  }

  return tasks;
}

export interface CountTasksParams {
  /** Filter by task status. */
  status?: TaskStatus | null;
  /** Filter by task type. */
  taskType?: TaskType | null;
}

/**
 * Get a count of tasks matching the given filters.
 *
 * Parameters
 * ----------
 * params : CountTasksParams
 *     Status and optional type filter.
 * deps : TaskApiDeps, optional
 *     Dependency injection for the HTTP client.
 *
 * Returns
 * -------
 * Promise<number>
 *     Count of matching tasks.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails.
 */
export async function countTasks(
  params: CountTasksParams,
  deps: TaskApiDeps = {},
): Promise<number> {
  const fetchImpl = deps.fetchImpl ?? fetch;
  const search = new URLSearchParams();
  if (params.status) {
    search.append("status", params.status);
  }
  if (params.taskType) {
    search.append("task_type", params.taskType);
  }
  const query = search.toString();
  const url = query ? `/api/tasks/count?${query}` : "/api/tasks/count";

  const response = await fetchImpl(url, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const detail = await getErrorDetail(response);
    throw new Error(detail || "Failed to count tasks");
  }

  const data = (await response.json()) as TaskCountResponse;
  return data.count;
}

export interface BulkCancelParams {
  /** Filter by task status. */
  status?: TaskStatus | null;
  /** Filter by task type. */
  taskType?: TaskType | null;
}

/**
 * Bulk-cancel all tasks matching the given filters via a single server call.
 *
 * Parameters
 * ----------
 * params : BulkCancelParams
 *     Status and optional type filter.
 * deps : TaskApiDeps, optional
 *     Dependency injection for the HTTP client.
 *
 * Returns
 * -------
 * Promise<BulkCancelResponse>
 *     Number of tasks cancelled and status message.
 *
 * Raises
 * ------
 * Error
 *     If the API request fails.
 */
export async function bulkCancelTasks(
  params: BulkCancelParams,
  deps: TaskApiDeps = {},
): Promise<BulkCancelResponse> {
  const fetchImpl = deps.fetchImpl ?? fetch;
  const search = new URLSearchParams();
  if (params.status) {
    search.append("status", params.status);
  }
  if (params.taskType) {
    search.append("task_type", params.taskType);
  }
  const query = search.toString();
  const url = query
    ? `/api/tasks/bulk-cancel?${query}`
    : "/api/tasks/bulk-cancel";

  const response = await fetchImpl(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const detail = await getErrorDetail(response);
    throw new Error(detail || "Failed to cancel tasks");
  }

  return (await response.json()) as BulkCancelResponse;
}
