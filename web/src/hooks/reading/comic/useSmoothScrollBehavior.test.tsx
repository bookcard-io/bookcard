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

import { act, render } from "@testing-library/react";
import { createRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  SMOOTH_SCROLL_RESTORE_DELAY_MS,
  type SmoothScrollBehaviorController,
  useSmoothScrollBehavior,
} from "./useSmoothScrollBehavior";

function Harness(props: {
  restoreDelayMs?: number;
  controllerRef: React.RefObject<SmoothScrollBehaviorController | null>;
}): null {
  const controller = useSmoothScrollBehavior(props.restoreDelayMs);
  props.controllerRef.current = controller;
  return null;
}

describe("useSmoothScrollBehavior", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("applies smooth scroll behavior and restores it after delay", () => {
    vi.useFakeTimers();
    const el = document.createElement("div");
    el.style.scrollBehavior = "auto";
    const scrollFn = vi.fn();
    const controllerRef = createRef<SmoothScrollBehaviorController>();

    render(<Harness controllerRef={controllerRef} />);
    const controller = controllerRef.current;
    if (!controller) throw new Error("Expected controller to be set");

    act(() => {
      controller.scrollWithSmoothBehavior(el, scrollFn);
    });

    expect(el.style.scrollBehavior).toBe("smooth");
    expect(scrollFn).toHaveBeenCalledTimes(1);

    act(() => {
      vi.advanceTimersByTime(SMOOTH_SCROLL_RESTORE_DELAY_MS);
    });

    expect(el.style.scrollBehavior).toBe("auto");
  });

  it("extends restore window on repeated calls", () => {
    vi.useFakeTimers();
    const el = document.createElement("div");
    el.style.scrollBehavior = "auto";
    const scrollFn1 = vi.fn();
    const scrollFn2 = vi.fn();
    const clearTimeoutSpy = vi.spyOn(window, "clearTimeout");
    const controllerRef = createRef<SmoothScrollBehaviorController>();

    render(<Harness controllerRef={controllerRef} />);
    const controller = controllerRef.current;
    if (!controller) throw new Error("Expected controller to be set");

    act(() => {
      controller.scrollWithSmoothBehavior(el, scrollFn1);
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    act(() => {
      vi.advanceTimersByTime(SMOOTH_SCROLL_RESTORE_DELAY_MS / 2);
      controller.scrollWithSmoothBehavior(el, scrollFn2);
    });

    expect(clearTimeoutSpy).toHaveBeenCalled();
    expect(el.style.scrollBehavior).toBe("smooth");
    expect(scrollFn2).toHaveBeenCalledTimes(1);

    act(() => {
      vi.advanceTimersByTime(SMOOTH_SCROLL_RESTORE_DELAY_MS - 1);
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(el.style.scrollBehavior).toBe("auto");

    clearTimeoutSpy.mockRestore();
  });

  it("restores original behavior on unmount", () => {
    vi.useFakeTimers();
    const el = document.createElement("div");
    el.style.scrollBehavior = "auto";
    const scrollFn = vi.fn();
    const clearTimeoutSpy = vi.spyOn(window, "clearTimeout");
    const controllerRef = createRef<SmoothScrollBehaviorController>();

    const { unmount } = render(<Harness controllerRef={controllerRef} />);
    const controller = controllerRef.current;
    if (!controller) throw new Error("Expected controller to be set");

    act(() => {
      controller.scrollWithSmoothBehavior(el, scrollFn);
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    unmount();
    expect(clearTimeoutSpy).toHaveBeenCalled();
    expect(el.style.scrollBehavior).toBe("auto");

    clearTimeoutSpy.mockRestore();
  });

  it("preserves original behavior value", () => {
    vi.useFakeTimers();
    const el = document.createElement("div");
    el.style.scrollBehavior = "smooth";
    const scrollFn = vi.fn();
    const controllerRef = createRef<SmoothScrollBehaviorController>();

    render(<Harness controllerRef={controllerRef} />);
    const controller = controllerRef.current;
    if (!controller) throw new Error("Expected controller to be set");

    act(() => {
      controller.scrollWithSmoothBehavior(el, scrollFn);
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    act(() => {
      vi.advanceTimersByTime(SMOOTH_SCROLL_RESTORE_DELAY_MS);
    });
    expect(el.style.scrollBehavior).toBe("smooth");
  });

  it("uses custom restore delay when provided", () => {
    vi.useFakeTimers();
    const customDelay = 500;
    const el = document.createElement("div");
    el.style.scrollBehavior = "auto";
    const scrollFn = vi.fn();
    const controllerRef = createRef<SmoothScrollBehaviorController>();

    render(
      <Harness restoreDelayMs={customDelay} controllerRef={controllerRef} />,
    );
    const controller = controllerRef.current;
    if (!controller) throw new Error("Expected controller to be set");

    act(() => {
      controller.scrollWithSmoothBehavior(el, scrollFn);
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    act(() => {
      vi.advanceTimersByTime(customDelay - 1);
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(el.style.scrollBehavior).toBe("auto");
  });
});
