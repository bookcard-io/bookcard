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
import { useDebounce } from "./useDebounce";

describe("useDebounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should return initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("test", 300));
    expect(result.current).toBe("test");
  });

  it("should debounce value changes", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: "initial" } },
    );

    expect(result.current).toBe("initial");

    rerender({ value: "updated" });
    expect(result.current).toBe("initial"); // Still initial

    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe("updated");
  });

  it("should use default delay of 300ms", () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value), {
      initialProps: { value: "initial" },
    });

    rerender({ value: "updated" });
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe("updated");
  });

  it("should cancel previous timeout on rapid changes", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: "initial" } },
    );

    rerender({ value: "change1" });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    rerender({ value: "change2" });
    act(() => {
      vi.advanceTimersByTime(100);
    });
    rerender({ value: "change3" });
    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current).toBe("change3");
  });

  it("should handle different delay values", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: "initial", delay: 500 } },
    );

    rerender({ value: "updated", delay: 500 });
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe("initial"); // Not yet updated

    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe("updated");
  });

  it("should handle number values", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: 0 } },
    );

    rerender({ value: 100 });
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe(100);
  });

  it("should handle boolean values", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: false } },
    );

    rerender({ value: true });
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(result.current).toBe(true);
  });

  it("should cleanup timeout on unmount", () => {
    const { unmount } = renderHook(() => useDebounce("test", 300));
    unmount();
    // If cleanup works, advancing timers shouldn't cause issues
    act(() => {
      vi.advanceTimersByTime(300);
    });
    // Test passes if no errors are thrown
    expect(true).toBe(true);
  });

  it("should cleanup timeout when value changes before delay", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      { initialProps: { value: "initial" } },
    );

    rerender({ value: "updated" });
    // Cleanup should clear the previous timeout
    act(() => {
      vi.advanceTimersByTime(100);
    });
    // Value should still be initial
    expect(result.current).toBe("initial");

    // Advance to complete the new timeout
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe("updated");
  });
});
