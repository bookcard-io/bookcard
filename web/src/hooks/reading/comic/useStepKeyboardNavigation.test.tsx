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
import { useStepKeyboardNavigation } from "./useStepKeyboardNavigation";

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

function Harness(props: Parameters<typeof useStepKeyboardNavigation>[0]): null {
  useStepKeyboardNavigation(props);
  return null;
}

describe("useStepKeyboardNavigation", () => {
  it("does not register listeners when disabled", () => {
    const t = createKeydownTarget();
    render(
      <Harness
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 1}
        onGoToPage={vi.fn()}
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
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 1}
        onGoToPage={vi.fn()}
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
    const onGoToPage = vi.fn();

    render(
      <Harness
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 1}
        onGoToPage={onGoToPage}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault = vi.fn();
    const input = document.createElement("input");

    listener({
      key: "ArrowDown",
      preventDefault,
      target: input,
    } as unknown as KeyboardEvent);

    expect(preventDefault).not.toHaveBeenCalled();
    expect(onGoToPage).not.toHaveBeenCalled();
  });

  it("ArrowDown advances a page and prevents default", () => {
    const t = createKeydownTarget();
    const onGoToPage = vi.fn();

    render(
      <Harness
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 3}
        onGoToPage={onGoToPage}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault = vi.fn();
    listener({
      key: "ArrowDown",
      preventDefault,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);

    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(onGoToPage).toHaveBeenCalledWith(4);
  });

  it("ArrowUp decrements a page and prevents default", () => {
    const t = createKeydownTarget();
    const onGoToPage = vi.fn();

    render(
      <Harness
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 3}
        onGoToPage={onGoToPage}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault = vi.fn();
    listener({
      key: "ArrowUp",
      preventDefault,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);

    expect(preventDefault).toHaveBeenCalledTimes(1);
    expect(onGoToPage).toHaveBeenCalledWith(2);
  });

  it("Home/End jump to first/last page", () => {
    const t = createKeydownTarget();
    const onGoToPage = vi.fn();

    render(
      <Harness
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 5}
        onGoToPage={onGoToPage}
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
    expect(onGoToPage).toHaveBeenLastCalledWith(10);
  });

  it("does not navigate past first/last page", () => {
    const t = createKeydownTarget();
    const onGoToPage = vi.fn();

    render(
      <Harness
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 10}
        onGoToPage={onGoToPage}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault1 = vi.fn();
    listener({
      key: "ArrowDown",
      preventDefault: preventDefault1,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);
    expect(preventDefault1).not.toHaveBeenCalled();
    expect(onGoToPage).not.toHaveBeenCalled();

    onGoToPage.mockClear();
    const t2 = createKeydownTarget();
    render(
      <Harness
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 1}
        onGoToPage={onGoToPage}
        enabled={true}
        target={t2.target}
      />,
    );
    const listener2 = t2.getListener();
    const preventDefault2 = vi.fn();
    listener2({
      key: "ArrowUp",
      preventDefault: preventDefault2,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);
    expect(preventDefault2).not.toHaveBeenCalled();
    expect(onGoToPage).not.toHaveBeenCalled();
  });

  it("ignores unrelated keys", () => {
    const t = createKeydownTarget();
    const onGoToPage = vi.fn();

    render(
      <Harness
        readingDirection="vertical"
        totalPages={10}
        getCurrentPage={() => 5}
        onGoToPage={onGoToPage}
        enabled={true}
        target={t.target}
      />,
    );

    const listener = t.getListener();
    const preventDefault = vi.fn();
    listener({
      key: "KeyA",
      preventDefault,
      target: document.createElement("div"),
    } as unknown as KeyboardEvent);

    expect(preventDefault).not.toHaveBeenCalled();
    expect(onGoToPage).not.toHaveBeenCalled();
  });
});
