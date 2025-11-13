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
import { useMultiSelect } from "./useMultiSelect";

describe("useMultiSelect", () => {
  it("should initialize with empty selection when no initialSelected", () => {
    const { result } = renderHook(() => useMultiSelect());
    expect(result.current.selected).toEqual([]);
  });

  it("should initialize with initialSelected items", () => {
    const initialSelected = [1, 2, 3];
    const { result } = renderHook(() => useMultiSelect({ initialSelected }));
    expect(result.current.selected).toEqual(initialSelected);
  });

  it("should return false for isSelected when item is not selected", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1, 2] }),
    );
    expect(result.current.isSelected(3)).toBe(false);
  });

  it("should return true for isSelected when item is selected", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1, 2] }),
    );
    expect(result.current.isSelected(1)).toBe(true);
    expect(result.current.isSelected(2)).toBe(true);
  });

  it("should toggle item selection", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1] }),
    );

    act(() => {
      result.current.toggle(2);
    });
    expect(result.current.selected).toEqual([1, 2]);

    act(() => {
      result.current.toggle(1);
    });
    expect(result.current.selected).toEqual([2]);
  });

  it("should select item when not already selected", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1] }),
    );

    act(() => {
      result.current.select(2);
    });
    expect(result.current.selected).toEqual([1, 2]);
  });

  it("should not duplicate item when selecting already selected item", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1] }),
    );

    act(() => {
      result.current.select(1);
    });
    expect(result.current.selected).toEqual([1]);
  });

  it("should deselect item", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1, 2, 3] }),
    );

    act(() => {
      result.current.deselect(2);
    });
    expect(result.current.selected).toEqual([1, 3]);
  });

  it("should not change selection when deselecting non-selected item", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1, 2] }),
    );

    act(() => {
      result.current.deselect(3);
    });
    expect(result.current.selected).toEqual([1, 2]);
  });

  it("should clear all selections", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1, 2, 3] }),
    );

    act(() => {
      result.current.clear();
    });
    expect(result.current.selected).toEqual([]);
  });

  it("should set selected items", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [1] }),
    );

    act(() => {
      result.current.setSelected([2, 3, 4]);
    });
    expect(result.current.selected).toEqual([2, 3, 4]);
  });

  it("should call onSelectionChange when selection changes", () => {
    const onSelectionChange = vi.fn();
    const { result } = renderHook(() => useMultiSelect({ onSelectionChange }));

    act(() => {
      result.current.toggle(1);
    });
    expect(onSelectionChange).toHaveBeenCalledWith([1]);

    act(() => {
      result.current.select(2);
    });
    expect(onSelectionChange).toHaveBeenCalledWith([1, 2]);

    act(() => {
      result.current.deselect(1);
    });
    expect(onSelectionChange).toHaveBeenCalledWith([2]);

    act(() => {
      result.current.clear();
    });
    expect(onSelectionChange).toHaveBeenCalledWith([]);

    act(() => {
      result.current.setSelected([3, 4]);
    });
    expect(onSelectionChange).toHaveBeenCalledWith([3, 4]);
  });

  it("should work with string items", () => {
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: ["a", "b"] }),
    );

    expect(result.current.isSelected("a")).toBe(true);
    expect(result.current.isSelected("c")).toBe(false);

    act(() => {
      result.current.toggle("c");
    });
    expect(result.current.selected).toEqual(["a", "b", "c"]);
  });

  it("should work with object items", () => {
    const item1 = { id: 1, name: "Item 1" };
    const item2 = { id: 2, name: "Item 2" };
    const { result } = renderHook(() =>
      useMultiSelect({ initialSelected: [item1] }),
    );

    expect(result.current.isSelected(item1)).toBe(true);
    expect(result.current.isSelected(item2)).toBe(false);

    act(() => {
      result.current.select(item2);
    });
    expect(result.current.selected).toEqual([item1, item2]);
  });
});
