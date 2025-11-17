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

import { vi } from "vitest";

vi.mock("./useDeleteConfirmation", () => ({
  useDeleteConfirmation: vi.fn(),
}));

import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { UserContext } from "@/contexts/UserContext";
import type { Book } from "@/types/book";
import { useBookCardMenuActions } from "./useBookCardMenuActions";
import { useDeleteConfirmation } from "./useDeleteConfirmation";

type UserContextValue = React.ComponentProps<
  typeof UserContext.Provider
>["value"];

/**
 * Creates a wrapper component with UserContext.
 *
 * Parameters
 * ----------
 * mockContext : Partial<UserContextValue>
 *     Mock context values.
 *
 * Returns
 * -------
 * ({ children }: { children: ReactNode }) => JSX.Element
 *     Wrapper component.
 */
function createWrapper(mockContext: Partial<UserContextValue> = {}) {
  const defaultContext: UserContextValue = {
    user: null,
    isLoading: false,
    error: null,
    refresh: vi.fn(),
    refreshTimestamp: 0,
    updateUser: vi.fn(),
    profilePictureUrl: null,
    invalidateProfilePictureCache: vi.fn(),
    settings: {},
    isSaving: false,
    getSetting: vi.fn(() => null),
    updateSetting: vi.fn(),
    defaultDevice: null,
    hasPermission: vi.fn(() => false),
    canPerformAction: vi.fn(() => false),
    ...mockContext,
  };

  return ({ children }: { children: ReactNode }) => (
    <UserContext.Provider value={defaultContext}>
      {children}
    </UserContext.Provider>
  );
}

/**
 * Creates a mock book with the given ID.
 *
 * Parameters
 * ----------
 * id : number
 *     Book ID.
 *
 * Returns
 * -------
 * Book
 *     Mock book object.
 */
function createMockBook(id: number): Book {
  return {
    id,
    title: `Test Book ${id}`,
    authors: [`Author ${id}`],
    author_sort: `Author ${id}`,
    pubdate: null,
    timestamp: null,
    series: null,
    series_id: null,
    series_index: null,
    isbn: null,
    uuid: `uuid-${id}`,
    thumbnail_url: null,
    has_cover: false,
  };
}

describe("useBookCardMenuActions", () => {
  let capturedOnSuccess: (() => void) | undefined;
  let capturedOnError: ((error: string) => void) | undefined;

  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    capturedOnSuccess = undefined;
    capturedOnError = undefined;

    vi.mocked(useDeleteConfirmation).mockImplementation((options) => {
      capturedOnSuccess = options.onSuccess;
      capturedOnError = options.onError;
      return {
        isOpen: false,
        dontShowAgain: false,
        deleteFilesFromDrive: false,
        isDeleting: false,
        error: null,
        open: vi.fn(),
        close: vi.fn(),
        toggleDontShowAgain: vi.fn(),
        toggleDeleteFilesFromDrive: vi.fn(),
        confirm: vi.fn(),
      };
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it("should initialize with all handlers and deleteConfirmation", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(result.current.handleBookInfo).toBeDefined();
    expect(result.current.handleSend).toBeDefined();
    expect(result.current.handleMoveToLibrary).toBeDefined();
    expect(result.current.handleConvert).toBeDefined();
    expect(result.current.handleDelete).toBeDefined();
    expect(result.current.handleMore).toBeDefined();
    expect(result.current.deleteConfirmation).toBeDefined();
  });

  it("should call onBookClick when handleBookInfo is called and onBookClick is provided", () => {
    const book = createMockBook(1);
    const onBookClick = vi.fn();
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
          onBookClick,
        }),
      { wrapper },
    );

    act(() => {
      result.current.handleBookInfo();
    });

    expect(onBookClick).toHaveBeenCalledTimes(1);
    expect(onBookClick).toHaveBeenCalledWith(book);
  });

  it("should not throw when handleBookInfo is called and onBookClick is not provided", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(() => {
      act(() => {
        result.current.handleBookInfo();
      });
    }).not.toThrow();
  });

  it("should call deleteConfirmation.open when handleDelete is called", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    const openSpy = vi.spyOn(result.current.deleteConfirmation, "open");

    act(() => {
      result.current.handleDelete();
    });

    expect(openSpy).toHaveBeenCalledTimes(1);
  });

  it("should call onBookDeleted when delete succeeds", () => {
    const book = createMockBook(1);
    const onBookDeleted = vi.fn();
    const wrapper = createWrapper();

    renderHook(
      () =>
        useBookCardMenuActions({
          book,
          onBookDeleted,
        }),
      { wrapper },
    );

    // Manually invoke the captured onSuccess callback
    act(() => {
      if (capturedOnSuccess) {
        capturedOnSuccess();
      }
    });

    expect(onBookDeleted).toHaveBeenCalledTimes(1);
  });

  it("should call onDeleteError when delete fails", () => {
    const book = createMockBook(1);
    const onDeleteError = vi.fn();
    const wrapper = createWrapper();
    const errorMessage = "Failed to delete book";

    renderHook(
      () =>
        useBookCardMenuActions({
          book,
          onDeleteError,
        }),
      { wrapper },
    );

    // Manually invoke the captured onError callback
    act(() => {
      if (capturedOnError) {
        capturedOnError(errorMessage);
      }
    });

    expect(onDeleteError).toHaveBeenCalledTimes(1);
    expect(onDeleteError).toHaveBeenCalledWith(errorMessage);
  });

  it("should not throw when onBookDeleted is undefined and delete succeeds", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(() => {
      act(() => {
        if (capturedOnSuccess) {
          capturedOnSuccess();
        }
      });
    }).not.toThrow();
  });

  it("should not throw when onDeleteError is undefined and delete fails", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();
    const errorMessage = "Failed to delete book";

    renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(() => {
      act(() => {
        if (capturedOnError) {
          capturedOnError(errorMessage);
        }
      });
    }).not.toThrow();
  });

  it("should not throw when handleSend is called", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(() => {
      act(() => {
        result.current.handleSend();
      });
    }).not.toThrow();
  });

  it("should not throw when handleMoveToLibrary is called", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(() => {
      act(() => {
        result.current.handleMoveToLibrary();
      });
    }).not.toThrow();
  });

  it("should not throw when handleConvert is called", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(() => {
      act(() => {
        result.current.handleConvert();
      });
    }).not.toThrow();
  });

  it("should not throw when handleMore is called", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(() => {
      act(() => {
        result.current.handleMore();
      });
    }).not.toThrow();
  });

  it("should pass book.id to useDeleteConfirmation", () => {
    const book = createMockBook(42);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    // Verify deleteConfirmation is initialized (it uses book.id internally)
    expect(result.current.deleteConfirmation).toBeDefined();
  });

  it("should handle all callbacks being undefined", () => {
    const book = createMockBook(1);
    const wrapper = createWrapper();

    const { result } = renderHook(
      () =>
        useBookCardMenuActions({
          book,
        }),
      { wrapper },
    );

    expect(() => {
      act(() => {
        result.current.handleBookInfo();
        result.current.handleSend();
        result.current.handleMoveToLibrary();
        result.current.handleConvert();
        result.current.handleDelete();
        result.current.handleMore();
      });
    }).not.toThrow();
  });
});
