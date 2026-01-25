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
import type { GetPreloadPages, PreloadPagesContext } from "./usePreloadPages";
import { defaultGetPreloadPages, usePreloadPages } from "./usePreloadPages";

function HookProbe(props: {
  ctx: PreloadPagesContext;
  getPreloadPages?: GetPreloadPages;
}) {
  const pages = usePreloadPages(props.ctx, props.getPreloadPages);
  return <div data-testid="pages">{pages.join(",")}</div>;
}

describe("defaultGetPreloadPages", () => {
  it("includes current page and overscan before/after", () => {
    const pages = defaultGetPreloadPages({
      currentPage: 5,
      totalPages: 10,
      overscan: 2,
      spreadMode: false,
    });
    expect(pages).toEqual([3, 4, 5, 6, 7]);
  });

  it("warms adjacent page when spreadMode=true (even before spread detected)", () => {
    const pages = defaultGetPreloadPages({
      currentPage: 1,
      totalPages: 10,
      overscan: 3,
      spreadMode: true,
    });
    // matches PagedComicView expectation: 1..5
    expect(pages).toEqual([1, 2, 3, 4, 5]);
  });

  it("respects bounds near start/end", () => {
    expect(
      defaultGetPreloadPages({
        currentPage: 1,
        totalPages: 3,
        overscan: 10,
        spreadMode: false,
      }),
    ).toEqual([1, 2, 3]);

    expect(
      defaultGetPreloadPages({
        currentPage: 3,
        totalPages: 3,
        overscan: 10,
        spreadMode: true,
      }),
    ).toEqual([1, 2, 3]);
  });
});

describe("usePreloadPages", () => {
  it("does not re-run policy when ctx object identity changes but values are the same", () => {
    const policy = vi.fn(defaultGetPreloadPages);

    const baseCtx = {
      currentPage: 5,
      totalPages: 10,
      overscan: 2,
      spreadMode: false,
    } satisfies PreloadPagesContext;

    const { rerender } = render(
      <HookProbe ctx={baseCtx} getPreloadPages={policy} />,
    );
    expect(policy).toHaveBeenCalledTimes(1);

    // New object, same values.
    rerender(<HookProbe ctx={{ ...baseCtx }} getPreloadPages={policy} />);

    expect(policy).toHaveBeenCalledTimes(1);
  });

  it("re-runs policy when dependencies change", () => {
    const policy = vi.fn(defaultGetPreloadPages);

    const { rerender } = render(
      <HookProbe
        ctx={{ currentPage: 1, totalPages: 10, overscan: 3, spreadMode: true }}
        getPreloadPages={policy}
      />,
    );
    expect(policy).toHaveBeenCalledTimes(1);

    rerender(
      <HookProbe
        ctx={{ currentPage: 2, totalPages: 10, overscan: 3, spreadMode: true }}
        getPreloadPages={policy}
      />,
    );
    expect(policy).toHaveBeenCalledTimes(2);
  });
});
