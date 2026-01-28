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
import { describe, expect, it, vi } from "vitest";
import type { KeydownEventTarget } from "@/types/pagedNavigation";
import { usePagedKeyboardNavigation } from "./usePagedKeyboardNavigation";

function createKeydownTarget(): {
  target: KeydownEventTarget;
  addSpy: ReturnType<typeof vi.fn>;
  removeSpy: ReturnType<typeof vi.fn>;
  getListener: () => (e: KeyboardEvent) => void;
} {
  const addSpy = vi.fn();
  const removeSpy = vi.fn();
  let listener: ((e: KeyboardEvent) => void) | null = null;

  const target: KeydownEventTarget = {
    addEventListener: (type, l) => {
      addSpy(type, l);
      listener = l;
    },
    removeEventListener: (type, l) => {
      removeSpy(type, l);
    },
  };

  return {
    target,
    addSpy,
    removeSpy,
    getListener: () => {
      if (!listener) {
        throw new Error("Expected keydown listener to be registered");
      }
      return listener;
    },
  };
}

function Harness(props: Parameters<typeof usePagedKeyboardNavigation>[0]) {
  usePagedKeyboardNavigation(props);
  return null;
}

describe("usePagedKeyboardNavigation", () => {
  it("does not register listeners when disabled", () => {
    const t = createKeydownTarget();
    render(
      <Harness
        readingDirection="ltr"
        totalPages={10}
        onGoToPage={vi.fn()}
        canGoNext={true}
        canGoPrevious={true}
        onNext={vi.fn()}
        onPrevious={vi.fn()}
        enabled={false}
        target={t.target}
      />,
    );
    expect(t.addSpy).not.toHaveBeenCalled();
    expect(t.removeSpy).not.toHaveBeenCalled();
  });

  it("registers and cleans up keydown listener", () => {
    const t = createKeydownTarget();
    const { unmount } = render(
      <Harness
        readingDirection="ltr"
        totalPages={10}
        onGoToPage={vi.fn()}
        canGoNext={true}
        canGoPrevious={true}
        onNext={vi.fn()}
        onPrevious={vi.fn()}
        enabled={true}
        target={t.target}
      />,
    );

    expect(t.addSpy).toHaveBeenCalledTimes(1);
    const listener = t.getListener();

    unmount();
    expect(t.removeSpy).toHaveBeenCalledTimes(1);
    expect(t.removeSpy.mock.calls[0]?.[1]).toBe(listener);
  });

  it("ignores events from editable targets", () => {
    const t = createKeydownTarget();
    const onNext = vi.fn();

    render(
      <Harness
        readingDirection="ltr"
        totalPages={10}
        onGoToPage={vi.fn()}
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={vi.fn()}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault = vi.fn();
    const input = document.createElement("input");

    listener({
      key: "ArrowRight",
      preventDefault,
      target: input,
    } as unknown as KeyboardEvent);

    expect(preventDefault).not.toHaveBeenCalled();
    expect(onNext).not.toHaveBeenCalled();
  });

  it("navigates next/previous and prevents default", () => {
    const t = createKeydownTarget();
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    render(
      <Harness
        readingDirection="ltr"
        totalPages={10}
        onGoToPage={vi.fn()}
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault1 = vi.fn();
    listener({
      key: "ArrowRight",
      preventDefault: preventDefault1,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);
    expect(preventDefault1).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);

    const preventDefault2 = vi.fn();
    listener({
      key: "ArrowLeft",
      preventDefault: preventDefault2,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);
    expect(preventDefault2).toHaveBeenCalledTimes(1);
    expect(onPrevious).toHaveBeenCalledTimes(1);
  });

  it("respects canGoNext/canGoPrevious for next/previous actions", () => {
    const t = createKeydownTarget();
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    render(
      <Harness
        readingDirection="ltr"
        totalPages={10}
        onGoToPage={vi.fn()}
        canGoNext={false}
        canGoPrevious={false}
        onNext={onNext}
        onPrevious={onPrevious}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault1 = vi.fn();
    listener({
      key: "ArrowRight",
      preventDefault: preventDefault1,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);
    expect(preventDefault1).not.toHaveBeenCalled();
    expect(onNext).not.toHaveBeenCalled();

    const preventDefault2 = vi.fn();
    listener({
      key: "ArrowLeft",
      preventDefault: preventDefault2,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);
    expect(preventDefault2).not.toHaveBeenCalled();
    expect(onPrevious).not.toHaveBeenCalled();
  });

  it("handles Home/End page jumps", () => {
    const t = createKeydownTarget();
    const onGoToPage = vi.fn();

    render(
      <Harness
        readingDirection="ltr"
        totalPages={42}
        onGoToPage={onGoToPage}
        canGoNext={true}
        canGoPrevious={true}
        onNext={vi.fn()}
        onPrevious={vi.fn()}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault1 = vi.fn();
    listener({
      key: "Home",
      preventDefault: preventDefault1,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);
    expect(preventDefault1).toHaveBeenCalledTimes(1);
    expect(onGoToPage).toHaveBeenCalledWith(1);

    const preventDefault2 = vi.fn();
    listener({
      key: "End",
      preventDefault: preventDefault2,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);
    expect(preventDefault2).toHaveBeenCalledTimes(1);
    expect(onGoToPage).toHaveBeenCalledWith(42);
  });

  it("uses reading direction strategy (rtl ArrowRight -> previous)", () => {
    const t = createKeydownTarget();
    const onNext = vi.fn();
    const onPrevious = vi.fn();

    render(
      <Harness
        readingDirection="rtl"
        totalPages={10}
        onGoToPage={vi.fn()}
        canGoNext={true}
        canGoPrevious={true}
        onNext={onNext}
        onPrevious={onPrevious}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault = vi.fn();
    listener({
      key: "ArrowRight",
      preventDefault,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);

    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(onPrevious).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(0);
  });
});
