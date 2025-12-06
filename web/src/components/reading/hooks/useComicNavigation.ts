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

import { useCallback, useEffect, useRef, useState } from "react";

export interface UseComicNavigationOptions {
  totalPages: number;
  initialPage?: number | null;
  onPageChange?: (page: number, totalPages: number, progress: number) => void;
}

export interface UseComicNavigationResult {
  currentPage: number;
  canGoNext: boolean;
  canGoPrevious: boolean;
  goToPage: (page: number) => void;
  goToNext: () => void;
  goToPrevious: () => void;
  goToFirst: () => void;
  goToLast: () => void;
  jumpToProgress: (progress: number) => void;
  registerJumpHandler: (handler: (progress: number) => void) => void;
}

/**
 * Hook for managing comic book page navigation.
 *
 * Handles page navigation logic, bounds checking, and progress calculation.
 * Follows SRP by focusing solely on navigation state management.
 *
 * Parameters
 * ----------
 * options : UseComicNavigationOptions
 *     Options including total pages and callbacks.
 *
 * Returns
 * -------
 * UseComicNavigationResult
 *     Navigation state and methods.
 */
export function useComicNavigation({
  totalPages,
  initialPage,
  onPageChange,
}: UseComicNavigationOptions): UseComicNavigationResult {
  const [currentPage, setCurrentPage] = useState(initialPage || 1);
  const isInitialLoadRef = useRef(true);
  const jumpHandlerRef = useRef<((progress: number) => void) | null>(null);

  // Navigate to initial page when it becomes available
  useEffect(() => {
    if (
      initialPage &&
      totalPages > 0 &&
      isInitialLoadRef.current &&
      initialPage >= 1 &&
      initialPage <= totalPages
    ) {
      setCurrentPage(initialPage);
      isInitialLoadRef.current = false;

      // Calculate and report progress
      if (onPageChange) {
        const progress = initialPage / totalPages;
        onPageChange(initialPage, totalPages, progress);
      }
    } else if (totalPages > 0 && isInitialLoadRef.current) {
      // If no initial page, start at page 1
      isInitialLoadRef.current = false;
    }
  }, [initialPage, totalPages, onPageChange]);

  // Ensure current page is within bounds
  useEffect(() => {
    if (totalPages > 0 && currentPage > totalPages) {
      setCurrentPage(totalPages);
    } else if (currentPage < 1) {
      setCurrentPage(1);
    }
  }, [currentPage, totalPages]);

  const goToPage = useCallback(
    (page: number) => {
      const clampedPage = Math.max(1, Math.min(page, totalPages));
      setCurrentPage(clampedPage);

      if (onPageChange && !isInitialLoadRef.current) {
        const progress = clampedPage / totalPages;
        onPageChange(clampedPage, totalPages, progress);
      }
    },
    [totalPages, onPageChange],
  );

  const goToNext = useCallback(() => {
    if (currentPage < totalPages) {
      goToPage(currentPage + 1);
    }
  }, [currentPage, totalPages, goToPage]);

  const goToPrevious = useCallback(() => {
    if (currentPage > 1) {
      goToPage(currentPage - 1);
    }
  }, [currentPage, goToPage]);

  const goToFirst = useCallback(() => {
    goToPage(1);
  }, [goToPage]);

  const goToLast = useCallback(() => {
    goToPage(totalPages);
  }, [totalPages, goToPage]);

  const jumpToProgress = useCallback(
    (progress: number) => {
      if (jumpHandlerRef.current) {
        jumpHandlerRef.current(progress);
      } else {
        // Fallback: calculate page from progress
        const targetPage = Math.max(
          1,
          Math.min(Math.ceil(progress * totalPages), totalPages),
        );
        goToPage(targetPage);
      }
    },
    [totalPages, goToPage],
  );

  const registerJumpHandler = useCallback(
    (handler: (progress: number) => void) => {
      jumpHandlerRef.current = handler;
    },
    [],
  );

  return {
    currentPage,
    canGoNext: currentPage < totalPages,
    canGoPrevious: currentPage > 1,
    goToPage,
    goToNext,
    goToPrevious,
    goToFirst,
    goToLast,
    jumpToProgress,
    registerJumpHandler,
  };
}
