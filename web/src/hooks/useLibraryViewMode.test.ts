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
