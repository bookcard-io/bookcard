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

import { describe, expect, it, vi } from "vitest";
import type { BulkCancelResponse, Task, TaskListResponse } from "@/types/tasks";
import { TaskStatus, TaskType } from "@/types/tasks";
import {
  bulkCancelTasks,
  countTasks,
  listAllTasksByStatus,
  listTasks,
} from "./tasks";

function makeFetchResponse(payload: unknown, ok = true): Response {
  return {
    ok,
    json: vi.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

function makeTask(id: number, status: TaskStatus): Task {
  return {
    id,
    task_type: TaskType.BOOK_UPLOAD,
    status,
    progress: 0,
    user_id: 1,
    username: "test",
    created_at: "2025-01-01T00:00:00Z",
    started_at: null,
    completed_at: null,
    cancelled_at: null,
    error_message: null,
    metadata: null,
    duration: null,
  };
}

describe("api/tasks", () => {
  it("listTasks builds query params and returns parsed response", async () => {
    const mockResponse: TaskListResponse = {
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    };

    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse(mockResponse));

    const data = await listTasks(
      {
        page: 1,
        pageSize: 50,
        status: TaskStatus.RUNNING,
        taskType: TaskType.BOOK_UPLOAD,
      },
      { fetchImpl },
    );

    expect(data).toEqual(mockResponse);
    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks?page=1&page_size=50&status=running&task_type=book_upload",
      expect.objectContaining({
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  it("listTasks throws error with server-provided detail", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse({ detail: "Nope" }, false));

    await expect(
      listTasks(
        { page: 1, pageSize: 50, status: null, taskType: null },
        { fetchImpl },
      ),
    ).rejects.toThrow("Nope");
  });

  it("listTasks throws default message when detail is empty or invalid", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse({ detail: "   " }, false));

    await expect(
      listTasks(
        { page: 1, pageSize: 50, status: null, taskType: null },
        { fetchImpl },
      ),
    ).rejects.toThrow("Failed to fetch tasks");
  });

  it("listTasks throws default message when error payload is not JSON", async () => {
    const response = {
      ok: false,
      json: vi.fn().mockRejectedValue(new Error("bad json")),
    } as unknown as Response;

    const fetchImpl = vi.fn().mockResolvedValue(response);

    await expect(
      listTasks(
        { page: 1, pageSize: 50, status: null, taskType: null },
        { fetchImpl },
      ),
    ).rejects.toThrow("Failed to fetch tasks");
  });

  it("listTasks uses global fetch when fetchImpl is not provided", async () => {
    const mockResponse: TaskListResponse = {
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    };

    const fetchSpy = vi.fn().mockResolvedValue(makeFetchResponse(mockResponse));
    vi.stubGlobal("fetch", fetchSpy as unknown as typeof fetch);

    const data = await listTasks({
      page: 1,
      pageSize: 50,
      status: null,
      taskType: null,
    });

    expect(data).toEqual(mockResponse);
    expect(fetchSpy).toHaveBeenCalled();
  });

  it("listAllTasksByStatus fetches all pages and returns combined tasks", async () => {
    const page1 = {
      items: [makeTask(1, TaskStatus.PENDING), makeTask(2, TaskStatus.PENDING)],
      total: 4,
      page: 1,
      page_size: 100,
      total_pages: 2,
    } satisfies Partial<TaskListResponse>;

    const page2 = {
      items: [makeTask(3, TaskStatus.PENDING), makeTask(4, TaskStatus.PENDING)],
      total: 4,
      page: 2,
      page_size: 100,
      total_pages: 2,
    } satisfies Partial<TaskListResponse>;

    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(makeFetchResponse(page1))
      .mockResolvedValueOnce(makeFetchResponse(page2));

    const tasks = await listAllTasksByStatus(
      { status: TaskStatus.PENDING, taskType: null },
      { fetchImpl },
    );

    expect(tasks.map((t) => t.id)).toEqual([1, 2, 3, 4]);
    expect(fetchImpl).toHaveBeenNthCalledWith(
      1,
      "/api/tasks?page=1&page_size=100&status=pending",
      expect.anything(),
    );
    expect(fetchImpl).toHaveBeenNthCalledWith(
      2,
      "/api/tasks?page=2&page_size=100&status=pending",
      expect.anything(),
    );
  });

  it("listAllTasksByStatus caps pageSize at 100", async () => {
    const page1 = {
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 0,
    } satisfies Partial<TaskListResponse>;

    const fetchImpl = vi.fn().mockResolvedValueOnce(makeFetchResponse(page1));

    await listAllTasksByStatus(
      { status: TaskStatus.PENDING, pageSize: 500 },
      { fetchImpl },
    );

    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks?page=1&page_size=100&status=pending",
      expect.anything(),
    );
  });

  it("listAllTasksByStatus defaults pageSize to 100", async () => {
    const page1 = {
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
      total_pages: 0,
    } satisfies Partial<TaskListResponse>;

    const fetchImpl = vi.fn().mockResolvedValueOnce(makeFetchResponse(page1));

    await listAllTasksByStatus({ status: TaskStatus.RUNNING }, { fetchImpl });

    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks?page=1&page_size=100&status=running",
      expect.anything(),
    );
  });

  it("listAllTasksByStatus respects custom pageSize and taskType", async () => {
    const page1 = {
      items: [makeTask(1, TaskStatus.RUNNING)],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    } satisfies Partial<TaskListResponse>;

    const fetchImpl = vi.fn().mockResolvedValueOnce(makeFetchResponse(page1));

    await listAllTasksByStatus(
      {
        status: TaskStatus.RUNNING,
        taskType: TaskType.BOOK_UPLOAD,
        pageSize: 10,
      },
      { fetchImpl },
    );

    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks?page=1&page_size=10&status=running&task_type=book_upload",
      expect.anything(),
    );
  });
});

describe("countTasks", () => {
  it("builds query with status filter", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse({ count: 42 }));

    const result = await countTasks(
      { status: TaskStatus.PENDING },
      { fetchImpl },
    );

    expect(result).toBe(42);
    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks/count?status=pending",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("builds query with task type filter", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse({ count: 7 }));

    const result = await countTasks(
      { taskType: TaskType.BOOK_UPLOAD },
      { fetchImpl },
    );

    expect(result).toBe(7);
    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks/count?task_type=book_upload",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("builds query with both status and task type", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse({ count: 3 }));

    await countTasks(
      { status: TaskStatus.RUNNING, taskType: TaskType.LIBRARY_SCAN },
      { fetchImpl },
    );

    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks/count?status=running&task_type=library_scan",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("builds URL with no query params when filters are null", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse({ count: 100 }));

    await countTasks({ status: null, taskType: null }, { fetchImpl });

    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks/count",
      expect.anything(),
    );
  });

  it("throws error with server-provided detail", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse({ detail: "Forbidden" }, false));

    await expect(
      countTasks({ status: TaskStatus.PENDING }, { fetchImpl }),
    ).rejects.toThrow("Forbidden");
  });

  it("throws default message when error payload is not JSON", async () => {
    const response = {
      ok: false,
      json: vi.fn().mockRejectedValue(new Error("bad json")),
    } as unknown as Response;
    const fetchImpl = vi.fn().mockResolvedValue(response);

    await expect(
      countTasks({ status: TaskStatus.PENDING }, { fetchImpl }),
    ).rejects.toThrow("Failed to count tasks");
  });

  it("uses global fetch when fetchImpl is not provided", async () => {
    const fetchSpy = vi.fn().mockResolvedValue(makeFetchResponse({ count: 0 }));
    vi.stubGlobal("fetch", fetchSpy as unknown as typeof fetch);

    const result = await countTasks({ status: TaskStatus.PENDING });

    expect(result).toBe(0);
    expect(fetchSpy).toHaveBeenCalled();
  });
});

describe("bulkCancelTasks", () => {
  it("sends POST with status filter", async () => {
    const serverResponse: BulkCancelResponse = {
      cancelled: 150,
      message: "Cancelled 150 task(s)",
    };
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse(serverResponse));

    const result = await bulkCancelTasks(
      { status: TaskStatus.PENDING },
      { fetchImpl },
    );

    expect(result).toEqual(serverResponse);
    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks/bulk-cancel?status=pending",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("sends POST with task type filter", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(
        makeFetchResponse({ cancelled: 5, message: "Cancelled 5 task(s)" }),
      );

    await bulkCancelTasks({ taskType: TaskType.LIBRARY_SCAN }, { fetchImpl });

    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks/bulk-cancel?task_type=library_scan",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("sends POST with both status and task type", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(
        makeFetchResponse({ cancelled: 3, message: "Cancelled 3 task(s)" }),
      );

    await bulkCancelTasks(
      { status: TaskStatus.RUNNING, taskType: TaskType.BOOK_UPLOAD },
      { fetchImpl },
    );

    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks/bulk-cancel?status=running&task_type=book_upload",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("sends POST with no query params when filters are null", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      makeFetchResponse({
        cancelled: 0,
        message: "No cancellable tasks found",
      }),
    );

    await bulkCancelTasks({ status: null, taskType: null }, { fetchImpl });

    expect(fetchImpl).toHaveBeenCalledWith(
      "/api/tasks/bulk-cancel",
      expect.anything(),
    );
  });

  it("throws error with server-provided detail", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(makeFetchResponse({ detail: "Server error" }, false));

    await expect(
      bulkCancelTasks({ status: TaskStatus.PENDING }, { fetchImpl }),
    ).rejects.toThrow("Server error");
  });

  it("throws default message when error payload is not JSON", async () => {
    const response = {
      ok: false,
      json: vi.fn().mockRejectedValue(new Error("bad json")),
    } as unknown as Response;
    const fetchImpl = vi.fn().mockResolvedValue(response);

    await expect(
      bulkCancelTasks({ status: TaskStatus.PENDING }, { fetchImpl }),
    ).rejects.toThrow("Failed to cancel tasks");
  });

  it("uses global fetch when fetchImpl is not provided", async () => {
    const fetchSpy = vi.fn().mockResolvedValue(
      makeFetchResponse({
        cancelled: 0,
        message: "No cancellable tasks found",
      }),
    );
    vi.stubGlobal("fetch", fetchSpy as unknown as typeof fetch);

    const result = await bulkCancelTasks({ status: TaskStatus.PENDING });

    expect(result.cancelled).toBe(0);
    expect(fetchSpy).toHaveBeenCalled();
  });
});
