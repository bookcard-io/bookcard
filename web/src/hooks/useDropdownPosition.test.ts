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

import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDropdownPosition } from "./useDropdownPosition";

describe("useDropdownPosition", () => {
  let buttonRef: React.RefObject<HTMLDivElement>;
  let buttonElement: HTMLDivElement;

  beforeEach(() => {
    buttonElement = document.createElement("div");
    buttonRef = { current: buttonElement };
    // Mock getBoundingClientRect
    buttonElement.getBoundingClientRect = vi.fn(() => ({
      top: 100,
      left: 200,
      right: 300,
      bottom: 150,
      width: 100,
      height: 50,
      x: 200,
      y: 100,
      toJSON: vi.fn(),
    }));
    document.body.appendChild(buttonElement);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    document.body.removeChild(buttonElement);
  });

  it("should return default position when menu is closed", () => {
    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: false,
        buttonRef,
        cursorPosition: { x: 250, y: 125 },
      }),
    );

    expect(result.current.position).toEqual({ top: 0, right: 0 });
  });

  it("should return default position when cursor position is null", () => {
    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef,
        cursorPosition: null,
      }),
    );

    expect(result.current.position).toEqual({ top: 0, right: 0 });
  });

  it("should calculate position relative to button and cursor", () => {
    const cursorPosition = { x: 250, y: 125 };
    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef,
        cursorPosition,
      }),
    );

    // Expected: menuX = 200 + (250 - 200) = 250
    // Expected: menuY = 100 + (125 - 100) = 125
    // Expected: top = 125 + 2 = 127
    // Expected: right = window.innerWidth - 250 - (-2) = window.innerWidth - 248
    const expectedRight = window.innerWidth - 248;
    expect(result.current.position.top).toBe(127);
    expect(result.current.position.right).toBe(expectedRight);
  });

  it("should fallback to cursor position when button ref is null", () => {
    const nullButtonRef = { current: null };
    const cursorPosition = { x: 250, y: 125 };
    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef: nullButtonRef,
        cursorPosition,
      }),
    );

    // Expected: top = 125 + 2 = 127
    // Expected: right = window.innerWidth - 250 - (-2) = window.innerWidth - 248
    const expectedRight = window.innerWidth - 248;
    expect(result.current.position.top).toBe(127);
    expect(result.current.position.right).toBe(expectedRight);
  });

  it("should update position on scroll", async () => {
    const cursorPosition = { x: 250, y: 125 };
    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef,
        cursorPosition,
      }),
    );

    const initialPosition = { ...result.current.position };

    // Simulate scroll by updating button position
    buttonElement.getBoundingClientRect = vi.fn(() => ({
      top: 150,
      left: 200,
      right: 300,
      bottom: 200,
      width: 100,
      height: 50,
      x: 200,
      y: 150,
      toJSON: vi.fn(),
    }));

    // Trigger scroll event
    window.dispatchEvent(new Event("scroll"));

    await waitFor(() => {
      // Position should update: menuY = 150 + (125 - 100) = 175
      expect(result.current.position.top).toBe(177); // 175 + 2
    });

    expect(result.current.position.top).not.toBe(initialPosition.top);
  });

  it("should update position on resize", async () => {
    const cursorPosition = { x: 250, y: 125 };
    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef,
        cursorPosition,
      }),
    );

    const initialRight = result.current.position.right;

    // Simulate window resize
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 2000,
    });

    window.dispatchEvent(new Event("resize"));

    await waitFor(() => {
      // Right position should update based on new window width
      expect(result.current.position.right).not.toBe(initialRight);
    });
  });

  it("should maintain cursor offset when button moves", async () => {
    const cursorPosition = { x: 250, y: 125 };
    const { result, rerender } = renderHook(
      ({ isOpen }) =>
        useDropdownPosition({
          isOpen,
          buttonRef,
          cursorPosition,
        }),
      { initialProps: { isOpen: false } },
    );

    // Open menu
    rerender({ isOpen: true });
    await waitFor(() => {
      expect(result.current.position.top).not.toBe(0);
    });
    const initialTop = result.current.position.top;

    // Move button down
    buttonElement.getBoundingClientRect = vi.fn(() => ({
      top: 200,
      left: 200,
      right: 300,
      bottom: 250,
      width: 100,
      height: 50,
      x: 200,
      y: 200,
      toJSON: vi.fn(),
    }));

    window.dispatchEvent(new Event("scroll"));

    // Position should maintain the same offset from button
    // menuY = 200 + (125 - 100) = 225, top = 225 + 2 = 227
    await waitFor(() => {
      expect(result.current.position.top).toBe(227);
    });
    expect(result.current.position.top - initialTop).toBe(100); // Button moved 100px down
  });

  it("should auto-flip up when menu would overflow bottom with button ref", async () => {
    const cursorPosition = { x: 250, y: 125 };
    const menuRef = { current: document.createElement("div") };
    const menuElement = menuRef.current as HTMLElement;
    menuElement.getBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      right: 100,
      bottom: 1000, // Large height that would overflow
      width: 100,
      height: 1000,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));

    // Set window height to be smaller than menu would need
    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: 500,
    });

    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef,
        cursorPosition,
        menuRef,
      }),
    );

    await waitFor(() => {
      // Should flip up: top = max(0, buttonRect.bottom - measuredHeight)
      // buttonRect.bottom = 150, measuredHeight = 1000
      // top = max(0, 150 - 1000) = max(0, -850) = 0
      expect(result.current.position.top).toBe(0);
    });
  });

  it("should auto-flip up when menu would overflow bottom with cursor fallback", async () => {
    const nullButtonRef = { current: null };
    const cursorPosition = { x: 250, y: 400 };
    const menuRef = { current: document.createElement("div") };
    const menuElement = menuRef.current as HTMLElement;
    menuElement.getBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      right: 100,
      bottom: 500,
      width: 100,
      height: 500,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));

    // Set window height to be smaller than menu would need
    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: 600,
    });

    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef: nullButtonRef,
        cursorPosition,
        menuRef,
      }),
    );

    await waitFor(() => {
      // Should flip up: top = max(0, cursorPosition.y - measuredHeight)
      // cursorPosition.y = 400, measuredHeight = 500
      // downTop = 400 + 2 = 402, wouldOverflow = 402 + 500 > 600 = true
      // top = max(0, 400 - 500) = max(0, -100) = 0
      expect(result.current.position.top).toBe(0);
    });
  });

  it("should position down when menu would not overflow", async () => {
    const cursorPosition = { x: 250, y: 125 };
    const menuRef = { current: document.createElement("div") };
    const menuElement = menuRef.current as HTMLElement;
    menuElement.getBoundingClientRect = vi.fn(() => ({
      top: 0,
      left: 0,
      right: 100,
      bottom: 100,
      width: 100,
      height: 100,
      x: 0,
      y: 0,
      toJSON: vi.fn(),
    }));

    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: 1000,
    });

    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef,
        cursorPosition,
        menuRef,
      }),
    );

    await waitFor(() => {
      // Should not flip: downTop = 125 + 2 = 127, wouldOverflow = 127 + 100 > 1000 = false
      // top = 127
      expect(result.current.position.top).toBe(127);
    });
  });

  it("should handle menu ref being null", async () => {
    const cursorPosition = { x: 250, y: 125 };
    const nullMenuRef = { current: null };

    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef,
        cursorPosition,
        menuRef: nullMenuRef,
      }),
    );

    await waitFor(() => {
      // Should use measuredHeight = 0 when menuRef is null
      // downTop = 125 + 2 = 127, wouldOverflow = 127 + 0 > window.innerHeight = false
      expect(result.current.position.top).toBe(127);
    });
  });
});
