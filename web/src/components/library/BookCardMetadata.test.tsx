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

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BookCardMetadata } from "./BookCardMetadata";

describe("BookCardMetadata", () => {
  it("should render title and authors", () => {
    render(<BookCardMetadata title="The Shining" authors={["Stephen King"]} />);

    expect(screen.getByText("The Shining")).toBeDefined();
    expect(screen.getByText("Stephen King")).toBeDefined();
  });

  it("should show 'Unknown Author' when authors array is empty", () => {
    render(<BookCardMetadata title="Untitled" authors={[]} />);

    expect(screen.getByText("Unknown Author")).toBeDefined();
  });

  it("should join multiple authors with commas", () => {
    render(
      <BookCardMetadata
        title="Good Omens"
        authors={["Terry Pratchett", "Neil Gaiman"]}
      />,
    );

    expect(screen.getByText("Terry Pratchett, Neil Gaiman")).toBeDefined();
  });

  describe("library badge", () => {
    it("should not render badge when showLibraryBadge is false (default)", () => {
      render(
        <BookCardMetadata
          title="Dune"
          authors={["Frank Herbert"]}
          libraryName="Science Fiction"
        />,
      );

      expect(screen.queryByText("Science Fiction")).toBeNull();
    });

    it("should not render badge when showLibraryBadge is true but libraryName is null", () => {
      render(
        <BookCardMetadata
          title="Dune"
          authors={["Frank Herbert"]}
          showLibraryBadge={true}
          libraryName={null}
        />,
      );

      // Title and author should render, but no badge
      expect(screen.getByText("Dune")).toBeDefined();
      expect(screen.getByText("Frank Herbert")).toBeDefined();
      // No extra span with a library name
      const spans = document.querySelectorAll("span");
      for (const span of spans) {
        expect(span.textContent).not.toBe("");
      }
    });

    it("should not render badge when showLibraryBadge is true but libraryName is undefined", () => {
      render(
        <BookCardMetadata
          title="Dune"
          authors={["Frank Herbert"]}
          showLibraryBadge={true}
        />,
      );

      expect(screen.getByText("Dune")).toBeDefined();
    });

    it("should render badge when showLibraryBadge is true and libraryName is provided", () => {
      render(
        <BookCardMetadata
          title="The Shining"
          authors={["Stephen King"]}
          showLibraryBadge={true}
          libraryName="Horror Collection"
        />,
      );

      expect(screen.getByText("The Shining")).toBeDefined();
      expect(screen.getByText("Stephen King")).toBeDefined();
      expect(screen.getByText("Horror Collection")).toBeDefined();
    });

    it("should render badge with truncation class", () => {
      render(
        <BookCardMetadata
          title="Test"
          authors={["Author"]}
          showLibraryBadge={true}
          libraryName="My Very Long Library Name That Should Be Truncated"
        />,
      );

      const badge = screen.getByText(
        "My Very Long Library Name That Should Be Truncated",
      );
      expect(badge.tagName).toBe("SPAN");
      expect(badge.classList.contains("truncate")).toBe(true);
    });

    it("should not render badge when showLibraryBadge is false even with libraryName", () => {
      render(
        <BookCardMetadata
          title="Test"
          authors={["Author"]}
          showLibraryBadge={false}
          libraryName="Comics"
        />,
      );

      expect(screen.queryByText("Comics")).toBeNull();
    });
  });
});
