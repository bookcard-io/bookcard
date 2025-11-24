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

import type { Rendition } from "epubjs";
import type { RefObject } from "react";
import { useRef } from "react";
import type { SearchResult } from "../EPUBReader";

/**
 * Options for useEpubSearch hook.
 */
export interface UseEpubSearchOptions {
  /** Ref to rendition instance. */
  renditionRef: RefObject<Rendition | undefined>;
  /** Function to set location. */
  setLocation: (location: string) => void;
  /** Callback when search results are available. */
  onSearchResults?: (results: SearchResult[]) => void;
}

/**
 * Hook to manage EPUB search functionality.
 *
 * Handles search result highlighting and navigation.
 * Follows SRP by focusing solely on search management.
 * Follows IOC by accepting dependencies as parameters.
 *
 * Parameters
 * ----------
 * options : UseEpubSearchOptions
 *     Hook options including refs and callbacks.
 *
 * Returns
 * -------
 * (results: SearchResult[]) => void
 *     Handler function for search results.
 */
export function useEpubSearch({
  renditionRef,
  setLocation,
  onSearchResults,
}: UseEpubSearchOptions): (results: SearchResult[]) => void {
  const prevSearchResultsRef = useRef<SearchResult[]>([]);

  return (results: SearchResult[]) => {
    const rendition = renditionRef.current;
    if (!rendition) {
      onSearchResults?.(results);
      return;
    }

    // Clear previous highlights
    prevSearchResultsRef.current.forEach((result) => {
      try {
        rendition.annotations.remove(result.cfi, "highlight");
      } catch {
        // Ignore errors when removing highlights
      }
    });

    // Note: Page numbers are not extracted here to avoid disrupting the reader view
    // They can be added asynchronously later if needed
    const enhancedResults: SearchResult[] = results;

    // Add new highlights
    enhancedResults.forEach((result) => {
      try {
        rendition.annotations.add("highlight", result.cfi);
      } catch {
        // Ignore errors when adding highlights
      }
    });

    // Navigate to first result if available
    if (enhancedResults.length > 0 && enhancedResults[0]) {
      setLocation(enhancedResults[0].cfi);
    }

    // Store current results for next clear
    prevSearchResultsRef.current = enhancedResults;

    // Notify parent component
    onSearchResults?.(enhancedResults);
  };
}
