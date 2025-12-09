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
import type { Shelf, ShelfCreate } from "@/types/shelf";
import { useCreateShelfWithBook } from "./useCreateShelfWithBook";

vi.mock("@/hooks/useShelfActions", () => ({
  useShelfActions: vi.fn(),
}));

vi.mock("@/hooks/useRecentShelves", () => ({
  useRecentShelves: vi.fn(),
}));

vi.mock("@/contexts/ShelvesContext", () => ({
  useShelvesContext: vi.fn(),
}));

vi.mock("@/services/shelfService", () => ({
  createShelf: vi.fn(),
}));

import { useShelvesContext } from "@/contexts/ShelvesContext";
import { useRecentShelves } from "@/hooks/useRecentShelves";
import { useShelfActions } from "@/hooks/useShelfActions";
import { createShelf } from "@/services/shelfService";

describe("useCreateShelfWithBook", () => {
  let mockAddBook: ReturnType<
    typeof vi.fn<(shelfId: number, bookId: number) => Promise<void>>
  >;
  let mockAddRecentShelf: ReturnType<typeof vi.fn<(shelfId: number) => void>>;
  let mockRefreshShelvesContext: ReturnType<typeof vi.fn<() => Promise<void>>>;
  let mockOnSuccess: ReturnType<typeof vi.fn<() => void>>;
  let mockOnError: ReturnType<typeof vi.fn<(error: unknown) => void>>;

  const mockShelf: Shelf = {
    id: 1,
    uuid: "test-uuid",
    name: "Test Shelf",
    description: null,
    cover_picture: null,
    is_public: false,
    is_active: true,
    shelf_type: "shelf",
    user_id: 1,
    library_id: 1,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    last_modified: "2025-01-01T00:00:00Z",
    book_count: 0,
  };

  beforeEach(() => {
    vi.clearAllMocks();

    mockAddBook = vi.fn<(shelfId: number, bookId: number) => Promise<void>>();
    mockAddRecentShelf = vi.fn<(shelfId: number) => void>();
    mockRefreshShelvesContext = vi.fn<() => Promise<void>>();
    mockOnSuccess = vi.fn<() => void>();
    mockOnError = vi.fn<(error: unknown) => void>();

    vi.mocked(useShelfActions).mockReturnValue({
      addBook: mockAddBook,
      removeBook: vi.fn(),
      reorderBooks: vi.fn(),
      isProcessing: false,
      error: null,
    } as ReturnType<typeof useShelfActions>);

    vi.mocked(useRecentShelves).mockReturnValue({
      recentShelfIds: [],
      addRecentShelf: mockAddRecentShelf,
      getRecentShelves: vi.fn(),
    } as ReturnType<typeof useRecentShelves>);

    vi.mocked(useShelvesContext).mockReturnValue({
      shelves: [],
      isLoading: false,
      error: null,
      refresh: mockRefreshShelvesContext,
    } as ReturnType<typeof useShelvesContext>);

    vi.mocked(createShelf).mockResolvedValue(mockShelf);
    mockAddBook.mockResolvedValue(undefined);
    mockRefreshShelvesContext.mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should initialize with closed modal", () => {
    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 1,
      }),
    );

    expect(result.current.showCreateModal).toBe(false);
  });

  it("should open modal when openCreateModal is called", () => {
    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 1,
      }),
    );

    act(() => {
      result.current.openCreateModal();
    });

    expect(result.current.showCreateModal).toBe(true);
  });

  it("should close modal when closeCreateModal is called", () => {
    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 1,
      }),
    );

    act(() => {
      result.current.openCreateModal();
    });

    expect(result.current.showCreateModal).toBe(true);

    act(() => {
      result.current.closeCreateModal();
    });

    expect(result.current.showCreateModal).toBe(false);
  });

  it("should create shelf, add book, and refresh context on success", async () => {
    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "Test Description",
      is_public: false,
    };

    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 10,
        onSuccess: mockOnSuccess,
      }),
    );

    act(() => {
      result.current.openCreateModal();
    });

    let createdShelf: Shelf | undefined;
    await act(async () => {
      createdShelf = await result.current.handleCreateShelf(shelfData);
    });

    expect(createShelf).toHaveBeenCalledWith(shelfData);
    expect(mockAddBook).toHaveBeenCalledWith(1, 10);
    expect(mockAddRecentShelf).toHaveBeenCalledWith(1);
    expect(mockRefreshShelvesContext).toHaveBeenCalled();
    expect(result.current.showCreateModal).toBe(false);
    expect(mockOnSuccess).toHaveBeenCalled();
    expect(createdShelf).toEqual(mockShelf);
  });

  it("should call onError and keep modal open on error", async () => {
    const error = new Error("Failed to create shelf");
    vi.mocked(createShelf).mockRejectedValueOnce(error);

    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "Test Description",
      is_public: false,
    };

    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 10,
        onError: mockOnError,
      }),
    );

    act(() => {
      result.current.openCreateModal();
    });

    await act(async () => {
      try {
        await result.current.handleCreateShelf(shelfData);
      } catch {
        // Expected to throw
      }
    });

    expect(mockOnError).toHaveBeenCalledWith(error);
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Failed to create shelf and add book:",
      error,
    );
    expect(result.current.showCreateModal).toBe(true); // Modal stays open

    consoleErrorSpy.mockRestore();
  });

  it("should handle error when adding book fails", async () => {
    const error = new Error("Failed to add book");
    mockAddBook.mockRejectedValueOnce(error);

    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "Test Description",
      is_public: false,
    };

    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 10,
        onError: mockOnError,
      }),
    );

    act(() => {
      result.current.openCreateModal();
    });

    await act(async () => {
      try {
        await result.current.handleCreateShelf(shelfData);
      } catch {
        // Expected to throw
      }
    });

    expect(createShelf).toHaveBeenCalled();
    expect(mockAddBook).toHaveBeenCalled();
    expect(mockOnError).toHaveBeenCalledWith(error);
    expect(result.current.showCreateModal).toBe(true);

    consoleErrorSpy.mockRestore();
  });

  it("should handle error when refresh fails", async () => {
    const error = new Error("Failed to refresh");
    mockRefreshShelvesContext.mockRejectedValueOnce(error);

    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "Test Description",
      is_public: false,
    };

    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 10,
        onError: mockOnError,
      }),
    );

    act(() => {
      result.current.openCreateModal();
    });

    await act(async () => {
      try {
        await result.current.handleCreateShelf(shelfData);
      } catch {
        // Expected to throw
      }
    });

    expect(mockOnError).toHaveBeenCalledWith(error);
    expect(result.current.showCreateModal).toBe(true);

    consoleErrorSpy.mockRestore();
  });

  it("should not call onSuccess if not provided", async () => {
    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "Test Description",
      is_public: false,
    };

    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 10,
      }),
    );

    await act(async () => {
      await result.current.handleCreateShelf(shelfData);
    });

    expect(createShelf).toHaveBeenCalled();
    expect(mockAddBook).toHaveBeenCalled();
    expect(result.current.showCreateModal).toBe(false);
  });

  it("should not call onError if not provided", async () => {
    const error = new Error("Failed to create shelf");
    vi.mocked(createShelf).mockRejectedValueOnce(error);

    const consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});

    const shelfData: ShelfCreate = {
      name: "New Shelf",
      description: "Test Description",
      is_public: false,
    };

    const { result } = renderHook(() =>
      useCreateShelfWithBook({
        bookId: 10,
      }),
    );

    // Open modal first
    act(() => {
      result.current.openCreateModal();
    });

    expect(result.current.showCreateModal).toBe(true);

    await act(async () => {
      try {
        await result.current.handleCreateShelf(shelfData);
      } catch {
        // Expected to throw
      }
    });

    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(result.current.showCreateModal).toBe(true);

    consoleErrorSpy.mockRestore();
  });
});
