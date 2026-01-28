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

import { render } from "@testing-library/react";
import { useEffect, useRef } from "react";
import { describe, expect, it, vi } from "vitest";

import { usePagedNavigation } from "./usePagedNavigation";

const mockHandleContainerClick = vi.fn();
const mockHandleTouchStart = vi.fn();
const mockHandleTouchEnd = vi.fn();
const mockHandleWheel = vi.fn();

const usePagedClickZoneNavigationMock = vi.fn((_args: unknown) => ({
  handleContainerClick: mockHandleContainerClick,
}));
const usePagedTouchGesturesMock = vi.fn((_args: unknown) => ({
  handleTouchStart: mockHandleTouchStart,
  handleTouchEnd: mockHandleTouchEnd,
}));
const usePagedWheelNavigationMock = vi.fn((_args: unknown) => ({
  handleWheel: mockHandleWheel,
}));
const usePagedKeyboardNavigationMock = vi.fn((_args: unknown) => undefined);

vi.mock("./usePagedClickZoneNavigation", () => ({
  usePagedClickZoneNavigation: (args: unknown) =>
    usePagedClickZoneNavigationMock(args),
}));
vi.mock("./usePagedTouchGestures", () => ({
  usePagedTouchGestures: (args: unknown) => usePagedTouchGesturesMock(args),
}));
vi.mock("./usePagedWheelNavigation", () => ({
  usePagedWheelNavigation: (args: unknown) => usePagedWheelNavigationMock(args),
}));
vi.mock("./usePagedKeyboardNavigation", () => ({
  usePagedKeyboardNavigation: (args: unknown) =>
    usePagedKeyboardNavigationMock(args),
}));

function Harness({
  onReady,
  ...props
}: Omit<Parameters<typeof usePagedNavigation>[0], "containerRef"> & {
  onReady?: (handlers: ReturnType<typeof usePagedNavigation>) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const handlers = usePagedNavigation({ ...props, containerRef });

  useEffect(() => {
    onReady?.(handlers);
  }, [handlers, onReady]);

  return <div ref={containerRef} data-testid="paged-nav-harness" />;
}

describe("usePagedNavigation", () => {
  it("wires options into sub-hooks and returns their handlers", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();
    const onGoToPage = vi.fn();
    const keyboardTarget = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };

    let gotHandlers: ReturnType<typeof usePagedNavigation> | null = null;
    render(
      <Harness
        readingDirection="rtl"
        totalPages={123}
        onGoToPage={onGoToPage}
        canGoNext={true}
        canGoPrevious={false}
        onNext={onNext}
        onPrevious={onPrevious}
        keyboardEnabled={false}
        keyboardTarget={keyboardTarget}
        swipeThresholdPx={99}
        swipeMaxDurationMs={777}
        onReady={(h) => {
          gotHandlers = h;
        }}
      />,
    );

    // containerRef is created inside the hook; we only assert it is present.
    expect(usePagedKeyboardNavigationMock).toHaveBeenCalledWith(
      expect.objectContaining({
        readingDirection: "rtl",
        totalPages: 123,
        onGoToPage,
        canGoNext: true,
        canGoPrevious: false,
        onNext,
        onPrevious,
        enabled: false,
        target: keyboardTarget,
      }),
    );

    expect(usePagedTouchGesturesMock).toHaveBeenCalledWith(
      expect.objectContaining({
        readingDirection: "rtl",
        canGoNext: true,
        canGoPrevious: false,
        onNext,
        onPrevious,
        swipeThresholdPx: 99,
        swipeMaxDurationMs: 777,
      }),
    );

    expect(usePagedWheelNavigationMock).toHaveBeenCalledWith(
      expect.objectContaining({
        readingDirection: "rtl",
        canGoNext: true,
        canGoPrevious: false,
        onNext,
        onPrevious,
        containerRef: expect.any(Object),
      }),
    );

    expect(usePagedClickZoneNavigationMock).toHaveBeenCalledWith(
      expect.objectContaining({
        readingDirection: "rtl",
        canGoNext: true,
        canGoPrevious: false,
        onNext,
        onPrevious,
        containerRef: expect.any(Object),
      }),
    );

    expect(gotHandlers).toEqual({
      handleContainerClick: mockHandleContainerClick,
      handleTouchStart: mockHandleTouchStart,
      handleTouchEnd: mockHandleTouchEnd,
      handleWheel: mockHandleWheel,
    });
  });
});
