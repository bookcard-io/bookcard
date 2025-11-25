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

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AuthorWithMetadata } from "@/types/author";
import { useAuthor } from "./useAuthor";

vi.mock("@/services/authorService", () => ({
  fetchAuthor: vi.fn(),
}));

vi.mock("@/utils/fetch", () => ({
  deduplicateFetch: vi.fn(),
  generateFetchKey: vi.fn(),
}));

import { fetchAuthor } from "@/services/authorService";
import { deduplicateFetch, generateFetchKey } from "@/utils/fetch";

/**
 * Create a mock author for testing.
 */
function createMockAuthor(id: string): AuthorWithMetadata {
  return {
    key: id,
    name: `Author ${id}`,
    personal_name: `Personal ${id}`,
  };
}

describe("useAuthor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(deduplicateFetch).mockImplementation(async (_key, fetchFn) =>
      fetchFn(),
    );
    vi.mocked(generateFetchKey).mockReturnValue("mock-key");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("initialization", () => {
    it("should initialize with null author when authorId is null", () => {
      const { result } = renderHook(() => useAuthor({ authorId: null }));

      expect(result.current.author).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("should initialize with null author when enabled is false", () => {
      const { result } = renderHook(() =>
        useAuthor({ authorId: "123", enabled: false }),
      );

      expect(result.current.author).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe("fetching", () => {
    it("should fetch author successfully", async () => {
      const mockAuthor = createMockAuthor("123");
      vi.mocked(fetchAuthor).mockResolvedValue(mockAuthor);

      const { result } = renderHook(() => useAuthor({ authorId: "123" }));

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.author).toEqual(mockAuthor);
      expect(result.current.error).toBeNull();
      expect(fetchAuthor).toHaveBeenCalledWith("123");
    });

    it.each([
      { authorId: "/authors/123", expected: "123" },
      { authorId: "/123", expected: "123" },
      { authorId: "123", expected: "123" },
      { authorId: "/authors/456/", expected: "456/" },
    ])(
      "should normalize authorId '$authorId' to '$expected'",
      async ({ authorId, expected }) => {
        const mockAuthor = createMockAuthor(expected);
        vi.mocked(fetchAuthor).mockResolvedValue(mockAuthor);

        const { result } = renderHook(() => useAuthor({ authorId }));

        await waitFor(() => {
          expect(result.current.isLoading).toBe(false);
        });

        expect(fetchAuthor).toHaveBeenCalledWith(expected);
      },
    );

    it("should handle fetch error", async () => {
      const errorMessage = "Author not found";
      vi.mocked(fetchAuthor).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useAuthor({ authorId: "123" }));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.author).toBeNull();
      expect(result.current.error).toBe(errorMessage);
    });

    it("should handle non-Error rejection", async () => {
      vi.mocked(fetchAuthor).mockRejectedValue("String error");

      const { result } = renderHook(() => useAuthor({ authorId: "123" }));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBe("Unknown error");
    });
  });

  describe("refetch", () => {
    it("should refetch author when refetch is called", async () => {
      const mockAuthor1 = createMockAuthor("123");
      const mockAuthor2 = createMockAuthor("123");
      mockAuthor2.name = "Updated Author";
      vi.mocked(fetchAuthor)
        .mockResolvedValueOnce(mockAuthor1)
        .mockResolvedValueOnce(mockAuthor2);

      const { result } = renderHook(() => useAuthor({ authorId: "123" }));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.author?.name).toBe("Author 123");

      await act(async () => {
        await result.current.refetch();
      });

      expect(result.current.author?.name).toBe("Updated Author");
      expect(fetchAuthor).toHaveBeenCalledTimes(2);
    });

    it("should not refetch when enabled is false", async () => {
      const { result } = renderHook(() =>
        useAuthor({ authorId: "123", enabled: false }),
      );

      await act(async () => {
        await result.current.refetch();
      });

      expect(fetchAuthor).not.toHaveBeenCalled();
    });

    it("should not refetch when authorId is null", async () => {
      const { result } = renderHook(() => useAuthor({ authorId: null }));

      await act(async () => {
        await result.current.refetch();
      });

      expect(fetchAuthor).not.toHaveBeenCalled();
    });
  });

  describe("updateAuthor", () => {
    it("should update author in place", async () => {
      const mockAuthor = createMockAuthor("123");
      vi.mocked(fetchAuthor).mockResolvedValue(mockAuthor);

      const { result } = renderHook(() => useAuthor({ authorId: "123" }));

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const updatedAuthor = { ...mockAuthor, name: "Updated Name" };

      act(() => {
        result.current.updateAuthor(updatedAuthor);
      });

      expect(result.current.author?.name).toBe("Updated Name");
    });
  });

  describe("authorId changes", () => {
    it("should refetch when authorId changes", async () => {
      const mockAuthor1 = createMockAuthor("123");
      const mockAuthor2 = createMockAuthor("456");
      vi.mocked(fetchAuthor)
        .mockResolvedValueOnce(mockAuthor1)
        .mockResolvedValueOnce(mockAuthor2);

      const { result, rerender } = renderHook(
        ({ authorId }) => useAuthor({ authorId }),
        { initialProps: { authorId: "123" } },
      );

      await waitFor(() => {
        expect(result.current.author?.key).toBe("123");
      });

      rerender({ authorId: "456" });

      await waitFor(() => {
        expect(result.current.author?.key).toBe("456");
      });

      expect(fetchAuthor).toHaveBeenCalledTimes(2);
    });
  });
});
