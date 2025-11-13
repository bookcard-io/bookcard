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
import type { Shelf } from "@/types/shelf";
import { useShelfDataUpdates } from "./useShelfDataUpdates";

describe("useShelfDataUpdates", () => {
  it("should initialize with empty overrides map", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    expect(result.current.shelfDataOverrides.size).toBe(0);
  });

  it("should update shelf data", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    act(() => {
      result.current.updateShelf(1, { name: "Updated Name" });
    });

    expect(result.current.shelfDataOverrides.get(1)).toEqual({
      name: "Updated Name",
    });
  });

  it("should merge with existing override when updating", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    act(() => {
      result.current.updateShelf(1, { name: "Updated Name" });
    });

    act(() => {
      result.current.updateShelf(1, { description: "Updated Description" });
    });

    expect(result.current.shelfDataOverrides.get(1)).toEqual({
      name: "Updated Name",
      description: "Updated Description",
    });
  });

  it("should update multiple shelves independently", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    act(() => {
      result.current.updateShelf(1, { name: "Shelf 1" });
    });

    act(() => {
      result.current.updateShelf(2, { name: "Shelf 2" });
    });

    expect(result.current.shelfDataOverrides.get(1)).toEqual({
      name: "Shelf 1",
    });
    expect(result.current.shelfDataOverrides.get(2)).toEqual({
      name: "Shelf 2",
    });
  });

  it("should update cover with cache-busting timestamp", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    act(() => {
      result.current.updateShelf(1, { cover_picture: "existing.jpg" });
    });

    act(() => {
      result.current.updateCover(1);
    });

    const override = result.current.shelfDataOverrides.get(1);
    expect(typeof override?.cover_picture).toBe("string");
    expect(override?.cover_picture).toMatch(/^refresh-\d+$/);
  });

  it("should preserve existing cover when updating cover", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    act(() => {
      result.current.updateShelf(1, { cover_picture: "existing.jpg" });
    });

    act(() => {
      result.current.updateCover(1);
    });

    const override = result.current.shelfDataOverrides.get(1);
    expect(override?.cover_picture).toMatch(/^refresh-\d+$/);
  });

  it("should set cover to null when original was null", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    act(() => {
      result.current.updateShelf(1, { cover_picture: null });
    });

    act(() => {
      result.current.updateCover(1);
    });

    const override = result.current.shelfDataOverrides.get(1);
    expect(override?.cover_picture).toBeNull();
  });

  it("should set cover to null when original was undefined", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    act(() => {
      result.current.updateCover(1);
    });

    const override = result.current.shelfDataOverrides.get(1);
    expect(override?.cover_picture).toBeNull();
  });

  it("should clear all overrides", () => {
    const { result } = renderHook(() => useShelfDataUpdates());

    act(() => {
      result.current.updateShelf(1, { name: "Shelf 1" });
      result.current.updateShelf(2, { name: "Shelf 2" });
    });

    expect(result.current.shelfDataOverrides.size).toBe(2);

    act(() => {
      result.current.clearOverrides();
    });

    expect(result.current.shelfDataOverrides.size).toBe(0);
  });

  it("should expose updateShelf and updateCover via ref", () => {
    const updateRef = { current: null } as unknown as React.RefObject<{
      updateShelf: (shelfId: number, shelfData: Partial<Shelf>) => void;
      updateCover: (shelfId: number) => void;
    }>;

    renderHook(() => useShelfDataUpdates({ updateRef }));

    expect(updateRef.current).not.toBeNull();
    expect(updateRef.current?.updateShelf).toBeDefined();
    expect(updateRef.current?.updateCover).toBeDefined();
  });

  it("should call updateShelf via ref", () => {
    const updateRef = { current: null } as unknown as React.RefObject<{
      updateShelf: (shelfId: number, shelfData: Partial<Shelf>) => void;
      updateCover: (shelfId: number) => void;
    }>;

    const { result } = renderHook(() => useShelfDataUpdates({ updateRef }));

    act(() => {
      updateRef.current?.updateShelf(1, { name: "Updated" });
    });

    expect(result.current.shelfDataOverrides.get(1)).toEqual({
      name: "Updated",
    });
  });

  it("should call updateCover via ref", () => {
    const updateRef = { current: null } as unknown as React.RefObject<{
      updateShelf: (shelfId: number, shelfData: Partial<Shelf>) => void;
      updateCover: (shelfId: number) => void;
    }>;

    const { result } = renderHook(() => useShelfDataUpdates({ updateRef }));

    act(() => {
      result.current.updateShelf(1, { cover_picture: "existing.jpg" });
    });

    act(() => {
      updateRef.current?.updateCover(1);
    });

    const override = result.current.shelfDataOverrides.get(1);
    expect(typeof override?.cover_picture).toBe("string");
    expect(override?.cover_picture).toMatch(/^refresh-\d+$/);
  });
});
