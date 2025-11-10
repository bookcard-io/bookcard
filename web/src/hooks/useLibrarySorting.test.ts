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
