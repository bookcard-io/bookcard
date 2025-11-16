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
import { useDeleteConfirmationState } from "./useDeleteConfirmationState";

describe("useDeleteConfirmationState", () => {
  it("should initialize with closed state and no item", () => {
    const { result } = renderHook(() =>
      useDeleteConfirmationState<{ id: number; name: string }>(),
    );

    expect(result.current.isOpen).toBe(false);
    expect(result.current.itemToDelete).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isDeleting).toBe(false);
  });

  it("should open delete confirmation and set item when openDelete is called", () => {
    const { result } = renderHook(() =>
      useDeleteConfirmationState<{ id: number; name: string }>(),
    );
    const testItem = { id: 1, name: "Test Item" };

    act(() => {
      result.current.openDelete(testItem);
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.itemToDelete).toEqual(testItem);
    expect(result.current.error).toBeNull();
  });

  it("should clear error when opening delete confirmation", () => {
    const { result } = renderHook(() =>
      useDeleteConfirmationState<{ id: number; name: string }>(),
    );
    const testItem = { id: 1, name: "Test Item" };

    act(() => {
      result.current.setError("Previous error");
    });

    expect(result.current.error).toBe("Previous error");

    act(() => {
      result.current.openDelete(testItem);
    });

    expect(result.current.error).toBeNull();
  });

  it("should close and clear state when close is called", () => {
    const { result } = renderHook(() =>
      useDeleteConfirmationState<{ id: number; name: string }>(),
    );
    const testItem = { id: 1, name: "Test Item" };

    act(() => {
      result.current.openDelete(testItem);
      result.current.setError("Some error");
      result.current.setIsDeleting(true);
    });

    expect(result.current.isOpen).toBe(true);
    expect(result.current.itemToDelete).toEqual(testItem);
    expect(result.current.error).toBe("Some error");
    expect(result.current.isDeleting).toBe(true);

    act(() => {
      result.current.close();
    });

    expect(result.current.isOpen).toBe(false);
    expect(result.current.itemToDelete).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("should set error when setError is called", () => {
    const { result } = renderHook(() =>
      useDeleteConfirmationState<{ id: number; name: string }>(),
    );

    act(() => {
      result.current.setError("Delete failed");
    });

    expect(result.current.error).toBe("Delete failed");
  });

  it("should clear error when setError is called with null", () => {
    const { result } = renderHook(() =>
      useDeleteConfirmationState<{ id: number; name: string }>(),
    );

    act(() => {
      result.current.setError("Delete failed");
    });

    expect(result.current.error).toBe("Delete failed");

    act(() => {
      result.current.setError(null);
    });

    expect(result.current.error).toBeNull();
  });

  it("should set isDeleting when setIsDeleting is called", () => {
    const { result } = renderHook(() =>
      useDeleteConfirmationState<{ id: number; name: string }>(),
    );

    act(() => {
      result.current.setIsDeleting(true);
    });

    expect(result.current.isDeleting).toBe(true);

    act(() => {
      result.current.setIsDeleting(false);
    });

    expect(result.current.isDeleting).toBe(false);
  });
});
