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

import { fireEvent, render } from "@testing-library/react";
import { useRef } from "react";
import { describe, expect, it, vi } from "vitest";
import { usePagedTouchGestures } from "./usePagedTouchGestures";

function makeTouch(
  target: Element,
  {
    clientX,
    clientY,
    identifier = 0,
  }: { clientX: number; clientY: number; identifier?: number },
): Touch {
  return new Touch({
    identifier,
    target,
    clientX,
    clientY,
    pageX: clientX,
    pageY: clientY,
    screenX: clientX,
    screenY: clientY,
    radiusX: 1,
    radiusY: 1,
    rotationAngle: 0,
    force: 0.5,
  });
}

function Harness(
  props: Omit<Parameters<typeof usePagedTouchGestures>[0], "now"> & {
    now?: () => number;
  },
) {
  const { handleTouchStart, handleTouchEnd } = usePagedTouchGestures(props);
  const ref = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={ref}
      data-testid="touch-harness"
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    />
  );
}

describe("usePagedTouchGestures", () => {
  it("ignores touchstart events without touches", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const now = vi.fn().mockReturnValue(0);

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        swipeThresholdPx={10}
        swipeMaxDurationMs={300}
        now={now}
      />,
    );

    const el = getByTestId("touch-harness");
    fireEvent.touchStart(el, { touches: [] });
    fireEvent.touchEnd(el, {
      changedTouches: [makeTouch(el, { clientX: 0, clientY: 0 })],
    });

    expect(onNext).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("clears touch state on touchend even if changedTouches is missing", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const now = vi.fn().mockReturnValueOnce(0).mockReturnValueOnce(10);

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        swipeThresholdPx={10}
        swipeMaxDurationMs={300}
        now={now}
      />,
    );

    const el = getByTestId("touch-harness");
    fireEvent.touchStart(el, {
      touches: [makeTouch(el, { clientX: 100, clientY: 0 })],
    });
    fireEvent.touchEnd(el, { changedTouches: [] });

    // This would normally be a swipe, but state was cleared by the prior touchend.
    fireEvent.touchEnd(el, {
      changedTouches: [makeTouch(el, { clientX: 0, clientY: 0 })],
    });
    expect(onNext).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("navigates next/previous for ltr swipes", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const now = vi
      .fn()
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(50)
      .mockReturnValueOnce(100)
      .mockReturnValueOnce(150);

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        swipeThresholdPx={10}
        swipeMaxDurationMs={300}
        now={now}
      />,
    );

    const el = getByTestId("touch-harness");

    // Swipe left (deltaX negative) -> next for LTR.
    fireEvent.touchStart(el, {
      touches: [makeTouch(el, { clientX: 100, clientY: 0 })],
    });
    fireEvent.touchEnd(el, {
      changedTouches: [makeTouch(el, { clientX: 0, clientY: 0 })],
    });
    expect(onNext).toHaveBeenCalledTimes(1);
    expect(onPrevious).toHaveBeenCalledTimes(0);

    // Swipe right (deltaX positive) -> previous for LTR.
    fireEvent.touchStart(el, {
      touches: [makeTouch(el, { clientX: 0, clientY: 0 })],
    });
    fireEvent.touchEnd(el, {
      changedTouches: [makeTouch(el, { clientX: 100, clientY: 0 })],
    });
    expect(onPrevious).toHaveBeenCalledTimes(1);
  });

  it("does not navigate when swipe exceeds max duration", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const now = vi.fn().mockReturnValueOnce(0).mockReturnValueOnce(999);

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        swipeThresholdPx={10}
        swipeMaxDurationMs={100}
        now={now}
      />,
    );

    const el = getByTestId("touch-harness");
    fireEvent.touchStart(el, {
      touches: [makeTouch(el, { clientX: 100, clientY: 0 })],
    });
    fireEvent.touchEnd(el, {
      changedTouches: [makeTouch(el, { clientX: 0, clientY: 0 })],
    });

    expect(onNext).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("respects canGoNext/canGoPrevious", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const now = vi.fn().mockReturnValueOnce(0).mockReturnValueOnce(50);

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={false}
        canGoPrevious={false}
        onNext={onNext}
        onPrevious={onPrevious}
        swipeThresholdPx={10}
        swipeMaxDurationMs={300}
        now={now}
      />,
    );

    const el = getByTestId("touch-harness");
    fireEvent.touchStart(el, {
      touches: [makeTouch(el, { clientX: 100, clientY: 0 })],
    });
    fireEvent.touchEnd(el, {
      changedTouches: [makeTouch(el, { clientX: 0, clientY: 0 })],
    });

    expect(onNext).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("uses vertical swipe mapping for vertical reading direction", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const now = vi.fn().mockReturnValueOnce(0).mockReturnValueOnce(50);

    const { getByTestId } = render(
      <Harness
        readingDirection="vertical"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        swipeThresholdPx={10}
        swipeMaxDurationMs={300}
        now={now}
      />,
    );

    const el = getByTestId("touch-harness");

    // Swipe up (deltaY negative) -> next for vertical.
    fireEvent.touchStart(el, {
      touches: [makeTouch(el, { clientX: 0, clientY: 100 })],
    });
    fireEvent.touchEnd(el, {
      changedTouches: [makeTouch(el, { clientX: 0, clientY: 0 })],
    });

    expect(onNext).toHaveBeenCalledTimes(1);
    expect(onPrevious).toHaveBeenCalledTimes(0);
  });
});
