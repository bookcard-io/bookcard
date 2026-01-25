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

import { act, render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type {
  ImageDimensions,
  UseSpreadDetectionOptions,
  UseSpreadDetectionResult,
} from "./useSpreadDetection";
import { useSpreadDetection } from "./useSpreadDetection";

let last: UseSpreadDetectionResult | null = null;

function HookProbe(props: UseSpreadDetectionOptions) {
  last = useSpreadDetection(props);
  return <div data-testid="spread">{String(last.effectiveSpreadMode)}</div>;
}

describe("useSpreadDetection", () => {
  it("starts false and flips true when dimensions for current+next indicate spread", async () => {
    render(
      <HookProbe enabled bookKey="1:cbz" currentPage={1} totalPages={10} />,
    );

    expect(last?.effectiveSpreadMode).toBe(false);

    act(() => {
      last?.onPageDimensions(1, { width: 2000, height: 1000 });
      last?.onPageDimensions(2, { width: 1980, height: 1000 });
    });

    await waitFor(() => {
      expect(last?.effectiveSpreadMode).toBe(true);
    });
  });

  it("does not compute spreads when disabled", async () => {
    render(
      <HookProbe
        enabled={false}
        bookKey="1:cbz"
        currentPage={1}
        totalPages={10}
      />,
    );

    act(() => {
      last?.onPageDimensions(1, { width: 2000, height: 1000 });
      last?.onPageDimensions(2, { width: 1980, height: 1000 });
    });

    await new Promise((r) => setTimeout(r, 0));
    expect(last?.effectiveSpreadMode).toBe(false);
  });

  it("resets cached dimensions when bookKey changes", async () => {
    const { rerender } = render(
      <HookProbe enabled bookKey="1:cbz" currentPage={1} totalPages={10} />,
    );

    act(() => {
      last?.onPageDimensions(1, { width: 2000, height: 1000 });
      last?.onPageDimensions(2, { width: 1980, height: 1000 });
    });

    await waitFor(() => expect(last?.effectiveSpreadMode).toBe(true));

    rerender(
      <HookProbe enabled bookKey="999:cbz" currentPage={1} totalPages={10} />,
    );

    await waitFor(() => expect(last?.effectiveSpreadMode).toBe(false));
  });

  it("uses injected heuristic instead of default", async () => {
    const heuristic = vi.fn(
      (_d1: ImageDimensions, _d2: ImageDimensions) => true,
    );

    render(
      <HookProbe
        enabled
        bookKey="1:cbz"
        currentPage={1}
        totalPages={10}
        heuristic={heuristic}
      />,
    );

    act(() => {
      last?.onPageDimensions(1, { width: 10, height: 1000 }); // portrait-like
      last?.onPageDimensions(2, { width: 10, height: 1000 });
    });

    await waitFor(() => {
      expect(heuristic).toHaveBeenCalledTimes(1);
      expect(last?.effectiveSpreadMode).toBe(true);
    });
  });
});
