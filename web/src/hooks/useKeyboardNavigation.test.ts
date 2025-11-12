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

import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useKeyboardNavigation } from "./useKeyboardNavigation";

describe("useKeyboardNavigation", () => {
  let onEscape: (() => void) | undefined;
  let onArrowLeft: (() => void) | undefined;
  let onArrowRight: (() => void) | undefined;

  beforeEach(() => {
    onEscape = vi.fn() as () => void;
    onArrowLeft = vi.fn() as () => void;
    onArrowRight = vi.fn() as () => void;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should call onEscape when Escape key is pressed", () => {
    renderHook(() =>
      useKeyboardNavigation({ onEscape, onArrowLeft, onArrowRight }),
    );

    const event = new KeyboardEvent("keydown", { key: "Escape" });
    document.dispatchEvent(event);

    expect(onEscape).toHaveBeenCalledTimes(1);
    expect(onArrowLeft).not.toHaveBeenCalled();
    expect(onArrowRight).not.toHaveBeenCalled();
  });

  it("should call onArrowLeft when ArrowLeft key is pressed", () => {
    renderHook(() =>
      useKeyboardNavigation({ onEscape, onArrowLeft, onArrowRight }),
    );

    const event = new KeyboardEvent("keydown", { key: "ArrowLeft" });
    document.dispatchEvent(event);

    expect(onArrowLeft).toHaveBeenCalledTimes(1);
    expect(onEscape).not.toHaveBeenCalled();
    expect(onArrowRight).not.toHaveBeenCalled();
  });

  it("should call onArrowRight when ArrowRight key is pressed", () => {
    renderHook(() =>
      useKeyboardNavigation({ onEscape, onArrowLeft, onArrowRight }),
    );

    const event = new KeyboardEvent("keydown", { key: "ArrowRight" });
    document.dispatchEvent(event);

    expect(onArrowRight).toHaveBeenCalledTimes(1);
    expect(onEscape).not.toHaveBeenCalled();
    expect(onArrowLeft).not.toHaveBeenCalled();
  });

  it("should not call callbacks when disabled", () => {
    renderHook(() =>
      useKeyboardNavigation({
        onEscape,
        onArrowLeft,
        onArrowRight,
        enabled: false,
      }),
    );

    const escapeEvent = new KeyboardEvent("keydown", { key: "Escape" });
    document.dispatchEvent(escapeEvent);

    expect(onEscape).not.toHaveBeenCalled();
  });

  it("should prevent default on key events", () => {
    renderHook(() =>
      useKeyboardNavigation({ onEscape, onArrowLeft, onArrowRight }),
    );

    const event = new KeyboardEvent("keydown", { key: "Escape" });
    const preventDefaultSpy = vi.spyOn(event, "preventDefault");
    document.dispatchEvent(event);

    expect(preventDefaultSpy).toHaveBeenCalled();
  });

  it("should handle partial callbacks", () => {
    renderHook(() => useKeyboardNavigation({ onEscape }));

    const escapeEvent = new KeyboardEvent("keydown", { key: "Escape" });
    document.dispatchEvent(escapeEvent);

    expect(onEscape).toHaveBeenCalledTimes(1);
  });

  it("should cleanup event listener on unmount", () => {
    const { unmount } = renderHook(() =>
      useKeyboardNavigation({ onEscape, onArrowLeft, onArrowRight }),
    );

    unmount();

    const event = new KeyboardEvent("keydown", { key: "Escape" });
    document.dispatchEvent(event);

    expect(onEscape).not.toHaveBeenCalled();
  });

  it("should not call onArrowLeft when callback is not provided", () => {
    renderHook(() => useKeyboardNavigation({ onEscape, onArrowRight }));

    const event = new KeyboardEvent("keydown", { key: "ArrowLeft" });
    document.dispatchEvent(event);

    expect(onArrowLeft).not.toHaveBeenCalled();
  });

  it("should not call onArrowRight when callback is not provided", () => {
    renderHook(() => useKeyboardNavigation({ onEscape, onArrowLeft }));

    const event = new KeyboardEvent("keydown", { key: "ArrowRight" });
    document.dispatchEvent(event);

    expect(onArrowRight).not.toHaveBeenCalled();
  });
});
