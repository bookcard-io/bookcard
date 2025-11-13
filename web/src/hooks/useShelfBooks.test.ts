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

import { vi } from "vitest";

vi.mock("@/services/shelfService", () => ({
  getShelfBooks: vi.fn(),
}));

import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { getShelfBooks } from "@/services/shelfService";
import { useShelfBooks } from "./useShelfBooks";

describe("useShelfBooks", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("should initialize with loading state", () => {
    const bookIds = [1, 2, 3];
    vi.mocked(getShelfBooks).mockResolvedValue(bookIds);

    const { result } = renderHook(() =>
      useShelfBooks({ shelfId: 1, page: 1, sortBy: "order" }),
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.bookIds).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("should load shelf books successfully", async () => {
    const bookIds = [1, 2, 3];
    vi.mocked(getShelfBooks).mockResolvedValue(bookIds);

    const { result } = renderHook(() =>
      useShelfBooks({ shelfId: 1, page: 1, sortBy: "order" }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.bookIds).toEqual(bookIds);
    expect(result.current.total).toBe(3);
    expect(result.current.error).toBeNull();
    expect(getShelfBooks).toHaveBeenCalledWith(1, 1, "order");
  });

  it("should handle error when loading shelf books", async () => {
    const errorMessage = "Failed to load shelf books";
    vi.mocked(getShelfBooks).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() =>
      useShelfBooks({ shelfId: 1, page: 1, sortBy: "order" }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.bookIds).toEqual([]);
    expect(result.current.total).toBe(0);
    expect(result.current.error).toBe(errorMessage);
  });

  it("should handle non-Error rejection", async () => {
    vi.mocked(getShelfBooks).mockRejectedValue("String error");

    const { result } = renderHook(() =>
      useShelfBooks({ shelfId: 1, page: 1, sortBy: "order" }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe("Failed to load shelf books");
  });

  it("should not load books when shelfId is 0", async () => {
    const { result } = renderHook(() =>
      useShelfBooks({ shelfId: 0, page: 1, sortBy: "order" }),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.bookIds).toEqual([]);
    expect(getShelfBooks).not.toHaveBeenCalled();
  });

  it("should use default page and sortBy values", async () => {
    const bookIds = [1, 2];
    vi.mocked(getShelfBooks).mockResolvedValue(bookIds);

    const { result } = renderHook(() => useShelfBooks({ shelfId: 1 }));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(getShelfBooks).toHaveBeenCalledWith(1, 1, "order");
  });

  it("should reload books when shelfId changes", async () => {
    const bookIds1 = [1, 2];
    const bookIds2 = [3, 4];
    vi.mocked(getShelfBooks)
      .mockResolvedValueOnce(bookIds1)
      .mockResolvedValueOnce(bookIds2);

    const { result, rerender } = renderHook(
      ({ shelfId }) => useShelfBooks({ shelfId, page: 1, sortBy: "order" }),
      { initialProps: { shelfId: 1 } },
    );

    await waitFor(() => {
      expect(result.current.bookIds).toEqual(bookIds1);
    });

    rerender({ shelfId: 2 });

    await waitFor(() => {
      expect(result.current.bookIds).toEqual(bookIds2);
    });

    expect(getShelfBooks).toHaveBeenCalledWith(2, 1, "order");
  });

  it("should reload books when page changes", async () => {
    const bookIds1 = [1, 2];
    const bookIds2 = [3, 4];
    vi.mocked(getShelfBooks)
      .mockResolvedValueOnce(bookIds1)
      .mockResolvedValueOnce(bookIds2);

    const { result, rerender } = renderHook(
      ({ page }) => useShelfBooks({ shelfId: 1, page, sortBy: "order" }),
      { initialProps: { page: 1 } },
    );

    await waitFor(() => {
      expect(result.current.bookIds).toEqual(bookIds1);
    });

    rerender({ page: 2 });

    await waitFor(() => {
      expect(result.current.bookIds).toEqual(bookIds2);
    });

    expect(getShelfBooks).toHaveBeenCalledWith(1, 2, "order");
  });

  it("should reload books when sortBy changes", async () => {
    const bookIds1 = [1, 2];
    const bookIds2 = [3, 4];
    vi.mocked(getShelfBooks)
      .mockResolvedValueOnce(bookIds1)
      .mockResolvedValueOnce(bookIds2);

    const { result, rerender } = renderHook(
      ({ sortBy }) => useShelfBooks({ shelfId: 1, page: 1, sortBy }),
      { initialProps: { sortBy: "order" } },
    );

    await waitFor(() => {
      expect(result.current.bookIds).toEqual(bookIds1);
    });

    rerender({ sortBy: "date_added" });

    await waitFor(() => {
      expect(result.current.bookIds).toEqual(bookIds2);
    });

    expect(getShelfBooks).toHaveBeenCalledWith(1, 1, "date_added");
  });

  it("should refresh books", async () => {
    const bookIds1 = [1, 2];
    const bookIds2 = [3, 4];
    vi.mocked(getShelfBooks)
      .mockResolvedValueOnce(bookIds1)
      .mockResolvedValueOnce(bookIds2);

    const { result } = renderHook(() =>
      useShelfBooks({ shelfId: 1, page: 1, sortBy: "order" }),
    );

    await waitFor(() => {
      expect(result.current.bookIds).toEqual(bookIds1);
    });

    await result.current.refresh();

    await waitFor(() => {
      expect(result.current.bookIds).toEqual(bookIds2);
    });
  });
});
