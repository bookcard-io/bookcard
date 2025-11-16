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
import { describe, expect, it } from "vitest";
import { useModalState } from "./useModalState";

describe("useModalState", () => {
  it("should initialize with closed state and no selected item", () => {
    const { result } = renderHook(() =>
      useModalState<{ id: number; name: string }>(),
    );

    expect(result.current.isOpen).toBe(false);
    expect(result.current.selectedItem).toBeNull();
  });

  it("should open modal for create mode when openCreate is called", () => {
    const { result } = renderHook(() =>
      useModalState<{ id: number; name: string }>(),
    );

    act(() => {
      result.current.openCreate();
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.selectedItem).toBeNull();
  });

  it("should open modal for edit mode when openEdit is called", () => {
    const { result } = renderHook(() =>
      useModalState<{ id: number; name: string }>(),
    );
    const testItem = { id: 1, name: "Test Item" };

    act(() => {
      result.current.openEdit(testItem);
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.selectedItem).toEqual(testItem);
  });

  it("should close modal and clear selected item when close is called", () => {
    const { result } = renderHook(() =>
      useModalState<{ id: number; name: string }>(),
    );
    const testItem = { id: 1, name: "Test Item" };

    act(() => {
      result.current.openEdit(testItem);
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.selectedItem).toEqual(testItem);

    act(() => {
      result.current.close();
    });

    expect(result.current.isOpen).toBe(false);
    expect(result.current.selectedItem).toBeNull();
  });

  it("should handle switching from create to edit mode", () => {
    const { result } = renderHook(() =>
      useModalState<{ id: number; name: string }>(),
    );
    const testItem = { id: 1, name: "Test Item" };

    act(() => {
      result.current.openCreate();
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.selectedItem).toBeNull();

    act(() => {
      result.current.openEdit(testItem);
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.selectedItem).toEqual(testItem);
  });

  it("should handle switching from edit to create mode", () => {
    const { result } = renderHook(() =>
      useModalState<{ id: number; name: string }>(),
    );
    const testItem = { id: 1, name: "Test Item" };

    act(() => {
      result.current.openEdit(testItem);
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.selectedItem).toEqual(testItem);

    act(() => {
      result.current.openCreate();
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.selectedItem).toBeNull();
  });
});
