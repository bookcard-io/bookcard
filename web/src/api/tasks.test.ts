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
import type { Task, TaskListResponse } from "@/types/tasks";
import { TaskStatus, TaskType } from "@/types/tasks";
import { listAllTasksByStatus, listTasks } from "./tasks";

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
      page_size: 200,
      total_pages: 2,
    } satisfies Partial<TaskListResponse>;

    const page2 = {
      items: [makeTask(3, TaskStatus.PENDING), makeTask(4, TaskStatus.PENDING)],
      total: 4,
      page: 2,
      page_size: 200,
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
      "/api/tasks?page=1&page_size=200&status=pending",
      expect.anything(),
    );
    expect(fetchImpl).toHaveBeenNthCalledWith(
      2,
      "/api/tasks?page=2&page_size=200&status=pending",
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
