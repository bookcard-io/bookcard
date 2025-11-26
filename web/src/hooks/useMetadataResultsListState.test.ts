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
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useMetadataResultsListState } from "./useMetadataResultsListState";

describe("useMetadataResultsListState", () => {
  beforeEach(() => {
    // No setup needed
  });

  afterEach(() => {
    // No cleanup needed
  });

  it("should initialize with no expanded key and empty collapsedKeys", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    expect(result.current.expandedKey).toBe(null);
    expect(result.current.collapsedKeys.size).toBe(0);
    expect(result.current.isExpanded("key1")).toBe(false);
    expect(result.current.isDimmed("key1")).toBe(false);
  });

  it("should expand an item when handleExpand is called", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.expandedKey).toBe("key1");
    expect(result.current.isExpanded("key1")).toBe(true);
    expect(result.current.isExpanded("key2")).toBe(false);
  });

  it("should collapse an item when handleExpand is called on the same key", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.expandedKey).toBe("key1");

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.expandedKey).toBe(null);
    expect(result.current.isExpanded("key1")).toBe(false);
  });

  it("should add item to collapsedKeys when collapsing", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.collapsedKeys.has("key1")).toBe(false);

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.collapsedKeys.has("key1")).toBe(true);
    expect(result.current.isDimmed("key1")).toBe(true);
  });

  it("should remove item from collapsedKeys when expanding", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    // Expand and collapse key1
    act(() => {
      result.current.handleExpand("key1");
    });

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.collapsedKeys.has("key1")).toBe(true);
    expect(result.current.isDimmed("key1")).toBe(true);

    // Expand key1 again
    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.expandedKey).toBe("key1");
    expect(result.current.collapsedKeys.has("key1")).toBe(false);
    expect(result.current.isDimmed("key1")).toBe(false);
  });

  it("should switch expanded item when handleExpand is called with different key", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.expandedKey).toBe("key1");

    act(() => {
      result.current.handleExpand("key2");
    });

    expect(result.current.expandedKey).toBe("key2");
    expect(result.current.isExpanded("key1")).toBe(false);
    expect(result.current.isExpanded("key2")).toBe(true);
  });

  it("should remove previous key from collapsedKeys when switching to different key", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    // Expand and collapse key1
    act(() => {
      result.current.handleExpand("key1");
    });

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.collapsedKeys.has("key1")).toBe(true);

    // Expand key2 (different key)
    act(() => {
      result.current.handleExpand("key2");
    });

    // key1 should still be in collapsedKeys
    expect(result.current.collapsedKeys.has("key1")).toBe(true);
    expect(result.current.isDimmed("key1")).toBe(true);

    // key2 should not be in collapsedKeys
    expect(result.current.collapsedKeys.has("key2")).toBe(false);
    expect(result.current.isDimmed("key2")).toBe(false);
  });

  it("should correctly identify expanded item", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.isExpanded("key1")).toBe(true);
    expect(result.current.isExpanded("key2")).toBe(false);
    expect(result.current.isExpanded("key3")).toBe(false);
  });

  it("should correctly identify dimmed items", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    // Expand and collapse key1
    act(() => {
      result.current.handleExpand("key1");
    });

    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.isDimmed("key1")).toBe(true);
    expect(result.current.isDimmed("key2")).toBe(false);

    // Expand and collapse key2
    act(() => {
      result.current.handleExpand("key2");
    });

    act(() => {
      result.current.handleExpand("key2");
    });

    expect(result.current.isDimmed("key1")).toBe(true);
    expect(result.current.isDimmed("key2")).toBe(true);
  });

  it("should handle multiple expand/collapse cycles", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    // First cycle
    act(() => {
      result.current.handleExpand("key1");
    });
    expect(result.current.expandedKey).toBe("key1");

    act(() => {
      result.current.handleExpand("key1");
    });
    expect(result.current.expandedKey).toBe(null);
    expect(result.current.collapsedKeys.has("key1")).toBe(true);

    // Second cycle
    act(() => {
      result.current.handleExpand("key1");
    });
    expect(result.current.expandedKey).toBe("key1");
    expect(result.current.collapsedKeys.has("key1")).toBe(false);

    act(() => {
      result.current.handleExpand("key1");
    });
    expect(result.current.expandedKey).toBe(null);
    expect(result.current.collapsedKeys.has("key1")).toBe(true);
  });

  it("should maintain collapsedKeys across multiple items", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    // Collapse key1
    act(() => {
      result.current.handleExpand("key1");
    });
    act(() => {
      result.current.handleExpand("key1");
    });

    // Collapse key2
    act(() => {
      result.current.handleExpand("key2");
    });
    act(() => {
      result.current.handleExpand("key2");
    });

    // Collapse key3
    act(() => {
      result.current.handleExpand("key3");
    });
    act(() => {
      result.current.handleExpand("key3");
    });

    expect(result.current.collapsedKeys.has("key1")).toBe(true);
    expect(result.current.collapsedKeys.has("key2")).toBe(true);
    expect(result.current.collapsedKeys.has("key3")).toBe(true);
    expect(result.current.isDimmed("key1")).toBe(true);
    expect(result.current.isDimmed("key2")).toBe(true);
    expect(result.current.isDimmed("key3")).toBe(true);
  });

  it("should handle expanding item that was previously collapsed and then another item", () => {
    const { result } = renderHook(() => useMetadataResultsListState());

    // Collapse key1
    act(() => {
      result.current.handleExpand("key1");
    });
    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.collapsedKeys.has("key1")).toBe(true);

    // Expand key1 again (should remove from collapsedKeys)
    act(() => {
      result.current.handleExpand("key1");
    });

    expect(result.current.expandedKey).toBe("key1");
    expect(result.current.collapsedKeys.has("key1")).toBe(false);

    // Switch to key2
    act(() => {
      result.current.handleExpand("key2");
    });

    expect(result.current.expandedKey).toBe("key2");
    expect(result.current.collapsedKeys.has("key1")).toBe(false);
    expect(result.current.collapsedKeys.has("key2")).toBe(false);
  });
});
