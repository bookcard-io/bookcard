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
import { useLibraryViewMode } from "./useLibraryViewMode";

describe("useLibraryViewMode", () => {
  it("should initialize with grid view mode", () => {
    const { result } = renderHook(() => useLibraryViewMode());
    expect(result.current.viewMode).toBe("grid");
  });

  it("should change view mode", () => {
    const { result } = renderHook(() => useLibraryViewMode());
    act(() => {
      result.current.handleViewModeChange("list");
    });
    expect(result.current.viewMode).toBe("list");
  });

  it("should call onSortToggle when mode is sort", () => {
    const onSortToggle = vi.fn();
    const { result } = renderHook(() => useLibraryViewMode({ onSortToggle }));
    act(() => {
      result.current.handleViewModeChange("sort");
    });
    expect(onSortToggle).toHaveBeenCalledTimes(1);
    expect(result.current.viewMode).toBe("grid"); // Should not change
  });

  it("should not call onSortToggle for other modes", () => {
    const onSortToggle = vi.fn();
    const { result } = renderHook(() => useLibraryViewMode({ onSortToggle }));
    act(() => {
      result.current.handleViewModeChange("list");
    });
    expect(onSortToggle).not.toHaveBeenCalled();
    expect(result.current.viewMode).toBe("list");
  });

  it("should handle multiple view mode changes", () => {
    const { result } = renderHook(() => useLibraryViewMode());
    act(() => {
      result.current.handleViewModeChange("list");
    });
    expect(result.current.viewMode).toBe("list");

    act(() => {
      result.current.handleViewModeChange("grid");
    });
    expect(result.current.viewMode).toBe("grid");
  });
});
