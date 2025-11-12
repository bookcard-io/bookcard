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
import { useLibrarySorting } from "./useLibrarySorting";

describe("useLibrarySorting", () => {
  it("should initialize with default sort values", () => {
    const { result } = renderHook(() => useLibrarySorting());
    expect(result.current.sortBy).toBe("timestamp");
    expect(result.current.sortOrder).toBe("desc");
    expect(result.current.showSortPanel).toBe(false);
  });

  it("should toggle sort panel", () => {
    const { result } = renderHook(() => useLibrarySorting());
    act(() => {
      result.current.handleSortByClick();
    });
    expect(result.current.showSortPanel).toBe(true);

    act(() => {
      result.current.handleSortByClick();
    });
    expect(result.current.showSortPanel).toBe(false);
  });

  it("should change sort field", () => {
    const { result } = renderHook(() => useLibrarySorting());
    act(() => {
      result.current.handleSortByChange("title");
    });
    expect(result.current.sortBy).toBe("title");
    expect(result.current.showSortPanel).toBe(false);
  });

  it("should toggle sort order", () => {
    const { result } = renderHook(() => useLibrarySorting());
    expect(result.current.sortOrder).toBe("desc");

    act(() => {
      result.current.handleSortToggle();
    });
    expect(result.current.sortOrder).toBe("asc");

    act(() => {
      result.current.handleSortToggle();
    });
    expect(result.current.sortOrder).toBe("desc");
  });

  it("should close sort panel programmatically", () => {
    const { result } = renderHook(() => useLibrarySorting());
    act(() => {
      result.current.handleSortByClick();
    });
    expect(result.current.showSortPanel).toBe(true);

    act(() => {
      result.current.closeSortPanel();
    });
    expect(result.current.showSortPanel).toBe(false);
  });

  it("should call onSortPanelChange when panel visibility changes", () => {
    const onSortPanelChange = vi.fn();
    const { result } = renderHook(() =>
      useLibrarySorting({ onSortPanelChange }),
    );

    act(() => {
      result.current.handleSortByClick();
    });
    expect(onSortPanelChange).toHaveBeenCalledWith(true);

    act(() => {
      result.current.handleSortByClick();
    });
    expect(onSortPanelChange).toHaveBeenCalledWith(false);
  });

  it("should call onSortPanelChange when closing via closeSortPanel", () => {
    const onSortPanelChange = vi.fn();
    const { result } = renderHook(() =>
      useLibrarySorting({ onSortPanelChange }),
    );

    act(() => {
      result.current.handleSortByClick();
    });
    act(() => {
      result.current.closeSortPanel();
    });
    expect(onSortPanelChange).toHaveBeenCalledWith(false);
  });
});
