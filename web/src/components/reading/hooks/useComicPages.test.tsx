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

import { render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useComicPages } from "./useComicPages";

function HookProbe(props: {
  bookId: number;
  format: string;
  enabled?: boolean;
  includeDimensions?: boolean;
}) {
  useComicPages(props);
  return null;
}

describe("useComicPages", () => {
  it("does not request include_dimensions by default", async () => {
    const fetchMock = vi.fn(async (_input: RequestInfo | URL) => {
      return new Response(JSON.stringify([]), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<HookProbe bookId={123} format="cbz" enabled />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const url = String(fetchMock.mock.calls[0]?.[0]);
    expect(url).toContain("/api/comic/123/pages?");
    expect(url).toContain("file_format=cbz");
    expect(url).not.toContain("include_dimensions=true");
  });

  it("requests include_dimensions=true when includeDimensions is enabled", async () => {
    const fetchMock = vi.fn(async (_input: RequestInfo | URL) => {
      return new Response(JSON.stringify([]), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <HookProbe bookId={123} format="cbz" enabled includeDimensions={true} />,
    );

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const url = String(fetchMock.mock.calls[0]?.[0]);
    expect(url).toContain("file_format=cbz");
    expect(url).toContain("include_dimensions=true");
  });

  it("does not fetch when disabled", async () => {
    const fetchMock = vi.fn(async (_input: RequestInfo | URL) => {
      return new Response(JSON.stringify([]), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<HookProbe bookId={123} format="cbz" enabled={false} />);

    // Give the effect a tick; should still be unused.
    await new Promise((r) => setTimeout(r, 0));
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
