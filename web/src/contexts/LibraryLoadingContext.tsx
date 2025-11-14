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

"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

interface LibraryLoadingContextType {
  /** Whether any library books request is currently loading. */
  isBooksLoading: boolean;
  /** Increment the internal counter of active book loading operations. */
  incrementBooksLoading: () => void;
  /** Decrement the internal counter of active book loading operations. */
  decrementBooksLoading: () => void;
}

const LibraryLoadingContext = createContext<
  LibraryLoadingContextType | undefined
>(undefined);

/**
 * Provider for global library loading state.
 *
 * Tracks how many book-related asynchronous operations are in-flight and
 * exposes a single `isBooksLoading` boolean derived from the internal counter.
 * This allows multiple consumers (e.g., grid/list views) to participate in a
 * shared loading signal without violating SRP or duplicating logic.
 *
 * Parameters
 * ----------
 * children : ReactNode
 *     Child components that can access the library loading context.
 */
export function LibraryLoadingProvider({ children }: { children: ReactNode }) {
  const [booksLoadingCount, setBooksLoadingCount] = useState(0);

  const incrementBooksLoading = useCallback(() => {
    setBooksLoadingCount((prev) => prev + 1);
  }, []);

  const decrementBooksLoading = useCallback(() => {
    setBooksLoadingCount((prev) => (prev > 0 ? prev - 1 : 0));
  }, []);

  const contextValue = useMemo(
    () => ({
      isBooksLoading: booksLoadingCount > 0,
      incrementBooksLoading,
      decrementBooksLoading,
    }),
    [booksLoadingCount, incrementBooksLoading, decrementBooksLoading],
  );

  return (
    <LibraryLoadingContext.Provider value={contextValue}>
      {children}
    </LibraryLoadingContext.Provider>
  );
}

/**
 * Hook to access library loading context.
 *
 * Returns
 * -------
 * LibraryLoadingContextType
 *     Aggregated loading state and control functions for library operations.
 *
 * Raises
 * ------
 * Error
 *     If used outside of LibraryLoadingProvider.
 */
export function useLibraryLoading() {
  const context = useContext(LibraryLoadingContext);
  if (context === undefined) {
    throw new Error(
      "useLibraryLoading must be used within a LibraryLoadingProvider",
    );
  }
  return context;
}
