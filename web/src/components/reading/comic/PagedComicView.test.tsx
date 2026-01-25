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
import { PagedComicView } from "./PagedComicView";

type MockComicPageProps = {
  pageNumber: number;
  onDimensions?: (d: { width: number; height: number }) => void;
  className?: string;
};

const seenProps: MockComicPageProps[] = [];

vi.mock("./ComicPage", () => ({
  ComicPage: (props: MockComicPageProps) => {
    seenProps.push(props);
    return (
      <div data-testid={`comic-page-${props.pageNumber}`}>
        {props.className ?? ""}
      </div>
    );
  },
}));

describe("PagedComicView", () => {
  const baseProps = {
    bookId: 1,
    format: "cbz",
    currentPage: 1,
    totalPages: 10,
    onPageChange: vi.fn(),
    canGoNext: true,
    canGoPrevious: false,
    onNext: vi.fn(),
    onPrevious: vi.fn(),
    spreadMode: true,
    readingDirection: "ltr" as const,
    zoomLevel: 1.0,
  };

  it("preloads adjacent pages using overscan even before spread is detected", () => {
    seenProps.length = 0;
    render(<PagedComicView {...baseProps} />);

    const renderedPageNumbers = new Set(seenProps.map((p) => p.pageNumber));
    // With spreadMode=true, current=1, overscan=3 => cache includes 1..5.
    expect(renderedPageNumbers).toEqual(new Set([1, 2, 3, 4, 5]));
  });

  it("switches to two-page display once dimensions for current+next indicate a spread", async () => {
    seenProps.length = 0;
    render(<PagedComicView {...baseProps} />);

    const p1 = seenProps.find((p) => p.pageNumber === 1);
    const p2 = seenProps.find((p) => p.pageNumber === 2);
    expect(p1?.onDimensions).toBeTypeOf("function");
    expect(p2?.onDimensions).toBeTypeOf("function");

    // landscape + similar dimensions
    p1?.onDimensions?.({ width: 2000, height: 1000 });
    p2?.onDimensions?.({ width: 1980, height: 1000 });

    await waitFor(() => {
      const page1El = document.querySelector(
        '[data-testid="comic-page-1"]',
      ) as HTMLElement | null;
      const page2El = document.querySelector(
        '[data-testid="comic-page-2"]',
      ) as HTMLElement | null;

      expect(page1El).toBeTruthy();
      expect(page2El).toBeTruthy();
      expect(page1El?.textContent).toContain("w-1/2");
      expect(page2El?.textContent).toContain("w-1/2");
    });
  });

  it("clears cached dimensions when switching books", async () => {
    seenProps.length = 0;
    const { rerender } = render(<PagedComicView {...baseProps} />);

    const p1 = seenProps.find((p) => p.pageNumber === 1);
    const p2 = seenProps.find((p) => p.pageNumber === 2);
    p1?.onDimensions?.({ width: 2000, height: 1000 });
    p2?.onDimensions?.({ width: 1980, height: 1000 });

    await waitFor(() => {
      const page2El = document.querySelector(
        '[data-testid="comic-page-2"]',
      ) as HTMLElement | null;
      expect(page2El?.textContent).toContain("w-1/2");
    });

    // Switch to a different book.
    rerender(<PagedComicView {...baseProps} bookId={999} />);

    await waitFor(() => {
      const page2El = document.querySelector(
        '[data-testid="comic-page-2"]',
      ) as HTMLElement | null;
      // Should not be in spread until dimensions are re-learned.
      expect(page2El?.textContent).not.toContain("w-1/2");
    });
  });
});
