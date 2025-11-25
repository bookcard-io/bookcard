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

import { renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AuthorWithMetadata } from "@/types/author";
import { getAuthorId, useAuthorSelection } from "./useAuthorSelection";

vi.mock("@/contexts/SelectedAuthorsContext", () => ({
  useSelectedAuthors: vi.fn(),
}));

import { useSelectedAuthors } from "@/contexts/SelectedAuthorsContext";

/**
 * Create a mock author for testing.
 */
function createMockAuthor(key: string, name: string): AuthorWithMetadata {
  return {
    key,
    name,
  };
}

describe("useAuthorSelection", () => {
  const mockContextValue = {
    selectedAuthorIds: new Set<string>(),
    isSelected: vi.fn(() => false),
    handleAuthorClick: vi.fn(),
    clearSelection: vi.fn(),
    selectAll: vi.fn(),
    selectedCount: 0,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useSelectedAuthors).mockReturnValue(mockContextValue);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("useAuthorSelection", () => {
    it("should return context value", () => {
      const { result } = renderHook(() => useAuthorSelection());

      expect(result.current).toEqual(mockContextValue);
      expect(useSelectedAuthors).toHaveBeenCalled();
    });
  });

  describe("getAuthorId", () => {
    it("should return key when available", () => {
      const author = createMockAuthor("OL123A", "Test Author");
      expect(getAuthorId(author)).toBe("OL123A");
    });

    it("should return name when key is not available", () => {
      const author = createMockAuthor("", "Test Author");
      author.key = undefined;
      expect(getAuthorId(author)).toBe("Test Author");
    });

    it("should return name when key is null", () => {
      const author = createMockAuthor("", "Test Author");
      author.key = null as unknown as string;
      expect(getAuthorId(author)).toBe("Test Author");
    });

    it("should return empty string when both key and name are missing", () => {
      const author = createMockAuthor("", "");
      author.key = undefined;
      expect(getAuthorId(author)).toBe("");
    });
  });
});
