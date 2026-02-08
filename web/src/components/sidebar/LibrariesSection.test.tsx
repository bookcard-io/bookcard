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

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Library } from "@/contexts/ActiveLibraryContext";
import { LibrariesSection } from "./LibrariesSection";

const mockSetSelectedLibraryId = vi.fn();

function makeLibrary(id: number, name: string, isActive = false): Library {
  return {
    id,
    name,
    calibre_db_path: `/path/to/${name.toLowerCase()}`,
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
const textbooksLibrary = makeLibrary(3, "Textbooks");

vi.mock("@/contexts/ActiveLibraryContext", () => ({
  useActiveLibrary: vi.fn(),
}));

// Import mock after vi.mock so we can control return values
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";

function setupMock(overrides: Partial<ReturnType<typeof useActiveLibrary>>) {
  vi.mocked(useActiveLibrary).mockReturnValue({
    activeLibrary: comicsLibrary,
    isLoading: false,
    refresh: vi.fn(),
    visibleLibraries: [comicsLibrary, literatureLibrary],
    selectedLibraryId: null,
    setSelectedLibraryId: mockSetSelectedLibraryId,
    ...overrides,
  });
}

describe("LibrariesSection", () => {
  it("should not render when only one visible library", () => {
    setupMock({ visibleLibraries: [comicsLibrary] });
    const { container } = render(<LibrariesSection isCollapsed={false} />);
    expect(container.innerHTML).toBe("");
  });

  it("should not render when no visible libraries", () => {
    setupMock({ visibleLibraries: [] });
    const { container } = render(<LibrariesSection isCollapsed={false} />);
    expect(container.innerHTML).toBe("");
  });

  it("should render section header with LIBRARIES text", () => {
    setupMock({});
    render(<LibrariesSection isCollapsed={false} />);
    expect(screen.getByText("LIBRARIES")).toBeDefined();
  });

  it("should hide header text when collapsed", () => {
    setupMock({});
    render(<LibrariesSection isCollapsed={true} />);
    expect(screen.queryByText("LIBRARIES")).toBeNull();
  });

  it("should render 'All Libraries' option", () => {
    setupMock({});
    render(<LibrariesSection isCollapsed={false} />);
    expect(screen.getByText("All Libraries")).toBeDefined();
  });

  it("should render each visible library by name", () => {
    setupMock({
      visibleLibraries: [comicsLibrary, literatureLibrary, textbooksLibrary],
    });
    render(<LibrariesSection isCollapsed={false} />);

    expect(screen.getByText("Comics")).toBeDefined();
    expect(screen.getByText("Literature")).toBeDefined();
    expect(screen.getByText("Textbooks")).toBeDefined();
  });

  it("should hide library list when collapsed", () => {
    setupMock({});
    render(<LibrariesSection isCollapsed={true} />);
    expect(screen.queryByText("All Libraries")).toBeNull();
    expect(screen.queryByText("Comics")).toBeNull();
  });

  it("should mark 'All Libraries' as active when selectedLibraryId is null", () => {
    setupMock({ selectedLibraryId: null });
    render(<LibrariesSection isCollapsed={false} />);

    // "All Libraries" button should have active styling
    const allButton = screen.getByText("All Libraries").closest("button");
    expect(allButton?.className).toContain("bg-");
  });

  it("should call setSelectedLibraryId(null) when 'All Libraries' is clicked", () => {
    setupMock({ selectedLibraryId: 1 });
    render(<LibrariesSection isCollapsed={false} />);

    fireEvent.click(screen.getByText("All Libraries"));
    expect(mockSetSelectedLibraryId).toHaveBeenCalledWith(null);
  });

  it("should call setSelectedLibraryId with library id when a library is clicked", () => {
    setupMock({});
    render(<LibrariesSection isCollapsed={false} />);

    fireEvent.click(screen.getByText("Literature"));
    expect(mockSetSelectedLibraryId).toHaveBeenCalledWith(2);
  });

  it("should show upload icon for the active library", () => {
    setupMock({ activeLibrary: comicsLibrary });
    render(<LibrariesSection isCollapsed={false} />);

    // The upload icon should exist with its title
    const uploadIcon = document.querySelector(
      '[title="Active library (ingest target)"]',
    );
    expect(uploadIcon).not.toBeNull();
  });

  it("should not show upload icon for non-active libraries", () => {
    setupMock({ activeLibrary: comicsLibrary });
    render(<LibrariesSection isCollapsed={false} />);

    // Only one upload icon should exist (for Comics, not Literature)
    const uploadIcons = document.querySelectorAll(
      '[title="Active library (ingest target)"]',
    );
    expect(uploadIcons.length).toBe(1);
  });

  it("should highlight the selected library", () => {
    setupMock({ selectedLibraryId: 2 });
    render(<LibrariesSection isCollapsed={false} />);

    // Literature button should have active styling
    const litButton = screen.getByText("Literature").closest("button");
    expect(litButton?.className).toContain("bg-");
  });

  it("should render with three libraries and correct number of items", () => {
    setupMock({
      visibleLibraries: [comicsLibrary, literatureLibrary, textbooksLibrary],
    });
    render(<LibrariesSection isCollapsed={false} />);

    // 1 "All" + 3 libraries = 4 list items
    const listItems = document.querySelectorAll("li");
    expect(listItems.length).toBe(4);
  });
});
