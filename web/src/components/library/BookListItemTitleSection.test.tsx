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
import { describe, expect, it, vi } from "vitest";
import type { Book } from "@/types/book";
import { BookListItemTitleSection } from "./BookListItemTitleSection";

function makeBook(overrides: Partial<Book> = {}): Book {
  return {
    id: 1,
    title: "The Shining",
    authors: ["Stephen King"],
    author_sort: "King, Stephen",
    title_sort: "Shining, The",
    pubdate: null,
    timestamp: null,
    series: null,
    series_id: null,
    series_index: null,
    isbn: null,
    uuid: "test-uuid",
    thumbnail_url: null,
    has_cover: false,
    ...overrides,
  };
}

describe("BookListItemTitleSection", () => {
  it("should render title and authors", () => {
    render(
      <BookListItemTitleSection
        book={makeBook()}
        selected={false}
        onClick={vi.fn()}
      />,
    );

    expect(screen.getByText("The Shining")).toBeDefined();
    expect(screen.getByText("Stephen King")).toBeDefined();
  });

  describe("library badge", () => {
    it("should not render badge when showLibraryBadge is false (default)", () => {
      render(
        <BookListItemTitleSection
          book={makeBook({ library_name: "Horror" })}
          selected={false}
          onClick={vi.fn()}
        />,
      );

      expect(screen.queryByText("Horror")).toBeNull();
    });

    it("should not render badge when showLibraryBadge is true but library_name is null", () => {
      render(
        <BookListItemTitleSection
          book={makeBook({ library_name: null })}
          selected={false}
          onClick={vi.fn()}
          showLibraryBadge={true}
        />,
      );

      expect(screen.getByText("The Shining")).toBeDefined();
      // No badge rendered
      const spans = document.querySelectorAll("span.truncate");
      expect(spans.length).toBe(0);
    });

    it("should not render badge when showLibraryBadge is true but library_name is undefined", () => {
      render(
        <BookListItemTitleSection
          book={makeBook()}
          selected={false}
          onClick={vi.fn()}
          showLibraryBadge={true}
        />,
      );

      expect(screen.getByText("The Shining")).toBeDefined();
    });

    it("should render badge when showLibraryBadge is true and library_name is set", () => {
      render(
        <BookListItemTitleSection
          book={makeBook({ library_name: "Comics" })}
          selected={false}
          onClick={vi.fn()}
          showLibraryBadge={true}
        />,
      );

      expect(screen.getByText("The Shining")).toBeDefined();
      expect(screen.getByText("Stephen King")).toBeDefined();
      expect(screen.getByText("Comics")).toBeDefined();
    });

    it("should render badge with truncation class", () => {
      render(
        <BookListItemTitleSection
          book={makeBook({ library_name: "My Library" })}
          selected={false}
          onClick={vi.fn()}
          showLibraryBadge={true}
        />,
      );

      const badge = screen.getByText("My Library");
      expect(badge.tagName).toBe("SPAN");
      expect(badge.classList.contains("truncate")).toBe(true);
    });
  });
});
