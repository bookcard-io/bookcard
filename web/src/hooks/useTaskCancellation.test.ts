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

import { renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useTaskCancellation } from "./useTaskCancellation";

describe("useTaskCancellation", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("should return cancelTask function", () => {
    const { result } = renderHook(() => useTaskCancellation());

    expect(result.current.cancelTask).toBeDefined();
    expect(typeof result.current.cancelTask).toBe("function");
  });

  it("should cancel task successfully with refresh callback", async () => {
    const onRefresh = vi.fn().mockResolvedValue(undefined);
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ success: true }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useTaskCancellation({ onRefresh }));

    const success = await result.current.cancelTask(123);

    expect(success).toBe(true);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/tasks/123/cancel",
      expect.objectContaining({
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }),
    );
    expect(onRefresh).toHaveBeenCalled();
  });

  it("should cancel task successfully without refresh callback", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ success: true }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useTaskCancellation());

    const success = await result.current.cancelTask(123);

    expect(success).toBe(true);
    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should return false when cancel fails", async () => {
    const mockResponse = {
      ok: false,
      status: 400,
      json: vi.fn().mockResolvedValue({ detail: "Task not found" }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useTaskCancellation());

    const success = await result.current.cancelTask(123);

    expect(success).toBe(false);
    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should return false when cancel returns success: false", async () => {
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ success: false }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useTaskCancellation());

    const success = await result.current.cancelTask(123);

    expect(success).toBe(false);
    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should return false when fetch throws error", async () => {
    const error = new Error("Network error");
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    const { result } = renderHook(() => useTaskCancellation());

    const success = await result.current.cancelTask(123);

    expect(success).toBe(false);
    expect(globalThis.fetch).toHaveBeenCalled();
  });

  it("should not call refresh when success is false", async () => {
    const onRefresh = vi.fn().mockResolvedValue(undefined);
    const mockResponse = {
      ok: true,
      json: vi.fn().mockResolvedValue({ success: false }),
    };
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockResponse,
    );

    const { result } = renderHook(() => useTaskCancellation({ onRefresh }));

    await result.current.cancelTask(123);

    expect(onRefresh).not.toHaveBeenCalled();
  });
});
