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
  useEffect,
  useState,
} from "react";
import type { AuthorWithMetadata } from "@/types/author";

interface SelectedAuthorsContextType {
  /** Set of selected author IDs (keys). */
  selectedAuthorIds: Set<string>;
  /** Whether an author is selected. */
  isSelected: (authorId: string) => boolean;
  /** Handle author click with multi-select support (Ctrl/Shift modifiers). */
  handleAuthorClick: (
    author: AuthorWithMetadata,
    authors: AuthorWithMetadata[],
    event: React.MouseEvent,
  ) => void;
  /** Clear all selections. */
  clearSelection: () => void;
  /** Select all authors. */
  selectAll: (authors: AuthorWithMetadata[]) => void;
  /** Number of selected authors. */
  selectedCount: number;
}

const SelectedAuthorsContext = createContext<
  SelectedAuthorsContextType | undefined
>(undefined);

/**
 * Get author identifier for selection.
 *
 * Parameters
 * ----------
 * author : AuthorWithMetadata
 *     Author to get identifier for.
 *
 * Returns
 * -------
 * string
 *     Author identifier (key or name as fallback).
 */
function getAuthorId(author: AuthorWithMetadata): string {
  return author.key || author.name;
}

/**
 * Provider for managing selected authors state.
 *
 * Implements multi-select functionality with Ctrl+click (toggle) and
 * Shift+click (range selection) support.
 */
export function SelectedAuthorsProvider({ children }: { children: ReactNode }) {
  const [selectedAuthorIds, setSelectedAuthorIds] = useState<Set<string>>(
    new Set(),
  );
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(
    null,
  );

  const isSelected = useCallback(
    (authorId: string) => {
      return selectedAuthorIds.has(authorId);
    },
    [selectedAuthorIds],
  );

  const handleAuthorClick = useCallback(
    (
      author: AuthorWithMetadata,
      authors: AuthorWithMetadata[],
      event: React.MouseEvent,
    ) => {
      const authorId = getAuthorId(author);
      const authorIndex = authors.findIndex((a) => getAuthorId(a) === authorId);
      if (authorIndex === -1) {
        return;
      }

      if (event.shiftKey && lastSelectedIndex !== null) {
        // Shift+click: select range from last selected to current
        const startIndex = lastSelectedIndex;
        const endIndex = authorIndex;
        const minIndex = Math.min(startIndex, endIndex);
        const maxIndex = Math.max(startIndex, endIndex);

        setSelectedAuthorIds((prev) => {
          const next = new Set(prev);
          for (let i = minIndex; i <= maxIndex; i++) {
            const author = authors[i];
            if (author) {
              next.add(getAuthorId(author));
            }
          }
          return next;
        });
        setLastSelectedIndex(authorIndex);
      } else if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd+click: toggle selection
        setSelectedAuthorIds((prev) => {
          const next = new Set(prev);
          if (next.has(authorId)) {
            next.delete(authorId);
          } else {
            next.add(authorId);
          }
          return next;
        });
        setLastSelectedIndex(authorIndex);
      } else {
        // Regular click: clear and select single
        setSelectedAuthorIds(new Set([authorId]));
        setLastSelectedIndex(authorIndex);
      }
    },
    [lastSelectedIndex],
  );

  const clearSelection = useCallback(() => {
    setSelectedAuthorIds(new Set());
    setLastSelectedIndex(null);
  }, []);

  const selectAll = useCallback((authors: AuthorWithMetadata[]) => {
    const allIds = new Set(authors.map((author) => getAuthorId(author)));
    setSelectedAuthorIds(allIds);
    if (authors.length > 0) {
      setLastSelectedIndex(authors.length - 1);
    }
  }, []);

  // Handle click-outside to clear selection
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Only clear if there are selected authors
      if (selectedAuthorIds.size === 0) {
        return;
      }

      const target = event.target as HTMLElement;
      // Check if click is on an author card using data attribute
      const isAuthorCard = target.closest("[data-author-card]");
      // Don't clear if clicking on an author card
      if (isAuthorCard) {
        return;
      }

      // Clear selection when clicking outside author cards
      clearSelection();
    };

    document.addEventListener("click", handleClickOutside);
    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    selectedAuthorIds.size, // Clear selection when clicking outside author cards
    clearSelection,
  ]);

  const selectedCount = selectedAuthorIds.size;

  return (
    <SelectedAuthorsContext.Provider
      value={{
        selectedAuthorIds,
        isSelected,
        handleAuthorClick,
        clearSelection,
        selectAll,
        selectedCount,
      }}
    >
      {children}
    </SelectedAuthorsContext.Provider>
  );
}

/**
 * Hook to access selected authors context.
 *
 * Returns
 * -------
 * SelectedAuthorsContextType
 *     Context value with selection state and handlers.
 *
 * Raises
 * ------
 * Error
 *     If used outside SelectedAuthorsProvider.
 */
export function useSelectedAuthors(): SelectedAuthorsContextType {
  const context = useContext(SelectedAuthorsContext);
  if (context === undefined) {
    throw new Error(
      "useSelectedAuthors must be used within SelectedAuthorsProvider",
    );
  }
  return context;
}
