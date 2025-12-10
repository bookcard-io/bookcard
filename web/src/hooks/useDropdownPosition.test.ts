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
    const menuRef = { current: null };
    const { result } = renderHook(() =>
      useDropdownPosition({
        isOpen: true,
        buttonRef: nullButtonRef,
        cursorPosition,
        menuRef,
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

  describe("Vertical Flipping", () => {
    it.each([
      { hasButton: true, desc: "with button ref" },
      { hasButton: false, desc: "with cursor fallback" },
    ])(
      "should auto-flip up when menu would overflow bottom $desc",
      async ({ hasButton }) => {
        const cursorPosition = { x: 250, y: hasButton ? 125 : 400 };
        const menuRef = { current: document.createElement("div") };
        const menuElement = menuRef.current as HTMLElement;
        // Large height that would overflow
        menuElement.getBoundingClientRect = vi.fn(() => ({
          top: 0,
          left: 0,
          right: 100,
          bottom: 1000,
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

        const buttonRefToUse = hasButton ? buttonRef : { current: null };

        const { result } = renderHook(() =>
          useDropdownPosition({
            isOpen: true,
            buttonRef: buttonRefToUse,
            cursorPosition,
            menuRef,
          }),
        );

        await waitFor(() => {
          // Should flip up
          expect(result.current.position.top).toBe(0);
        });
      },
    );

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
        // Should not flip
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
        expect(result.current.position.top).toBe(127);
      });
    });
  });

  describe("Horizontal Alignment & Auto-Flip", () => {
    // Shared setup for horizontal tests
    const setupHorizontalTest = (
      hasButton: boolean,
      horizontalAlign: "left" | "right",
      autoFlipHorizontal: boolean,
      alignLeftEdge: boolean,
      menuWidth: number,
      windowWidth: number,
      cursorX: number,
    ) => {
      const menuRef = { current: document.createElement("div") };
      const menuElement = menuRef.current as HTMLElement;
      menuElement.getBoundingClientRect = vi.fn(() => ({
        top: 0,
        left: 0,
        right: menuWidth,
        bottom: 100,
        width: menuWidth,
        height: 100,
        x: 0,
        y: 0,
        toJSON: vi.fn(),
      }));

      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: windowWidth,
      });

      const buttonRefToUse = hasButton ? buttonRef : { current: null };
      const cursorPosition = { x: cursorX, y: 100 };

      return renderHook(() =>
        useDropdownPosition({
          isOpen: true,
          buttonRef: buttonRefToUse,
          cursorPosition,
          menuRef,
          horizontalAlign,
          autoFlipHorizontal,
          alignLeftEdge,
        }),
      );
    };

    const scenarios = [
      // 1. Basic Right Align (no flip)
      {
        desc: "Basic right align, no overflow",
        hasButton: true,
        horizontalAlign: "right" as const,
        autoFlipHorizontal: true,
        alignLeftEdge: false,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 250, // menuX = 250
        expectedKey: "right",
      },
      {
        desc: "Basic right align, no overflow (fallback)",
        hasButton: false,
        horizontalAlign: "right" as const,
        autoFlipHorizontal: true,
        alignLeftEdge: false,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 250,
        expectedKey: "right",
      },
      // 2. Basic Left Align (no flip)
      {
        desc: "Basic left align, no overflow",
        hasButton: true,
        horizontalAlign: "left" as const,
        autoFlipHorizontal: true,
        alignLeftEdge: false,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 250, // menuX = 250
        expectedKey: "left",
      },
      {
        desc: "Basic left align, no overflow (fallback)",
        hasButton: false,
        horizontalAlign: "left" as const,
        autoFlipHorizontal: true,
        alignLeftEdge: false,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 250,
        expectedKey: "left",
      },
      // 3. Right Align -> Overflow Left -> Flip to Left
      // menuX = 50. Right align implies extending left.
      // If menuX < width (100), it overflows left.
      {
        desc: "Right align overflows left edge -> flip to left (with button)",
        hasButton: true,
        horizontalAlign: "right" as const,
        autoFlipHorizontal: true,
        alignLeftEdge: false,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 50, // Button rect left is 200. We need menuX to be 50.
        // Wait, menuX = buttonRect.left + (cursorX - buttonRect.left) = cursorX.
        // But in test setup, buttonRect.left is 200.
        // To get menuX = 50, we need cursorX=50.
        // 50 - 100 = -50 < 0. Flip to left.
        expectedKey: "left",
      },
      {
        desc: "Right align overflows left edge -> flip to left (fallback)",
        hasButton: false,
        horizontalAlign: "right" as const,
        autoFlipHorizontal: true,
        alignLeftEdge: false,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 50,
        expectedKey: "left",
      },
      // 4. Left Align -> Overflow Right -> Flip to Right
      // menuX = 950. Width = 100. windowWidth = 1000.
      // 950 + 100 = 1050 > 1000. Flip to right.
      {
        desc: "Left align overflows right edge -> flip to right (with button)",
        hasButton: true,
        horizontalAlign: "left" as const,
        autoFlipHorizontal: true,
        alignLeftEdge: false,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 950,
        expectedKey: "right",
      },
      {
        desc: "Left align overflows right edge -> flip to right (fallback)",
        hasButton: false,
        horizontalAlign: "left" as const,
        autoFlipHorizontal: true,
        alignLeftEdge: false,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 950,
        expectedKey: "right",
      },
      // 5. Align Left Edge Force
      {
        desc: "Align left edge forces left and adds offset (with button)",
        hasButton: true,
        horizontalAlign: "right" as const, // Should be ignored
        autoFlipHorizontal: false,
        alignLeftEdge: true,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 250,
        expectedKey: "left",
        expectOffset: true,
      },
      {
        desc: "Align left edge forces left and adds offset (fallback)",
        hasButton: false,
        horizontalAlign: "right" as const, // Should be ignored
        autoFlipHorizontal: false,
        alignLeftEdge: true,
        menuWidth: 100,
        windowWidth: 1000,
        cursorX: 250,
        expectedKey: "left",
        expectOffset: true,
      },
    ];

    it.each(scenarios)(
      "$desc",
      async ({
        hasButton,
        horizontalAlign,
        autoFlipHorizontal,
        alignLeftEdge,
        menuWidth,
        windowWidth,
        cursorX,
        expectedKey,
        expectOffset,
      }) => {
        // For 'with button', buttonRect.left is 200.
        // We want menuX to be cursorX.
        // In implementation: menuX = buttonRect.left + (cursorPos.x - buttonRect.left) = cursorPos.x
        // So passing cursorX is sufficient.

        const { result } = setupHorizontalTest(
          hasButton,
          horizontalAlign,
          autoFlipHorizontal,
          alignLeftEdge,
          menuWidth,
          windowWidth,
          cursorX,
        );

        await waitFor(() => {
          if (expectedKey === "left") {
            expect(result.current.position.left).toBeDefined();
            expect(result.current.position.right).toBeUndefined();
            expect(result.current.position.left).toBe(cursorX);
          } else {
            expect(result.current.position.right).toBeDefined();
            expect(result.current.position.left).toBeUndefined();
            // right = windowWidth - menuX - MENU_OFFSET_X (-2)
            expect(result.current.position.right).toBe(
              windowWidth - cursorX - -2,
            );
          }

          if (expectOffset) {
            // 100 (cursorY) + 2 (MENU_OFFSET_Y) + 8 (extra offset) = 110
            // But careful, buttonRef case might have different Y calculation if button moved?
            // No, buttonRect.top=100 in mock, cursorY=100.
            // implementation: menuY = buttonRect.top + (cursorPos.y - buttonRect.top) = cursorPos.y = 100.
            // top = 100 + 2 + 8 = 110.
            expect(result.current.position.top).toBe(110);
          } else {
            // 100 + 2 = 102
            expect(result.current.position.top).toBe(102);
          }
        });
      },
    );
  });
});
