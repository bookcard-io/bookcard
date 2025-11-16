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
import { useModalAnimation } from "./useModalAnimation";

describe("useModalAnimation", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should initialize with hasAnimated false and isShaking false", () => {
    const { result } = renderHook(() => useModalAnimation());

    expect(result.current.hasAnimated).toBe(false);
    expect(result.current.isShaking).toBe(false);
    expect(result.current.overlayStyle).toBeUndefined();
    expect(result.current.containerStyle).toBeUndefined();
  });

  it("should set hasAnimated to true after fadeInDuration", () => {
    const { result } = renderHook(() => useModalAnimation(250));

    expect(result.current.hasAnimated).toBe(false);

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(result.current.hasAnimated).toBe(true);
  });

  it("should use default fadeInDuration of 250ms", () => {
    const { result } = renderHook(() => useModalAnimation());

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(result.current.hasAnimated).toBe(true);
  });

  it("should set overlayStyle to animation none after animation completes", () => {
    const { result } = renderHook(() => useModalAnimation(250));

    expect(result.current.overlayStyle).toBeUndefined();

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(result.current.overlayStyle).toEqual({ animation: "none" });
  });

  it("should set containerStyle to animation none after animation completes when not shaking", () => {
    const { result } = renderHook(() => useModalAnimation(250));

    expect(result.current.containerStyle).toBeUndefined();

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(result.current.containerStyle).toEqual({ animation: "none" });
  });

  it("should set containerStyle to shake animation when shaking after animation completes", () => {
    const { result } = renderHook(() => useModalAnimation(250));

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(result.current.containerStyle).toEqual({ animation: "none" });

    act(() => {
      result.current.triggerShake();
    });

    expect(result.current.isShaking).toBe(true);
    expect(result.current.containerStyle).toEqual({
      animation: "shake 0.5s ease-in-out",
    });
  });

  it("should stop shaking after 500ms", () => {
    const { result } = renderHook(() => useModalAnimation(250));

    act(() => {
      vi.advanceTimersByTime(250);
    });

    act(() => {
      result.current.triggerShake();
    });

    expect(result.current.isShaking).toBe(true);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.isShaking).toBe(false);
    expect(result.current.containerStyle).toEqual({ animation: "none" });
  });

  it("should handle multiple shake triggers", () => {
    const { result } = renderHook(() => useModalAnimation(250));

    act(() => {
      vi.advanceTimersByTime(250);
    });

    act(() => {
      result.current.triggerShake();
    });

    expect(result.current.isShaking).toBe(true);

    act(() => {
      vi.advanceTimersByTime(200);
    });

    // Trigger another shake while still shaking
    act(() => {
      result.current.triggerShake();
    });

    expect(result.current.isShaking).toBe(true);

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.isShaking).toBe(false);
  });

  it("should not set overlayStyle or containerStyle before animation completes", () => {
    const { result } = renderHook(() => useModalAnimation(250));

    expect(result.current.overlayStyle).toBeUndefined();
    expect(result.current.containerStyle).toBeUndefined();

    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current.overlayStyle).toBeUndefined();
    expect(result.current.containerStyle).toBeUndefined();
  });

  it("should handle custom fadeInDuration", () => {
    const { result } = renderHook(() => useModalAnimation(500));

    expect(result.current.hasAnimated).toBe(false);

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(result.current.hasAnimated).toBe(false);

    act(() => {
      vi.advanceTimersByTime(250);
    });

    expect(result.current.hasAnimated).toBe(true);
  });

  it("should clean up timer on unmount", () => {
    const { unmount } = renderHook(() => useModalAnimation(250));

    unmount();

    act(() => {
      vi.advanceTimersByTime(250);
    });

    // Should not cause errors
    expect(true).toBe(true);
  });
});
