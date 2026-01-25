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
import type { RefObject } from "react";
import { describe, expect, it } from "vitest";
import { useZoomScrollCenter } from "./useZoomScrollCenter";

function HookProbe(props: {
  zoomLevel: number;
  containerRef: RefObject<HTMLElement | null>;
}) {
  useZoomScrollCenter({
    containerRef: props.containerRef,
    zoomLevel: props.zoomLevel,
  });
  return null;
}

describe("useZoomScrollCenter", () => {
  it("adjusts scroll offsets to preserve visual center when zoom changes", () => {
    const el = document.createElement("div");
    el.style.width = "200px";
    el.style.height = "100px";
    el.style.overflow = "scroll";
    const inner = document.createElement("div");
    inner.style.width = "2000px";
    inner.style.height = "2000px";
    el.appendChild(inner);
    document.body.appendChild(el);

    const ref = { current: el } as RefObject<HTMLElement | null>;

    el.scrollLeft = 100;
    el.scrollTop = 50;
    expect(el.scrollLeft).toBe(100);
    expect(el.scrollTop).toBe(50);

    const { rerender } = render(<HookProbe zoomLevel={1} containerRef={ref} />);
    rerender(<HookProbe zoomLevel={2} containerRef={ref} />);

    const width = el.clientWidth;
    const height = el.clientHeight;
    const expectedLeft = (100 + width / 2) * 2 - width / 2;
    const expectedTop = (50 + height / 2) * 2 - height / 2;

    expect(el.scrollLeft).toBe(expectedLeft);
    expect(el.scrollTop).toBe(expectedTop);

    el.remove();
  });

  it("does not adjust when zoom changes are below threshold", () => {
    const el = document.createElement("div");
    el.style.width = "200px";
    el.style.height = "100px";
    el.style.overflow = "scroll";
    const inner = document.createElement("div");
    inner.style.width = "2000px";
    inner.style.height = "2000px";
    el.appendChild(inner);
    document.body.appendChild(el);

    const ref = { current: el } as RefObject<HTMLElement | null>;

    el.scrollLeft = 100;
    el.scrollTop = 50;
    expect(el.scrollLeft).toBe(100);
    expect(el.scrollTop).toBe(50);

    const { rerender } = render(<HookProbe zoomLevel={1} containerRef={ref} />);
    rerender(<HookProbe zoomLevel={1.0005} containerRef={ref} />);

    expect(el.scrollLeft).toBe(100);
    expect(el.scrollTop).toBe(50);

    el.remove();
  });
});
