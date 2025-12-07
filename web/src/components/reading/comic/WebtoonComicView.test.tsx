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

import { useVirtualizer } from "@tanstack/react-virtual";
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { WebtoonComicView } from "./WebtoonComicView";

// Mock ComicPage
vi.mock("./ComicPage", () => ({
  ComicPage: ({ pageNumber }: { pageNumber: number }) => (
    <div data-testid="comic-page">Page {pageNumber}</div>
  ),
}));

// Mock virtualizer
vi.mock("@tanstack/react-virtual", async () => {
  const actual = await vi.importActual<
    typeof import("@tanstack/react-virtual")
  >("@tanstack/react-virtual");
  return {
    ...actual,
    useVirtualizer: vi.fn((options) => actual.useVirtualizer(options)),
  };
});

describe("WebtoonComicView", () => {
  const defaultProps = {
    bookId: 1,
    format: "cbz",
    totalPages: 10,
    onPageChange: vi.fn(),
    zoomLevel: 1.0,
  };

  it("renders without snapping classes", () => {
    const { container } = render(<WebtoonComicView {...defaultProps} />);

    // Should find the container by overflow classes
    const scrollContainer = container.querySelector(".overflow-y-auto");

    expect(scrollContainer).toBeInTheDocument();
    expect(scrollContainer).not.toHaveClass("snap-y");
    expect(scrollContainer).not.toHaveClass("snap-proximity");
    expect(scrollContainer).not.toHaveClass("snap-mandatory");
  });

  it("initializes virtualizer with overscan of 5", () => {
    render(<WebtoonComicView {...defaultProps} />);

    expect(useVirtualizer).toHaveBeenCalledWith(
      expect.objectContaining({
        overscan: 5,
        count: 10,
      }),
    );
  });
});
