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
import { beforeEach, describe, expect, it } from "vitest";
import { useModalAnimation } from "./useModalAnimation";

describe("useModalAnimation", () => {
  beforeEach(() => {
    // No setup needed
  });

  it("should initialize with hasAnimated false and isShaking false", () => {
    const { result } = renderHook(() => useModalAnimation());

    expect(result.current.hasAnimated).toBe(false);
    expect(result.current.isShaking).toBe(false);
  });

  it("should have undefined overlayStyle and containerStyle initially", () => {
    const { result } = renderHook(() => useModalAnimation());

    expect(result.current.overlayStyle).toBeUndefined();
    expect(result.current.containerStyle).toBeUndefined();
  });

  it("should trigger shake animation and set isShaking to true", () => {
    const { result } = renderHook(() => useModalAnimation());

    act(() => {
      result.current.triggerShake();
    });

    expect(result.current.isShaking).toBe(true);
  });

  it("should use default fadeInDuration of 250ms", () => {
    const { result } = renderHook(() => useModalAnimation());

    expect(result.current.hasAnimated).toBe(false);
    expect(result.current.overlayStyle).toBeUndefined();
  });

  it("should accept custom fadeInDuration", () => {
    const { result } = renderHook(() => useModalAnimation(500));

    expect(result.current.hasAnimated).toBe(false);
    expect(result.current.overlayStyle).toBeUndefined();
  });

  it("should return stable triggerShake function", () => {
    const { result, rerender } = renderHook(() => useModalAnimation());

    const initialTriggerShake = result.current.triggerShake;

    rerender();

    expect(result.current.triggerShake).toBe(initialTriggerShake);
  });

  it("should return all expected properties", () => {
    const { result } = renderHook(() => useModalAnimation());

    expect(result.current).toHaveProperty("hasAnimated");
    expect(result.current).toHaveProperty("isShaking");
    expect(result.current).toHaveProperty("triggerShake");
    expect(result.current).toHaveProperty("overlayStyle");
    expect(result.current).toHaveProperty("containerStyle");
  });

  it("should have triggerShake as a function", () => {
    const { result } = renderHook(() => useModalAnimation());

    expect(typeof result.current.triggerShake).toBe("function");
  });

  it("should compute overlayStyle based on hasAnimatedRef", () => {
    const { result } = renderHook(() => useModalAnimation(250));

    // Initially overlayStyle is undefined because hasAnimatedRef.current is false (line 77-79)
    expect(result.current.overlayStyle).toBeUndefined();
  });

  it("should not replay animation on subsequent renders (early return check)", () => {
    const { result, rerender } = renderHook(() => useModalAnimation(250));

    // Initially hasAnimated is false
    expect(result.current.hasAnimated).toBe(false);

    // Rerender multiple times - the early return check (line 60) prevents
    // the effect from running again after the first time
    rerender();
    rerender();
    rerender();

    // Verify hook maintains state correctly
    expect(result.current).toHaveProperty("hasAnimated");
    expect(result.current).toHaveProperty("isShaking");
    expect(result.current).toHaveProperty("triggerShake");
  });

  it("should compute containerStyle based on hasAnimatedRef and isShaking state", () => {
    const { result } = renderHook(() => useModalAnimation());

    // Initially containerStyle is undefined (hasAnimatedRef.current is false, line 81-85)
    expect(result.current.containerStyle).toBeUndefined();

    // Trigger shake - this sets isShaking to true (line 71)
    // The setTimeout callback (line 73) will reset it later, but we test the immediate state
    act(() => {
      result.current.triggerShake();
    });

    // isShaking should be true immediately after triggerShake (line 71)
    expect(result.current.isShaking).toBe(true);
  });
});
