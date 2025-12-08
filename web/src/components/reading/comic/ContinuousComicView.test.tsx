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
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ContinuousComicView } from "./ContinuousComicView";

// Mock ComicPage to avoid rendering children and focus on container logic
vi.mock("./ComicPage", () => ({
  ComicPage: ({ pageNumber }: { pageNumber: number }) => (
    <div data-testid="comic-page">Page {pageNumber}</div>
  ),
}));

// Mock virtualizer to inspect options
vi.mock("@tanstack/react-virtual", async () => {
  const actual = await vi.importActual<
    typeof import("@tanstack/react-virtual")
  >("@tanstack/react-virtual");
  return {
    ...actual,
    useVirtualizer: vi.fn((options) => actual.useVirtualizer(options)),
  };
});

describe("ContinuousComicView", () => {
  const defaultProps = {
    bookId: 1,
    format: "cbz",
    totalPages: 10,
    onPageChange: vi.fn(),
    zoomLevel: 1.0,
  };

  it("renders with correct snapping classes", () => {
    const { container } = render(<ContinuousComicView {...defaultProps} />);
    const scrollContainer = container.querySelector(
      ".snap-y.snap-mandatory.overflow-y-auto",
    );

    expect(scrollContainer).toBeInTheDocument();
    expect(scrollContainer).toHaveClass("snap-y");
    expect(scrollContainer).toHaveClass("snap-mandatory");
  });

  it("renders pages with snap-start class", () => {
    render(<ContinuousComicView {...defaultProps} />);

    // Since it's virtualized, we might only see a few pages
    // We can inspect the wrapper of the comic page
    const pageWrappers = screen
      .getAllByTestId("comic-page")
      .map((page) => page.parentElement);

    expect(pageWrappers.length).toBeGreaterThan(0);
    pageWrappers.forEach((wrapper) => {
      expect(wrapper).toHaveClass("snap-start");
    });
  });

  it("initializes virtualizer with default overscan of 3", () => {
    render(<ContinuousComicView {...defaultProps} />);

    expect(useVirtualizer).toHaveBeenCalledWith(
      expect.objectContaining({
        overscan: 3,
        count: 10,
      }),
    );
  });

  it("respects custom configuration for overscan", () => {
    render(
      <ContinuousComicView
        {...defaultProps}
        config={{ overscan: 10, estimatedPageHeight: 500 }}
      />,
    );

    expect(useVirtualizer).toHaveBeenCalledWith(
      expect.objectContaining({
        overscan: 10,
        estimateSize: expect.any(Function),
      }),
    );
  });
});
