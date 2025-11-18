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

import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { TaskStatus, TaskType } from "@/types/tasks";
import { useTaskFilters } from "./useTaskFilters";

describe("useTaskFilters", () => {
  it("should initialize with null filters", () => {
    const setStatus = vi.fn();
    const setTaskType = vi.fn();
    const setPage = vi.fn();

    const { result } = renderHook(() =>
      useTaskFilters({ setStatus, setTaskType, setPage }),
    );

    expect(result.current.selectedStatus).toBeNull();
    expect(result.current.selectedTaskType).toBeNull();
  });

  it("should handle status filter change", () => {
    const setStatus = vi.fn();
    const setTaskType = vi.fn();
    const setPage = vi.fn();

    const { result } = renderHook(() =>
      useTaskFilters({ setStatus, setTaskType, setPage }),
    );

    act(() => {
      result.current.handleStatusFilter("completed" as TaskStatus);
    });

    expect(result.current.selectedStatus).toBe("completed");
    expect(setStatus).toHaveBeenCalledWith("completed");
    expect(setPage).toHaveBeenCalledWith(1);
  });

  it("should handle task type filter change", () => {
    const setStatus = vi.fn();
    const setTaskType = vi.fn();
    const setPage = vi.fn();

    const { result } = renderHook(() =>
      useTaskFilters({ setStatus, setTaskType, setPage }),
    );

    act(() => {
      result.current.handleTaskTypeFilter("book_upload" as TaskType);
    });

    expect(result.current.selectedTaskType).toBe("book_upload");
    expect(setTaskType).toHaveBeenCalledWith("book_upload");
    expect(setPage).toHaveBeenCalledWith(1);
  });

  it("should handle status filter reset to null", () => {
    const setStatus = vi.fn();
    const setTaskType = vi.fn();
    const setPage = vi.fn();

    const { result } = renderHook(() =>
      useTaskFilters({ setStatus, setTaskType, setPage }),
    );

    act(() => {
      result.current.handleStatusFilter("completed" as TaskStatus);
    });

    act(() => {
      result.current.handleStatusFilter(null);
    });

    expect(result.current.selectedStatus).toBeNull();
    expect(setStatus).toHaveBeenCalledWith(null);
    expect(setPage).toHaveBeenCalledWith(1);
  });

  it("should handle task type filter reset to null", () => {
    const setStatus = vi.fn();
    const setTaskType = vi.fn();
    const setPage = vi.fn();

    const { result } = renderHook(() =>
      useTaskFilters({ setStatus, setTaskType, setPage }),
    );

    act(() => {
      result.current.handleTaskTypeFilter("book_upload" as TaskType);
    });

    act(() => {
      result.current.handleTaskTypeFilter(null);
    });

    expect(result.current.selectedTaskType).toBeNull();
    expect(setTaskType).toHaveBeenCalledWith(null);
    expect(setPage).toHaveBeenCalledWith(1);
  });

  it("should reset page when changing filters multiple times", () => {
    const setStatus = vi.fn();
    const setTaskType = vi.fn();
    const setPage = vi.fn();

    const { result } = renderHook(() =>
      useTaskFilters({ setStatus, setTaskType, setPage }),
    );

    act(() => {
      result.current.handleStatusFilter("pending" as TaskStatus);
    });

    act(() => {
      result.current.handleStatusFilter("running" as TaskStatus);
    });

    expect(setPage).toHaveBeenCalledTimes(2);
    expect(setPage).toHaveBeenNthCalledWith(1, 1);
    expect(setPage).toHaveBeenNthCalledWith(2, 1);
  });
});
