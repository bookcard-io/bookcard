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
import { useShelfCardAnimation } from "./useShelfCardAnimation";

describe("useShelfCardAnimation", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should initialize with false states", () => {
    const { result } = renderHook(() => useShelfCardAnimation());

    expect(result.current.isShaking).toBe(false);
    expect(result.current.isGlowing).toBe(false);
    expect(result.current.triggerAnimation).toBeDefined();
  });

  it("should trigger shake and glow animation", () => {
    const { result } = renderHook(() => useShelfCardAnimation());

    act(() => {
      result.current.triggerAnimation();
    });

    expect(result.current.isShaking).toBe(true);
    expect(result.current.isGlowing).toBe(true);
  });

  it("should reset shake after 500ms", () => {
    const { result } = renderHook(() => useShelfCardAnimation());

    act(() => {
      result.current.triggerAnimation();
    });

    expect(result.current.isShaking).toBe(true);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.isShaking).toBe(false);
    expect(result.current.isGlowing).toBe(true); // Still glowing
  });

  it("should reset glow after 1000ms", () => {
    const { result } = renderHook(() => useShelfCardAnimation());

    act(() => {
      result.current.triggerAnimation();
    });

    expect(result.current.isGlowing).toBe(true);

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(result.current.isGlowing).toBe(false);
    expect(result.current.isShaking).toBe(false); // Already reset at 500ms
  });

  it("should handle multiple animation triggers", () => {
    const { result } = renderHook(() => useShelfCardAnimation());

    act(() => {
      result.current.triggerAnimation();
    });

    expect(result.current.isShaking).toBe(true);
    expect(result.current.isGlowing).toBe(true);

    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Trigger again before first completes
    act(() => {
      result.current.triggerAnimation();
    });

    expect(result.current.isShaking).toBe(true);
    expect(result.current.isGlowing).toBe(true);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.isShaking).toBe(false);
    expect(result.current.isGlowing).toBe(true);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.isGlowing).toBe(false);
  });

  it("should maintain stable triggerAnimation reference", () => {
    const { result, rerender } = renderHook(() => useShelfCardAnimation());

    const firstTrigger = result.current.triggerAnimation;

    rerender();

    expect(result.current.triggerAnimation).toBe(firstTrigger);
  });
});
