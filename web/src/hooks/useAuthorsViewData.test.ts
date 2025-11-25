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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAuthorsViewData } from "./useAuthorsViewData";

vi.mock("./useAuthors", () => ({
  useAuthors: vi.fn(),
}));

import { useAuthors } from "./useAuthors";

describe("useAuthorsViewData", () => {
  const mockUseAuthorsResult = {
    authors: [],
    total: 0,
    isLoading: false,
    error: null,
    loadMore: vi.fn(),
    hasMore: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuthors).mockReturnValue(mockUseAuthorsResult);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should use default pageSize of 20", () => {
    renderHook(() => useAuthorsViewData());

    expect(useAuthors).toHaveBeenCalledWith({
      infiniteScroll: true,
      pageSize: 20,
      filter: undefined,
    });
  });

  it("should use custom pageSize", () => {
    renderHook(() => useAuthorsViewData({ pageSize: 50 }));

    expect(useAuthors).toHaveBeenCalledWith({
      infiniteScroll: true,
      pageSize: 50,
      filter: undefined,
    });
  });

  it("should use 'all' filterType", () => {
    renderHook(() => useAuthorsViewData({ filterType: "all" }));

    expect(useAuthors).toHaveBeenCalledWith({
      infiniteScroll: true,
      pageSize: 20,
      filter: undefined,
    });
  });

  it("should use 'unmatched' filterType", () => {
    renderHook(() => useAuthorsViewData({ filterType: "unmatched" }));

    expect(useAuthors).toHaveBeenCalledWith({
      infiniteScroll: true,
      pageSize: 20,
      filter: "unmatched",
    });
  });

  it("should return all values from useAuthors", () => {
    const { result } = renderHook(() => useAuthorsViewData());

    expect(result.current).toEqual({
      authors: [],
      total: 0,
      isLoading: false,
      error: null,
      loadMore: mockUseAuthorsResult.loadMore,
      hasMore: false,
    });
  });

  it("should pass through authors data", () => {
    const mockAuthors = [
      { key: "1", name: "Author 1" },
      { key: "2", name: "Author 2" },
    ] as unknown as typeof mockUseAuthorsResult.authors;
    vi.mocked(useAuthors).mockReturnValue({
      ...mockUseAuthorsResult,
      authors: mockAuthors,
    });

    const { result } = renderHook(() => useAuthorsViewData());

    expect(result.current.authors).toEqual(mockAuthors);
  });

  it("should pass through loading state", () => {
    vi.mocked(useAuthors).mockReturnValue({
      ...mockUseAuthorsResult,
      isLoading: true,
    });

    const { result } = renderHook(() => useAuthorsViewData());

    expect(result.current.isLoading).toBe(true);
  });

  it("should pass through error", () => {
    vi.mocked(useAuthors).mockReturnValue({
      ...mockUseAuthorsResult,
      error: "Test error",
    });

    const { result } = renderHook(() => useAuthorsViewData());

    expect(result.current.error).toBe("Test error");
  });
});
