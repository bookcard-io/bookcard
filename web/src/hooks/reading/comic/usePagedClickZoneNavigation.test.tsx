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
import { usePagedClickZoneNavigation } from "./usePagedClickZoneNavigation";

function mockRect(
  el: HTMLElement,
  rect: Partial<DOMRect> & { width: number; height: number },
) {
  Object.defineProperty(el, "getBoundingClientRect", {
    configurable: true,
    value: () =>
      ({
        left: 0,
        top: 0,
        right: rect.width,
        bottom: rect.height,
        x: 0,
        y: 0,
        ...rect,
      }) as DOMRect,
  });
}

function Harness({
  attachRef = true,
  ...props
}: Omit<Parameters<typeof usePagedClickZoneNavigation>[0], "containerRef"> & {
  attachRef?: boolean;
}) {
  const containerRef = useRef<HTMLButtonElement>(null);
  const { handleContainerClick } = usePagedClickZoneNavigation({
    ...props,
    containerRef,
  });

  return (
    <button
      type="button"
      ref={attachRef ? containerRef : undefined}
      data-testid="click-harness"
      onClick={handleContainerClick}
    />
  );
}

describe("usePagedClickZoneNavigation", () => {
  it("does nothing when containerRef is null", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    const { getByTestId } = render(
      <Harness
        attachRef={false}
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
      />,
    );

    fireEvent.click(getByTestId("click-harness"), {
      clientX: 999,
      clientY: 999,
    });
    expect(onNext).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("does nothing when container has zero size", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
      />,
    );

    const el = getByTestId("click-harness") as HTMLElement;
    mockRect(el, { width: 0, height: 200 });

    fireEvent.click(el, { clientX: 10, clientY: 10 });
    expect(onNext).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("navigates next/previous based on click zones (ltr)", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
      />,
    );

    const el = getByTestId("click-harness") as HTMLElement;
    mockRect(el, { width: 300, height: 300 });

    fireEvent.click(el, { clientX: 10, clientY: 150 }); // left third
    expect(onPrevious).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(0);

    fireEvent.click(el, { clientX: 290, clientY: 150 }); // right third
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it("does not navigate when clicking in the center zone", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
      />,
    );

    const el = getByTestId("click-harness") as HTMLElement;
    mockRect(el, { width: 300, height: 300 });

    fireEvent.click(el, { clientX: 150, clientY: 150 });
    expect(onNext).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("respects canGoNext/canGoPrevious", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    const { getByTestId } = render(
      <Harness
        readingDirection="ltr"
        canGoNext={false}
        canGoPrevious={false}
        onNext={onNext}
        onPrevious={onPrevious}
      />,
    );

    const el = getByTestId("click-harness") as HTMLElement;
    mockRect(el, { width: 300, height: 300 });

    fireEvent.click(el, { clientX: 10, clientY: 150 }); // would be previous
    fireEvent.click(el, { clientX: 290, clientY: 150 }); // would be next
    expect(onNext).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("uses vertical click zones for vertical reading direction", () => {
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    const { getByTestId } = render(
      <Harness
        readingDirection="vertical"
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
      />,
    );

    const el = getByTestId("click-harness") as HTMLElement;
    mockRect(el, { width: 300, height: 300 });

    fireEvent.click(el, { clientX: 150, clientY: 10 }); // top third
    expect(onPrevious).toHaveBeenCalledTimes(1);

    fireEvent.click(el, { clientX: 150, clientY: 290 }); // bottom third
    expect(onNext).toHaveBeenCalledTimes(1);
  });
});
