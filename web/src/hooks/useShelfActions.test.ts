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

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  addBookToShelf,
  removeBookFromShelf,
  reorderShelfBooks,
} from "@/services/shelfService";
import { useShelfActions } from "./useShelfActions";

const shelfServiceMocks = vi.hoisted(() => ({
  addBookToShelf: vi.fn(),
  removeBookFromShelf: vi.fn(),
  reorderShelfBooks: vi.fn(),
}));

vi.mock("@/services/shelfService", () => shelfServiceMocks);

describe("useShelfActions", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("addBook", () => {
    it("should add book to shelf successfully", async () => {
      vi.mocked(addBookToShelf).mockResolvedValue(undefined);

      const { result } = renderHook(() => useShelfActions());

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.error).toBeNull();

      await act(async () => {
        await result.current.addBook(1, 10, 1);
      });

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.error).toBeNull();
      expect(addBookToShelf).toHaveBeenCalledWith(1, 10, 1);
    });

    it("should handle error when adding book", async () => {
      const errorMessage = "Failed to add book";
      vi.mocked(addBookToShelf).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useShelfActions());

      await act(async () => {
        try {
          await result.current.addBook(1, 10, 1);
        } catch {
          // Expected to throw
        }
      });

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.error).toBe(errorMessage);
    });

    it("should handle non-Error rejection when adding book", async () => {
      vi.mocked(addBookToShelf).mockRejectedValue("String error");

      const { result } = renderHook(() => useShelfActions());

      await act(async () => {
        try {
          await result.current.addBook(1, 10, 1);
        } catch {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe("Failed to add book to shelf");
    });

    it("should set isProcessing during operation", async () => {
      let resolvePromise: () => void;
      const promise = new Promise<void>((resolve) => {
        resolvePromise = resolve;
      });
      vi.mocked(addBookToShelf).mockImplementation(() => promise);

      const { result } = renderHook(() => useShelfActions());

      act(() => {
        void result.current.addBook(1, 10, 1);
      });

      expect(result.current.isProcessing).toBe(true);

      act(() => {
        if (resolvePromise) {
          resolvePromise();
        }
      });

      await act(async () => {
        await promise;
      });

      expect(result.current.isProcessing).toBe(false);
    });
  });

  describe("removeBook", () => {
    it("should remove book from shelf successfully", async () => {
      vi.mocked(removeBookFromShelf).mockResolvedValue(undefined);

      const { result } = renderHook(() => useShelfActions());

      await act(async () => {
        await result.current.removeBook(1, 10, 1);
      });

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.error).toBeNull();
      expect(removeBookFromShelf).toHaveBeenCalledWith(1, 10, 1);
    });

    it("should handle error when removing book", async () => {
      const errorMessage = "Failed to remove book";
      vi.mocked(removeBookFromShelf).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useShelfActions());

      await act(async () => {
        try {
          await result.current.removeBook(1, 10, 1);
        } catch {
          // Expected to throw
        }
      });

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.error).toBe(errorMessage);
    });

    it("should handle non-Error rejection when removing book", async () => {
      vi.mocked(removeBookFromShelf).mockRejectedValue("String error");

      const { result } = renderHook(() => useShelfActions());

      await act(async () => {
        try {
          await result.current.removeBook(1, 10, 1);
        } catch {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe("Failed to remove book from shelf");
    });
  });

  describe("reorderBooks", () => {
    it("should reorder books successfully", async () => {
      const bookOrders = [
        { book_id: 1, library_id: 1, order: 0 },
        { book_id: 2, library_id: 1, order: 1 },
        { book_id: 3, library_id: 1, order: 2 },
      ];
      vi.mocked(reorderShelfBooks).mockResolvedValue(undefined);

      const { result } = renderHook(() => useShelfActions());

      await act(async () => {
        await result.current.reorderBooks(1, bookOrders);
      });

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.error).toBeNull();
      expect(reorderShelfBooks).toHaveBeenCalledWith(1, bookOrders);
    });

    it("should handle error when reordering books", async () => {
      const errorMessage = "Failed to reorder books";
      const bookOrders = [
        { book_id: 1, library_id: 1, order: 0 },
        { book_id: 2, library_id: 1, order: 1 },
      ];
      vi.mocked(reorderShelfBooks).mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useShelfActions());

      await act(async () => {
        try {
          await result.current.reorderBooks(1, bookOrders);
        } catch {
          // Expected to throw
        }
      });

      expect(result.current.isProcessing).toBe(false);
      expect(result.current.error).toBe(errorMessage);
    });

    it("should handle non-Error rejection when reordering books", async () => {
      const bookOrders = [
        { book_id: 1, library_id: 1, order: 0 },
        { book_id: 2, library_id: 1, order: 1 },
      ];
      vi.mocked(reorderShelfBooks).mockRejectedValue("String error");

      const { result } = renderHook(() => useShelfActions());

      await act(async () => {
        try {
          await result.current.reorderBooks(1, bookOrders);
        } catch {
          // Expected to throw
        }
      });

      expect(result.current.error).toBe("Failed to reorder books in shelf");
    });
  });
});
