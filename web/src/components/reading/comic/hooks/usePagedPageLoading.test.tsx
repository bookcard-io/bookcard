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
import { describe, expect, it } from "vitest";
import type {
  UsePagedPageLoadingOptions,
  UsePagedPageLoadingResult,
} from "./usePagedPageLoading";
import { usePagedPageLoading } from "./usePagedPageLoading";

let last: UsePagedPageLoadingResult | null = null;

function HookProbe(props: UsePagedPageLoadingOptions) {
  last = usePagedPageLoading(props);
  return <div data-testid="loading">{String(last.isLoading)}</div>;
}

describe("usePagedPageLoading", () => {
  it("starts loading until all visible pages have loaded", async () => {
    render(<HookProbe bookKey="1:cbz" visiblePages={[1, 2]} />);
    expect(last?.isLoading).toBe(true);

    act(() => last?.onPageLoad(1));
    await new Promise((r) => setTimeout(r, 0));
    expect(last?.isLoading).toBe(true);

    act(() => last?.onPageLoad(2));
    await waitFor(() => expect(last?.isLoading).toBe(false));
  });

  it("returns to loading if visible pages change to include an unloaded page", async () => {
    const { rerender } = render(
      <HookProbe bookKey="1:cbz" visiblePages={[1]} />,
    );

    act(() => last?.onPageLoad(1));
    await waitFor(() => expect(last?.isLoading).toBe(false));

    rerender(<HookProbe bookKey="1:cbz" visiblePages={[1, 2]} />);
    await waitFor(() => expect(last?.isLoading).toBe(true));
  });

  it("resets loading state when bookKey changes", async () => {
    const { rerender } = render(
      <HookProbe bookKey="1:cbz" visiblePages={[1]} />,
    );

    act(() => last?.onPageLoad(1));
    await waitFor(() => expect(last?.isLoading).toBe(false));

    rerender(<HookProbe bookKey="999:cbz" visiblePages={[1]} />);
    await waitFor(() => expect(last?.isLoading).toBe(true));
  });
});
