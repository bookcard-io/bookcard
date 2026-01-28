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
import { useEffect, useRef } from "react";
import { describe, expect, it, vi } from "vitest";
import { usePagedWheelNavigation } from "./usePagedWheelNavigation";

type WheelHandler = (e: React.WheelEvent<HTMLElement>) => void;

function Harness({
  onWheelReady,
  attachRef = true,
  ...props
}: Omit<Parameters<typeof usePagedWheelNavigation>[0], "containerRef"> & {
  onWheelReady?: (handler: WheelHandler) => void;
  attachRef?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { handleWheel } = usePagedWheelNavigation({ ...props, containerRef });

  useEffect(() => {
    onWheelReady?.(handleWheel);
  }, [handleWheel, onWheelReady]);

  return (
    <div
      ref={attachRef ? containerRef : undefined}
      data-testid="wheel-harness"
      onWheel={handleWheel}
    />
  );
}

function setScroll(
  el: HTMLElement,
  values: Partial<
    HTMLElement & {
      scrollTop: number;
      scrollLeft: number;
      scrollHeight: number;
      scrollWidth: number;
      clientHeight: number;
      clientWidth: number;
    }
  >,
) {
  for (const [k, v] of Object.entries(values)) {
    Object.defineProperty(el, k, { value: v, configurable: true });
  }
}

describe("usePagedWheelNavigation", () => {
  it("does nothing when containerRef is null", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    let handler: WheelHandler | null = null;

    render(
      <Harness
        attachRef={false}
        readingDirection="vertical"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        wheelThresholdPx={1}
        edgeTolerancePx={0}
        cooldownMs={0}
        onWheelReady={(h) => {
          handler = h;
        }}
      />,
    );

    if (handler === null) {
      throw new Error("Expected wheel handler to be available");
    }
    const mustHandler: WheelHandler = handler;
    const preventDefault = vi.fn();
    mustHandler({
      ctrlKey: false,
      preventDefault,
      nativeEvent: { deltaX: 0, deltaY: -50, deltaMode: 0 },
    } as unknown as React.WheelEvent<HTMLElement>);

    expect(preventDefault).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
    expect(onNext).not.toHaveBeenCalled();
  });

  it("ignores ctrl+wheel (trackpad pinch-to-zoom)", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    const { getByTestId } = render(
      <Harness
        readingDirection="vertical"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        wheelThresholdPx={1}
        edgeTolerancePx={0}
        cooldownMs={0}
      />,
    );

    const el = getByTestId("wheel-harness") as HTMLElement;
    setScroll(el, { scrollTop: 0, scrollHeight: 2000, clientHeight: 1000 });

    fireEvent.wheel(el, { deltaY: -100, ctrlKey: true });
    expect(onPrevious).not.toHaveBeenCalled();
    expect(onNext).not.toHaveBeenCalled();
  });

  it("respects canGoNext/canGoPrevious gating", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    const { getByTestId } = render(
      <Harness
        readingDirection="vertical"
        canGoNext={false}
        canGoPrevious={false}
        onNext={onNext}
        onPrevious={onPrevious}
        wheelThresholdPx={1}
        edgeTolerancePx={0}
        cooldownMs={0}
      />,
    );

    const el = getByTestId("wheel-harness") as HTMLElement;
    setScroll(el, {
      scrollTop: 0,
      scrollHeight: 2000,
      clientHeight: 1000,
      scrollLeft: 0,
      scrollWidth: 1000,
      clientWidth: 1000,
    });

    fireEvent.wheel(el, { deltaY: -50 }); // would be previous at top edge
    setScroll(el, { scrollTop: 1000 });
    fireEvent.wheel(el, { deltaY: 50 }); // would be next at bottom edge

    expect(onPrevious).not.toHaveBeenCalled();
    expect(onNext).not.toHaveBeenCalled();
  });

  it("prevents repeated same-direction navigation within cooldown", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const nowSpy = vi
      .spyOn(performance, "now")
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(100);

    const { getByTestId } = render(
      <Harness
        readingDirection="vertical"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        wheelThresholdPx={1}
        edgeTolerancePx={0}
        cooldownMs={500}
      />,
    );

    const el = getByTestId("wheel-harness") as HTMLElement;
    setScroll(el, {
      scrollTop: 0,
      scrollHeight: 2000,
      clientHeight: 1000,
      scrollLeft: 0,
      scrollWidth: 1000,
      clientWidth: 1000,
    });

    fireEvent.wheel(el, { deltaY: -50 });
    fireEvent.wheel(el, { deltaY: -50 });

    expect(onPrevious).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(0);
    nowSpy.mockRestore();
  });

  it("allows opposite-direction navigation within cooldown", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const nowSpy = vi
      .spyOn(performance, "now")
      .mockReturnValueOnce(0)
      .mockReturnValueOnce(100);

    const { getByTestId } = render(
      <Harness
        readingDirection="vertical"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        wheelThresholdPx={1}
        edgeTolerancePx={0}
        cooldownMs={500}
      />,
    );

    const el = getByTestId("wheel-harness") as HTMLElement;
    setScroll(el, {
      scrollTop: 0,
      scrollHeight: 2000,
      clientHeight: 1000,
      scrollLeft: 0,
      scrollWidth: 1000,
      clientWidth: 1000,
    });

    fireEvent.wheel(el, { deltaY: -50 }); // previous at top
    setScroll(el, { scrollTop: 1000 }); // jump to bottom for next
    fireEvent.wheel(el, { deltaY: 50 }); // next at bottom

    expect(onPrevious).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
    nowSpy.mockRestore();
  });

  it("normalizes wheel deltas for deltaMode=line", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    let handler: WheelHandler | null = null;

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        wheelThresholdPx={30}
        edgeTolerancePx={0}
        cooldownMs={0}
        onWheelReady={(h) => {
          handler = h;
        }}
      />,
    );

    const el = getByTestId("wheel-harness") as HTMLElement;
    setScroll(el, {
      scrollLeft: 0,
      scrollWidth: 2000,
      clientWidth: 1000,
      scrollTop: 0,
      scrollHeight: 1000,
      clientHeight: 1000,
    });

    // deltaMode=1 => 2 lines => ~32px after normalization, should exceed 30px.
    // We call the handler directly to control `nativeEvent.deltaMode` reliably.
    if (handler === null) {
      throw new Error("Expected wheel handler to be available");
    }
    const mustHandler: WheelHandler = handler;
    const preventDefault = vi.fn();
    mustHandler({
      ctrlKey: false,
      preventDefault,
      nativeEvent: { deltaX: -2, deltaY: 0, deltaMode: 1 },
    } as unknown as React.WheelEvent<HTMLElement>);

    expect(preventDefault).toHaveBeenCalled();
    expect(onPrevious).toHaveBeenCalledTimes(1);
  });

  it("normalizes wheel deltas for deltaMode=page", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    let handler: WheelHandler | null = null;

    const { getByTestId } = render(
      <Harness
        readingDirection="vertical"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        wheelThresholdPx={500}
        edgeTolerancePx={0}
        cooldownMs={0}
        onWheelReady={(h) => {
          handler = h;
        }}
      />,
    );

    const el = getByTestId("wheel-harness") as HTMLElement;
    setScroll(el, {
      scrollTop: 0,
      scrollHeight: 2000,
      clientHeight: 1000,
      scrollLeft: 0,
      scrollWidth: 1000,
      clientWidth: 1000,
    });

    if (handler === null) {
      throw new Error("Expected wheel handler to be available");
    }
    const mustHandler: WheelHandler = handler;
    const preventDefault = vi.fn();
    mustHandler({
      ctrlKey: false,
      preventDefault,
      nativeEvent: { deltaX: 0, deltaY: -1, deltaMode: 2 },
    } as unknown as React.WheelEvent<HTMLElement>);

    // -1 page => ~-800px after normalization, exceeds 500 threshold.
    expect(preventDefault).toHaveBeenCalled();
    expect(onPrevious).toHaveBeenCalledTimes(1);
  });
});
