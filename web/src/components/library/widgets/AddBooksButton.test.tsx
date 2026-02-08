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
import { createRef } from "react";
import { describe, expect, it, vi } from "vitest";
import type { Library } from "@/contexts/ActiveLibraryContext";
import { AddBooksButton } from "./AddBooksButton";

function makeLibrary(id: number, name: string, isActive = false): Library {
  return {
    id,
    name,
    calibre_db_path: `/path/${name}`,
    calibre_db_file: "metadata.db",
    calibre_uuid: null,
    use_split_library: false,
    split_library_dir: null,
    auto_reconnect: false,
    is_active: isActive,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  };
}

const comicsLibrary = makeLibrary(1, "Comics", true);
const literatureLibrary = makeLibrary(2, "Literature");

// Mock useUser
vi.mock("@/contexts/UserContext", () => ({
  useUser: vi.fn(() => ({
    user: { id: 1, username: "test" },
    isLoading: false,
    error: null,
    refresh: vi.fn(),
    refreshTimestamp: 0,
    updateUser: vi.fn(),
    profilePictureUrl: null,
    canPerformAction: vi.fn(() => true),
  })),
}));

// Mock useActiveLibrary
vi.mock("@/contexts/ActiveLibraryContext", () => ({
  useActiveLibrary: vi.fn(),
}));

import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";

function setupMock(overrides: Partial<ReturnType<typeof useActiveLibrary>>) {
  vi.mocked(useActiveLibrary).mockReturnValue({
    activeLibrary: comicsLibrary,
    isLoading: false,
    refresh: vi.fn(),
    visibleLibraries: [comicsLibrary, literatureLibrary],
    selectedLibraryId: null,
    setSelectedLibraryId: vi.fn(),
    ...overrides,
  });
}

function renderButton() {
  const ref = createRef<HTMLInputElement>();
  return render(
    <AddBooksButton
      fileInputRef={ref}
      onFileChange={vi.fn()}
      accept=".epub,.pdf"
    />,
  );
}

describe("AddBooksButton", () => {
  describe("library awareness indicator", () => {
    it("should not show indicator when selectedLibraryId is null (All Libraries)", () => {
      setupMock({
        selectedLibraryId: null,
        activeLibrary: comicsLibrary,
        visibleLibraries: [comicsLibrary, literatureLibrary],
      });
      renderButton();

      expect(screen.queryByText(/Adding to/)).toBeNull();
    });

    it("should not show indicator when viewing the active library", () => {
      setupMock({
        selectedLibraryId: 1, // Same as activeLibrary.id
        activeLibrary: comicsLibrary,
        visibleLibraries: [comicsLibrary, literatureLibrary],
      });
      renderButton();

      expect(screen.queryByText(/Adding to/)).toBeNull();
    });

    it("should show indicator when viewing a different library than active", () => {
      setupMock({
        selectedLibraryId: 2, // Literature, not Comics (active)
        activeLibrary: comicsLibrary,
        visibleLibraries: [comicsLibrary, literatureLibrary],
      });
      renderButton();

      expect(screen.getByText("Adding to Comics")).toBeDefined();
    });

    it("should include active library name in title attribute", () => {
      setupMock({
        selectedLibraryId: 2,
        activeLibrary: comicsLibrary,
        visibleLibraries: [comicsLibrary, literatureLibrary],
      });
      renderButton();

      const indicator = screen.getByText("Adding to Comics");
      expect(indicator.getAttribute("title")).toBe(
        "Books will be added to Comics",
      );
    });

    it("should not show indicator when only one visible library", () => {
      setupMock({
        selectedLibraryId: 1,
        activeLibrary: comicsLibrary,
        visibleLibraries: [comicsLibrary],
      });
      renderButton();

      expect(screen.queryByText(/Adding to/)).toBeNull();
    });

    it("should not show indicator when activeLibrary is null", () => {
      setupMock({
        selectedLibraryId: 2,
        activeLibrary: null,
        visibleLibraries: [comicsLibrary, literatureLibrary],
      });
      renderButton();

      expect(screen.queryByText(/Adding to/)).toBeNull();
    });

    it("should render the Add Books button text", () => {
      setupMock({
        selectedLibraryId: null,
        activeLibrary: comicsLibrary,
        visibleLibraries: [comicsLibrary, literatureLibrary],
      });
      renderButton();

      expect(screen.getByText("Add Books")).toBeDefined();
    });

    it("should show Uploading text when isUploading is true", () => {
      setupMock({
        selectedLibraryId: null,
        activeLibrary: comicsLibrary,
        visibleLibraries: [],
      });
      const ref = createRef<HTMLInputElement>();
      render(
        <AddBooksButton
          fileInputRef={ref}
          onFileChange={vi.fn()}
          accept=".epub"
          isUploading={true}
        />,
      );

      expect(screen.getByText("Uploading...")).toBeDefined();
    });
  });
});
