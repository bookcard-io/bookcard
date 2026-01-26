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

import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Book } from "@/types/book";
import { MoreFromSameFlyoutMenu } from "./MoreFromSameFlyoutMenu";

const showDanger = vi.fn();

vi.mock("@/contexts/GlobalMessageContext", () => ({
  useGlobalMessages: () => ({
    showDanger,
    showInfo: vi.fn(),
    showSuccess: vi.fn(),
    showWarning: vi.fn(),
  }),
}));

// Make flyout positioning deterministic
vi.mock("@/hooks/useFlyoutPosition", () => ({
  useFlyoutPosition: () => ({
    position: { x: 0, y: 0 },
    direction: "right",
    menuRef: { current: null },
  }),
}));

vi.mock("@/hooks/useFlyoutIntent", () => ({
  useFlyoutIntent: () => {},
}));

const apply = vi.fn(async () => {});

vi.mock("@/hooks/useMoreFromSameFilters", () => ({
  useMoreFromSameFilters: () => ({
    canApplyAuthor: true,
    canApplySeries: true,
    canApplyGenre: true,
    canApplyPublisher: true,
    isGenreLookupLoading: false,
    genreLookupError: null,
    apply,
  }),
}));

function makeBook(overrides: Partial<Book> = {}): Book {
  return {
    id: 1,
    title: "Book",
    authors: ["Author Name"],
    author_ids: [123],
    author_sort: null,
    title_sort: null,
    pubdate: null,
    timestamp: null,
    series: "Series Name",
    series_id: 42,
    series_index: null,
    isbn: null,
    uuid: "uuid",
    thumbnail_url: null,
    has_cover: false,
    tags: ["Fiction"],
    tag_ids: [55],
    publisher: "Publisher Name",
    publisher_id: 7,
    ...overrides,
  };
}

describe("MoreFromSameFlyoutMenu", () => {
  it("should render items and call apply+close on click", async () => {
    const onClose = vi.fn();
    const onSuccess = vi.fn();
    const parentItemRef = { current: document.createElement("div") };

    render(
      <MoreFromSameFlyoutMenu
        isOpen
        parentItemRef={parentItemRef}
        book={makeBook()}
        onClose={onClose}
        onSuccess={onSuccess}
      />,
    );

    // mounted effect
    await act(async () => {});

    fireEvent.click(screen.getByRole("menuitem", { name: /author/i }));
    expect(apply).toHaveBeenCalledWith("author");

    // applyAndClose closes after promise resolves
    await act(async () => {});
    expect(onClose).toHaveBeenCalled();
    expect(onSuccess).toHaveBeenCalled();
  });

  it("should show error via showDanger if apply fails", async () => {
    apply.mockRejectedValueOnce(new Error("boom"));

    const onClose = vi.fn();
    const parentItemRef = { current: document.createElement("div") };

    render(
      <MoreFromSameFlyoutMenu
        isOpen
        parentItemRef={parentItemRef}
        book={makeBook()}
        onClose={onClose}
      />,
    );

    await act(async () => {});

    fireEvent.click(screen.getByRole("menuitem", { name: /publisher/i }));
    await act(async () => {});

    expect(showDanger).toHaveBeenCalledWith("boom");
    // error path does not close menu
    expect(onClose).not.toHaveBeenCalled();
  });
});
