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
import { useBookCardMenu } from "./useBookCardMenu";

describe("useBookCardMenu", () => {
  it("should initialize with closed menu state", () => {
    const { result } = renderHook(() => useBookCardMenu());

    expect(result.current.isMenuOpen).toBe(false);
    expect(result.current.cursorPosition).toBeNull();
    expect(result.current.menuButtonRef).toBeDefined();
    expect(result.current.menuButtonRef.current).toBeNull();
  });

  it("should open menu and capture cursor position when toggling from closed state", () => {
    const { result } = renderHook(() => useBookCardMenu());

    const mockEvent = {
      stopPropagation: vi.fn(),
      clientX: 100,
      clientY: 200,
    } as unknown as React.MouseEvent<HTMLDivElement>;

    act(() => {
      result.current.handleMenuToggle(mockEvent);
    });

    expect(result.current.isMenuOpen).toBe(true);
    expect(result.current.cursorPosition).toEqual({ x: 100, y: 200 });
    expect(mockEvent.stopPropagation).toHaveBeenCalledTimes(1);
  });

  it("should close menu and clear cursor position when toggling from open state", () => {
    const { result } = renderHook(() => useBookCardMenu());

    const mockEvent = {
      stopPropagation: vi.fn(),
      clientX: 100,
      clientY: 200,
    } as unknown as React.MouseEvent<HTMLDivElement>;

    // Open menu first
    act(() => {
      result.current.handleMenuToggle(mockEvent);
    });

    expect(result.current.isMenuOpen).toBe(true);
    expect(result.current.cursorPosition).toEqual({ x: 100, y: 200 });

    // Close menu by toggling again
    act(() => {
      result.current.handleMenuToggle(mockEvent);
    });

    expect(result.current.isMenuOpen).toBe(false);
    expect(result.current.cursorPosition).toBeNull();
  });

  it("should close menu and clear cursor position when handleMenuClose is called", () => {
    const { result } = renderHook(() => useBookCardMenu());

    const mockEvent = {
      stopPropagation: vi.fn(),
      clientX: 100,
      clientY: 200,
    } as unknown as React.MouseEvent<HTMLDivElement>;

    // Open menu first
    act(() => {
      result.current.handleMenuToggle(mockEvent);
    });

    expect(result.current.isMenuOpen).toBe(true);
    expect(result.current.cursorPosition).toEqual({ x: 100, y: 200 });

    // Close menu using handleMenuClose
    act(() => {
      result.current.handleMenuClose();
    });

    expect(result.current.isMenuOpen).toBe(false);
    expect(result.current.cursorPosition).toBeNull();
  });

  it("should call stopPropagation on event when handleMenuToggle is called", () => {
    const { result } = renderHook(() => useBookCardMenu());

    const mockEvent = {
      stopPropagation: vi.fn(),
      clientX: 50,
      clientY: 75,
    } as unknown as React.MouseEvent<HTMLDivElement>;

    act(() => {
      result.current.handleMenuToggle(mockEvent);
    });

    expect(mockEvent.stopPropagation).toHaveBeenCalledTimes(1);
  });
});
