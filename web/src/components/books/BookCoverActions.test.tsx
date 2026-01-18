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

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createQueryClientWrapper } from "@/hooks/test-utils";
import type { Book } from "@/types/book";
import { BookCoverActions } from "./BookCoverActions";

describe("BookCoverActions", () => {
  const mockBook: Book = {
    id: 1,
    title: "Test Book",
    authors: [],
    tags: [],
    identifiers: [],
    languages: [],
    language_ids: [],
    formats: [],
    has_cover: false,
    uuid: "uuid",
    author_sort: null,
    title_sort: null,
    pubdate: null,
    timestamp: null,
    series: null,
    series_id: null,
    series_index: null,
    isbn: null,
    description: null,
    publisher: null,
    publisher_id: null,
    rating: null,
    rating_id: null,
    reading_summary: null,
    thumbnail_url: null,
  };

  const Wrapper = createQueryClientWrapper();

  beforeEach(() => {
    // Mock fetch to return an admin user so buttons are enabled
    globalThis.fetch = vi.fn((url: string) => {
      if (url === "/api/auth/me") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              id: 1,
              username: "testuser",
              email: "test@example.com",
              is_admin: true,
              ereader_devices: [],
              roles: [],
            }),
        } as Response);
      }
      if (url === "/api/auth/settings") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ settings: {} }),
        } as Response);
      }
      return Promise.reject(new Error(`Unexpected fetch to ${url}`));
    }) as typeof fetch;
  });

  it("should render action buttons", () => {
    render(
      <Wrapper>
        <BookCoverActions
          book={mockBook}
          isUrlInputVisible={false}
          onSetFromUrlClick={vi.fn()}
        />
      </Wrapper>,
    );

    expect(screen.getByText("Browse for a cover")).toBeDefined();
    expect(screen.getByText("Set cover from URL")).toBeDefined();
    expect(screen.getByText("Download cover")).toBeDefined();
    expect(screen.getByText("Generate cover")).toBeDefined();
  });

  it("should trigger file input when browse button is clicked", async () => {
    const onFileSelect = vi.fn();
    render(
      <Wrapper>
        <BookCoverActions
          book={mockBook}
          isUrlInputVisible={false}
          onSetFromUrlClick={vi.fn()}
          onFileSelect={onFileSelect}
        />
      </Wrapper>,
    );

    // Wait for user context to load and button to be enabled
    const browseButton = (await waitFor(() => {
      const button = screen.getByText("Browse for a cover").closest("button");
      expect(button).toBeTruthy();
      expect(button).not.toBeDisabled();
      return button;
    })) as HTMLButtonElement;

    const fileInput = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    expect(fileInput).toBeTruthy();

    // Spy on file input click
    const clickSpy = vi.spyOn(fileInput, "click");

    fireEvent.click(browseButton);

    expect(clickSpy).toHaveBeenCalled();
  });

  it("should call onFileSelect when file is selected", async () => {
    const onFileSelect = vi.fn();
    render(
      <Wrapper>
        <BookCoverActions
          book={mockBook}
          isUrlInputVisible={false}
          onSetFromUrlClick={vi.fn()}
          onFileSelect={onFileSelect}
        />
      </Wrapper>,
    );

    // Wait for user context to load and component to render
    await waitFor(() => {
      const fileInput = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;
      expect(fileInput).toBeTruthy();
    });

    const fileInput = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;
    const file = new File(["dummy content"], "cover.jpg", {
      type: "image/jpeg",
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(onFileSelect).toHaveBeenCalledWith(file);
    // Check that input value is cleared
    expect(fileInput.value).toBe("");
  });

  it("should display loading state when isLoading is true", () => {
    render(
      <Wrapper>
        <BookCoverActions
          book={mockBook}
          isUrlInputVisible={false}
          onSetFromUrlClick={vi.fn()}
          isLoading={true}
        />
      </Wrapper>,
    );

    const browseButton = screen
      .getByText("Browse for a cover")
      .closest("button");
    const urlButton = screen.getByText("Set cover from URL").closest("button");

    expect(browseButton).toBeDisabled();
    expect(urlButton).toBeDisabled();
  });
});
