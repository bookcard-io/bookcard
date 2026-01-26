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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  type UseCursorAutoHideOptions,
  useCursorAutoHide,
} from "./useCursorAutoHide";

describe("useCursorAutoHide", () => {
  let mockTime: number;

  beforeEach(() => {
    vi.useFakeTimers({
      // In the browser (Chromium) runner, explicitly fake Date so Date.now()
      // advances together with timer advancement.
      toFake: [
        "Date",
        "setTimeout",
        "clearTimeout",
        "setInterval",
        "clearInterval",
      ],
    });
    // Set a fixed start time for Date.now() mocking before any hooks are called
    mockTime = 1000000000000;
    vi.setSystemTime(mockTime);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  // Helper to advance time and run pending timers in browser environment
  const advanceTime = (ms: number) => {
    vi.advanceTimersByTime(ms);
  };

  describe("default behavior", () => {
    it("should start with cursor visible", () => {
      const { result } = renderHook(() => useCursorAutoHide());
      expect(result.current.cursorVisible).toBe(true);
      expect(result.current.cursorClassName).toBe("");
    });

    it("should hide cursor after default idle timeout (2000ms)", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      expect(result.current.cursorVisible).toBe(true);

      act(() => {
        // Hiding occurs on the first interval check at/after the timeout.
        // With default checkInterval=300ms, the first check >= 2000ms is at 2100ms.
        advanceTime(2100);
      });

      expect(result.current.cursorVisible).toBe(false);
      expect(result.current.cursorClassName).toBe("cursor-none");
    });

    it("should check at default interval (300ms)", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      // Should still be visible well before timeout (using 1500ms which is clearly < 2000ms)
      act(() => {
        advanceTime(1500);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Should hide after timeout
      act(() => {
        advanceTime(600); // Advance to well past 2000ms timeout
      });
      expect(result.current.cursorVisible).toBe(false);
    });
  });

  describe("activity detection", () => {
    it("should show cursor when activity is detected", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      // Hide cursor first
      act(() => {
        advanceTime(2100);
      });
      expect(result.current.cursorVisible).toBe(false);

      // Trigger activity
      act(() => {
        result.current.handleUserActivity();
      });
      expect(result.current.cursorVisible).toBe(true);
      expect(result.current.cursorClassName).toBe("");
    });

    it("should reset idle timer when activity is detected", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      // Advance time but not enough to hide
      act(() => {
        advanceTime(1500);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Trigger activity - should reset timer
      act(() => {
        result.current.handleUserActivity();
      });

      // Advance time again, but cursor should still be visible
      act(() => {
        advanceTime(1500);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Now advance past timeout from last activity
      act(() => {
        // Allow for interval quantization (default checkInterval=300ms).
        advanceTime(800);
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should handle multiple rapid activity events", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      // Hide cursor
      act(() => {
        advanceTime(2100);
      });
      expect(result.current.cursorVisible).toBe(false);

      // Rapid activity events
      act(() => {
        result.current.handleUserActivity();
        result.current.handleUserActivity();
        result.current.handleUserActivity();
      });
      expect(result.current.cursorVisible).toBe(true);

      // Should remain visible after rapid events
      act(() => {
        advanceTime(100);
      });
      expect(result.current.cursorVisible).toBe(true);
    });

    it("should not hide cursor if activity occurs before timeout", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      // Advance partway through timeout
      act(() => {
        advanceTime(1000);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Trigger activity
      act(() => {
        result.current.handleUserActivity();
      });

      // Advance more time, but not enough from last activity
      act(() => {
        advanceTime(1500);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Now advance past timeout from last activity
      act(() => {
        advanceTime(500);
      });
      expect(result.current.cursorVisible).toBe(false);
    });
  });

  describe("custom configuration", () => {
    it("should respect custom idleTimeout", () => {
      const { result } = renderHook(() =>
        useCursorAutoHide({ idleTimeout: 3000 }),
      );

      expect(result.current.cursorVisible).toBe(true);

      // Should still be visible well before custom timeout (using 2500ms which is < 3000ms)
      act(() => {
        advanceTime(2500);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Should hide after custom timeout
      act(() => {
        advanceTime(600); // Advance to well past 3000ms timeout
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should respect custom checkInterval", () => {
      const { result } = renderHook(() =>
        useCursorAutoHide({ idleTimeout: 1000, checkInterval: 100 }),
      );

      expect(result.current.cursorVisible).toBe(true);

      // Should still be visible well before timeout (using 800ms which is < 1000ms)
      act(() => {
        advanceTime(800);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Should hide after timeout (checkInterval should allow this)
      act(() => {
        advanceTime(300); // Advance to well past 1000ms timeout
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should work with very short idleTimeout", () => {
      const { result } = renderHook(() =>
        useCursorAutoHide({ idleTimeout: 100, checkInterval: 50 }),
      );

      expect(result.current.cursorVisible).toBe(true);

      act(() => {
        advanceTime(100);
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should work with very long idleTimeout", () => {
      const { result } = renderHook(() =>
        useCursorAutoHide({ idleTimeout: 10000 }),
      );

      expect(result.current.cursorVisible).toBe(true);

      // Should still be visible well before long timeout (using 9000ms which is < 10000ms)
      act(() => {
        advanceTime(9000);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Should hide after long timeout
      act(() => {
        advanceTime(1500); // Advance to well past 10000ms timeout
      });
      expect(result.current.cursorVisible).toBe(false);
    });
  });

  describe("enabled/disabled state", () => {
    it("should keep cursor visible when disabled", () => {
      const { result } = renderHook(() =>
        useCursorAutoHide({ enabled: false }),
      );

      expect(result.current.cursorVisible).toBe(true);
      expect(result.current.cursorClassName).toBe("");

      // Advance time - cursor should remain visible
      act(() => {
        advanceTime(10000);
      });
      expect(result.current.cursorVisible).toBe(true);
      expect(result.current.cursorClassName).toBe("");
    });

    it("should show cursor immediately when disabled after being hidden", () => {
      const { result, rerender } = renderHook(
        (props: UseCursorAutoHideOptions) => useCursorAutoHide(props),
        { initialProps: { enabled: true } },
      );

      // Hide cursor
      act(() => {
        advanceTime(2100);
      });
      expect(result.current.cursorVisible).toBe(false);

      // Disable - should show cursor
      rerender({ enabled: false });
      expect(result.current.cursorVisible).toBe(true);
      expect(result.current.cursorClassName).toBe("");
    });

    it("should re-enable auto-hide when enabled changes from false to true", () => {
      const { result, rerender } = renderHook(
        (props: UseCursorAutoHideOptions) => useCursorAutoHide(props),
        { initialProps: { enabled: false } },
      );

      expect(result.current.cursorVisible).toBe(true);

      // Enable auto-hide
      rerender({ enabled: true });

      // Should hide after timeout
      act(() => {
        advanceTime(2100);
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should handle rapid enable/disable toggles", () => {
      const { result, rerender } = renderHook(
        (props: UseCursorAutoHideOptions) => useCursorAutoHide(props),
        { initialProps: { enabled: true } },
      );

      // Hide cursor
      act(() => {
        advanceTime(2100);
      });
      expect(result.current.cursorVisible).toBe(false);

      // Disable
      rerender({ enabled: false });
      expect(result.current.cursorVisible).toBe(true);

      // Enable again
      rerender({ enabled: true });
      expect(result.current.cursorVisible).toBe(true);

      // Should hide after timeout
      act(() => {
        advanceTime(2100);
      });
      expect(result.current.cursorVisible).toBe(false);
    });
  });

  describe("edge cases", () => {
    it("should cleanup interval on unmount", () => {
      const { unmount } = renderHook(() => useCursorAutoHide());
      unmount();

      // If cleanup works, advancing timers shouldn't cause issues
      act(() => {
        advanceTime(10000);
      });
      // Test passes if no errors are thrown
      expect(true).toBe(true);
    });

    it("should handle zero idleTimeout", () => {
      const { result } = renderHook(() =>
        useCursorAutoHide({ idleTimeout: 0 }),
      );

      expect(result.current.cursorVisible).toBe(true);

      // Should hide immediately on next check
      act(() => {
        advanceTime(300);
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should handle very small checkInterval", () => {
      const { result } = renderHook(() =>
        useCursorAutoHide({ idleTimeout: 100, checkInterval: 10 }),
      );

      expect(result.current.cursorVisible).toBe(true);

      act(() => {
        advanceTime(100);
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should handle checkInterval larger than idleTimeout", () => {
      const { result } = renderHook(() =>
        useCursorAutoHide({ idleTimeout: 100, checkInterval: 500 }),
      );

      expect(result.current.cursorVisible).toBe(true);

      // First check happens at 500ms, but timeout is 100ms
      // So it should hide on first check
      act(() => {
        advanceTime(500);
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should maintain cursor visibility state when activity occurs while visible", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      expect(result.current.cursorVisible).toBe(true);

      // Trigger activity while already visible
      act(() => {
        result.current.handleUserActivity();
      });

      // Should remain visible
      expect(result.current.cursorVisible).toBe(true);
      expect(result.current.cursorClassName).toBe("");
    });

    it("should handle configuration changes during runtime", () => {
      const { result, rerender } = renderHook(
        (props: UseCursorAutoHideOptions) => useCursorAutoHide(props),
        { initialProps: { idleTimeout: 2000 } },
      );

      expect(result.current.cursorVisible).toBe(true);

      // Change to shorter timeout
      rerender({ idleTimeout: 500 });

      // Should hide after new timeout
      act(() => {
        // Default checkInterval=300ms, so first check >= 500ms is at 600ms.
        advanceTime(600);
      });
      expect(result.current.cursorVisible).toBe(false);

      // Show cursor again
      act(() => {
        result.current.handleUserActivity();
      });
      expect(result.current.cursorVisible).toBe(true);

      // Change to longer timeout
      rerender({ idleTimeout: 5000 });

      // Should not hide yet
      act(() => {
        advanceTime(2000);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Should hide after new longer timeout
      act(() => {
        // Ensure we cross the timeout and allow a subsequent interval check to run.
        advanceTime(3300);
      });
      expect(result.current.cursorVisible).toBe(false);
    });
  });

  describe("return values", () => {
    it("should return correct cursorClassName when visible", () => {
      const { result } = renderHook(() => useCursorAutoHide());
      expect(result.current.cursorClassName).toBe("");
    });

    it("should return correct cursorClassName when hidden", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      act(() => {
        advanceTime(2100);
      });

      expect(result.current.cursorClassName).toBe("cursor-none");
    });

    it("should return handleUserActivity function", () => {
      const { result } = renderHook(() => useCursorAutoHide());
      expect(typeof result.current.handleUserActivity).toBe("function");
    });

    it("should return stable handleUserActivity reference", () => {
      const { result, rerender } = renderHook(
        (props: UseCursorAutoHideOptions) => useCursorAutoHide(props),
        { initialProps: {} },
      );

      const firstHandler = result.current.handleUserActivity;

      rerender({});
      const secondHandler = result.current.handleUserActivity;

      expect(firstHandler).toBe(secondHandler);
    });
  });

  describe("integration scenarios", () => {
    it("should handle typical reading scenario: idle, then activity, then idle again", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      // Initial state: visible
      expect(result.current.cursorVisible).toBe(true);

      // Idle: hide cursor
      act(() => {
        advanceTime(2100);
      });
      expect(result.current.cursorVisible).toBe(false);

      // User moves mouse: show cursor
      act(() => {
        result.current.handleUserActivity();
      });
      expect(result.current.cursorVisible).toBe(true);

      // Idle again: hide cursor
      act(() => {
        advanceTime(2100);
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should handle continuous activity preventing cursor from hiding", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      // Simulate continuous activity (e.g., user scrolling)
      for (let i = 0; i < 10; i++) {
        act(() => {
          advanceTime(500);
          result.current.handleUserActivity();
        });
      }

      // Cursor should remain visible
      expect(result.current.cursorVisible).toBe(true);

      // Now idle: should hide
      act(() => {
        // Allow for interval quantization (default checkInterval=300ms).
        advanceTime(2300);
      });
      expect(result.current.cursorVisible).toBe(false);
    });

    it("should handle activity just before timeout", () => {
      const { result } = renderHook(() => useCursorAutoHide());

      // Advance to a time well before timeout (using 1500ms which is clearly < 2000ms)
      act(() => {
        advanceTime(1500);
      });
      expect(result.current.cursorVisible).toBe(true);

      // Activity just before timeout
      act(() => {
        result.current.handleUserActivity();
      });

      // Should still be visible
      expect(result.current.cursorVisible).toBe(true);

      // Advance past timeout from last activity
      act(() => {
        advanceTime(2100); // Should hide after full timeout from last activity
      });
      expect(result.current.cursorVisible).toBe(false);
    });
  });
});
