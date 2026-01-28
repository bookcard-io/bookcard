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
import { act, createRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SMOOTH_SCROLL_RESTORE_DELAY_MS } from "@/hooks/reading/comic/useSmoothScrollBehavior";
import {
  BaseVirtualizedComicView,
  type VirtualizedComicViewHandle,
} from "./BaseVirtualizedComicView";

const useVirtualizerMock = vi.fn();
vi.mock("@tanstack/react-virtual", () => ({
  useVirtualizer: (opts: unknown) => useVirtualizerMock(opts),
}));

vi.mock("./ComicPage", () => ({
  ComicPage: () => <div data-testid="comic-page" />,
}));

function makeVirtualizer() {
  return {
    getVirtualItems: () => [],
    getTotalSize: () => 1234,
    measureElement: vi.fn(),
    scrollToIndex: vi.fn(),
  };
}

describe("BaseVirtualizedComicView.scrollToPage", () => {
  afterEach(() => {
    vi.useRealTimers();
    useVirtualizerMock.mockReset();
  });

  it("clamps page and delegates to scrollToIndex (auto)", async () => {
    const v = makeVirtualizer();
    useVirtualizerMock.mockReturnValue(v);
    const setTimeoutSpy = vi.spyOn(window, "setTimeout");

    const ref = createRef<VirtualizedComicViewHandle>();
    const { container } = render(
      <BaseVirtualizedComicView
        ref={ref}
        bookId={1}
        format="cbz"
        totalPages={10}
        onPageChange={vi.fn()}
        config={{ estimatedPageHeight: 800, overscan: 1, enableSnap: true }}
      />,
    );

    if (!ref.current) {
      throw new Error("Expected ref to be set after render");
    }
    const el = container.querySelector("section");
    if (!el) throw new Error("Expected scroll container to be rendered");

    el.style.scrollBehavior = "auto";

    act(() => {
      ref.current?.scrollToPage(0, "auto");
      ref.current?.scrollToPage(999, "auto");
    });

    expect(v.scrollToIndex).toHaveBeenNthCalledWith(1, 0, { align: "start" });
    expect(v.scrollToIndex).toHaveBeenNthCalledWith(2, 9, { align: "start" });
    expect(el.style.scrollBehavior).toBe("auto");
    expect(setTimeoutSpy).not.toHaveBeenCalled();
    setTimeoutSpy.mockRestore();
  });

  it("temporarily applies smooth scroll via CSS and restores it", async () => {
    const v = makeVirtualizer();
    useVirtualizerMock.mockReturnValue(v);

    const ref = createRef<VirtualizedComicViewHandle>();
    const { container } = render(
      <BaseVirtualizedComicView
        ref={ref}
        bookId={1}
        format="cbz"
        totalPages={10}
        onPageChange={vi.fn()}
        config={{ estimatedPageHeight: 800, overscan: 1, enableSnap: true }}
      />,
    );

    if (!ref.current) {
      throw new Error("Expected ref to be set after render");
    }
    const el = container.querySelector("section");
    if (!el) throw new Error("Expected scroll container to be rendered");

    el.style.scrollBehavior = "auto";

    vi.useFakeTimers();
    act(() => {
      ref.current?.scrollToPage(2, "smooth");
    });

    expect(el.style.scrollBehavior).toBe("smooth");
    expect(v.scrollToIndex).toHaveBeenCalledWith(1, { align: "start" });

    act(() => {
      vi.advanceTimersByTime(SMOOTH_SCROLL_RESTORE_DELAY_MS);
    });
    expect(el.style.scrollBehavior).toBe("auto");
  });

  it("repeated smooth calls extend the restore window and restore the original value", async () => {
    const v = makeVirtualizer();
    useVirtualizerMock.mockReturnValue(v);

    vi.useFakeTimers();
    const clearTimeoutSpy = vi.spyOn(window, "clearTimeout");

    const ref = createRef<VirtualizedComicViewHandle>();
    const { container } = render(
      <BaseVirtualizedComicView
        ref={ref}
        bookId={1}
        format="cbz"
        totalPages={10}
        onPageChange={vi.fn()}
        config={{ estimatedPageHeight: 800, overscan: 1, enableSnap: true }}
      />,
    );

    if (!ref.current) {
      throw new Error("Expected ref to be set after render");
    }
    const el = container.querySelector("section");
    if (!el) throw new Error("Expected scroll container to be rendered");

    el.style.scrollBehavior = "auto";

    act(() => {
      ref.current?.scrollToPage(2, "smooth");
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    act(() => {
      vi.advanceTimersByTime(400);
      ref.current?.scrollToPage(3, "smooth");
    });

    expect(clearTimeoutSpy).toHaveBeenCalled();
    expect(el.style.scrollBehavior).toBe("smooth");

    act(() => {
      vi.advanceTimersByTime(799);
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(el.style.scrollBehavior).toBe("auto");

    clearTimeoutSpy.mockRestore();
  });

  it("clears pending restore timers on unmount", async () => {
    const v = makeVirtualizer();
    useVirtualizerMock.mockReturnValue(v);
    vi.useFakeTimers();
    const clearTimeoutSpy = vi.spyOn(window, "clearTimeout");

    const ref = createRef<VirtualizedComicViewHandle>();
    const { container, unmount } = render(
      <BaseVirtualizedComicView
        ref={ref}
        bookId={1}
        format="cbz"
        totalPages={10}
        onPageChange={vi.fn()}
        config={{ estimatedPageHeight: 800, overscan: 1, enableSnap: true }}
      />,
    );

    if (!ref.current) {
      throw new Error("Expected ref to be set after render");
    }
    const el = container.querySelector("section");
    if (!el) throw new Error("Expected scroll container to be rendered");

    el.style.scrollBehavior = "auto";

    act(() => {
      ref.current?.scrollToPage(2, "smooth");
    });
    expect(el.style.scrollBehavior).toBe("smooth");

    unmount();
    expect(clearTimeoutSpy).toHaveBeenCalled();
    // Element is unmounted, but this reference should still be restored.
    expect(el.style.scrollBehavior).toBe("auto");

    clearTimeoutSpy.mockRestore();
  });
});
