// Copyright (C) 2025 khoa and others
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

import type { Book, Rendition } from "epubjs";
import { useRef } from "react";
import type { ReactReader } from "react-reader";

/**
 * Hook to manage all EPUB reader refs in one place.
 *
 * Centralizes ref management for better organization and easier testing.
 * Follows SRP by isolating ref creation and management.
 *
 * Returns
 * -------
 * object
 *     Object containing all EPUB reader refs.
 */
export function useEpubRefs() {
  const renditionRef = useRef<Rendition | undefined>(undefined);
  const bookRef = useRef<Book | null>(null);
  const reactReaderRef = useRef<ReactReader | null>(null);
  const isNavigatingRef = useRef(false);
  const progressCalculationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isInitialLoadRef = useRef(true);

  return {
    renditionRef,
    bookRef,
    reactReaderRef,
    isNavigatingRef,
    progressCalculationTimeoutRef,
    isInitialLoadRef,
  };
}
