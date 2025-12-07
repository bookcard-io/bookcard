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

"use client";

import { useMemo } from "react";
import { ReactReader } from "react-reader";
import { useReadingSettingsContext } from "@/contexts/ReadingSettingsContext";
import { useEPUBBook } from "@/hooks/useEPUBBook";
import { cn } from "@/libs/utils";
import { createEpubInitOptions } from "@/utils/epubInitOptions";
import {
  createLocationChangedHandler,
  type LocationChangedHandlerOptions,
} from "@/utils/epubLocationHandlers";
import {
  createReaderStyles,
  createTocHoverStyles,
} from "@/utils/epubReaderStyles";
import { useEpubLayout } from "./hooks/useEpubLayout";
import { useEpubRefs } from "./hooks/useEpubRefs";
import { useEpubSearch } from "./hooks/useEpubSearch";
import { useEpubTheme } from "./hooks/useEpubTheme";
import { useEpubUrl } from "./hooks/useEpubUrl";
import { useInitialCfi } from "./hooks/useInitialCfi";
import { useJumpToCfi } from "./hooks/useJumpToCfi";
import { useJumpToProgress } from "./hooks/useJumpToProgress";
import { useLocationState } from "./hooks/useLocationState";
import { usePagingInfo } from "./hooks/usePagingInfo";
import { useProgressCleanup } from "./hooks/useProgressCleanup";
import { useRenditionCallback } from "./hooks/useRenditionCallback";
import { useThemeRefs } from "./hooks/useThemeRefs";
import { useTocToggle } from "./hooks/useTocToggle";
import { useTocTracking } from "./hooks/useTocTracking";
import type { PagingInfo } from "./ReaderControls";

export type SearchResult = {
  cfi: string;
  excerpt: string;
  page?: number;
};

export interface EPUBReaderProps {
  /** Book URL or book ID. If string starts with /api/, treated as URL. Otherwise treated as book ID. */
  url?: string;
  /** Book ID (alternative to url). */
  bookId?: number;
  /** Initial CFI location to jump to. */
  initialCfi?: string | null;
  /** Callback when location changes. */
  onLocationChange?: (
    cfi: string,
    progress: number,
    skipBackendUpdate?: boolean,
  ) => void;
  /** Callback to register jump to progress handler. */
  onJumpToProgress?: (handler: ((progress: number) => void) | null) => void;
  /** Callback to register TOC toggle handler. */
  onTocToggle?: (handler: (() => void) | null) => void;
  /** Callback when locations are ready. */
  onLocationsReadyChange?: (ready: boolean) => void;
  /** Callback when paging information changes. */
  onPagingInfoChange?: (info: PagingInfo | null) => void;
  /** Current theme. */
  theme?: "light" | "dark";
  /** Search query to search for in the book. */
  searchQuery?: string;
  /** Callback when search results are available. */
  onSearchResults?: (results: SearchResult[]) => void;
  /** Callback to register jump to CFI handler. */
  onJumpToCfi?: (handler: ((cfi: string) => void) | null) => void;
  /** Optional className. */
  className?: string;
}

/**
 * EPUB reader component using react-reader.
 *
 * Fetches book as ArrayBuffer and renders using react-reader.
 * Supports theme colors, font customization, and scroll navigation.
 * Follows SRP by focusing solely on EPUB rendering.
 *
 * Parameters
 * ----------
 * props : EPUBReaderProps
 *     Component props including book ID and callbacks.
 */
export function EPUBReader({
  url,
  bookId,
  initialCfi,
  onLocationChange,
  onJumpToProgress,
  onTocToggle,
  onLocationsReadyChange,
  onPagingInfoChange,
  searchQuery,
  onSearchResults,
  onJumpToCfi,
  className,
}: EPUBReaderProps) {
  // Get settings from context
  const { fontFamily, fontSize, pageColor, pageLayout } =
    useReadingSettingsContext();

  // Manage all refs in one place
  const {
    renditionRef,
    bookRef,
    reactReaderRef,
    isNavigatingRef,
    progressCalculationTimeoutRef,
    isInitialLoadRef,
  } = useEpubRefs();

  // Track TOC for chapter information
  const { tocRef, handleTocChanged } = useTocTracking();

  // Manage location state and ref
  const { location, setLocation, locationRef } = useLocationState(
    initialCfi || 0,
  );

  const downloadUrl = useEpubUrl(url, bookId);

  // Fetch book as ArrayBuffer using hook
  const { bookArrayBuffer, isLoading, isError } = useEPUBBook(downloadUrl);

  // Manage theme refs for content hooks
  const { pageColorRef, fontFamilyRef, fontSizeRef } = useThemeRefs(
    pageColor,
    fontFamily,
    fontSize,
  );

  // Manage initial CFI application
  // Refs are stable objects and don't need to be in deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const { applyInitialCfi } = useInitialCfi(
    initialCfi,
    renditionRef,
    isNavigatingRef,
    locationRef,
    setLocation,
  );

  // Update theme colors and fonts when they change
  useEpubTheme({
    renditionRef,
    locationRef,
    isNavigatingRef,
    pageColor,
    fontFamily,
    fontSize,
  });

  // Update spread layout when pageLayout changes
  useEpubLayout({
    renditionRef,
    pageLayout,
  });

  // Calculate paging info when location changes
  const updatePagingInfo = usePagingInfo({
    renditionRef,
    tocRef,
    onPagingInfoChange,
  });

  // Handle location changes and calculate progress
  // Refs are stable objects and don't need to be in deps
  // We access refs inside the callback, which is the correct pattern
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const handleLocationChanged = useMemo(() => {
    const baseHandler = createLocationChangedHandler({
      isNavigatingRef,
      location,
      setLocation,
      bookRef,
      onLocationChange,
      isInitialLoadRef,
      progressCalculationTimeoutRef,
    } satisfies LocationChangedHandlerOptions);

    return (loc: string) => {
      baseHandler(loc);
      updatePagingInfo(loc);
    };
  }, [
    location,
    onLocationChange,
    bookRef,
    isInitialLoadRef,
    isNavigatingRef,
    progressCalculationTimeoutRef,
    setLocation,
    updatePagingInfo,
  ]);

  // Register jump to progress handler
  // Refs are stable objects and don't need to be in deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useJumpToProgress(
    {
      bookRef,
      renditionRef,
      isNavigatingRef,
      setLocation,
      onLocationChange,
    },
    onJumpToProgress,
  );

  // Register TOC toggle handler
  useTocToggle(reactReaderRef, onTocToggle);

  // Register jump to CFI handler
  useJumpToCfi({
    renditionRef,
    bookRef,
    isNavigatingRef,
    setLocation,
    onLocationChange,
    onJumpToCfi,
  });

  // Create rendition callback handler
  const handleGetRendition = useRenditionCallback({
    renditionRef,
    bookRef,
    initialCfi,
    applyInitialCfi,
    pageColor,
    fontFamily,
    fontSize,
    pageColorRef,
    fontFamilyRef,
    fontSizeRef,
    onLocationsReadyChange,
    onLocationChange,
    isInitialLoadRef,
  });

  // Create reader styles based on page color theme
  const readerStyles = useMemo(
    () => createReaderStyles(pageColor),
    [pageColor],
  );

  // Generate TOC hover styles based on theme
  const tocHoverStyles = useMemo(
    () => createTocHoverStyles(pageColor),
    [pageColor],
  );

  // Create epubOptions based on layout
  const epubOptions = useMemo(
    () => ({
      flow: "paginated" as const,
      spread: pageLayout === "single" ? ("none" as const) : ("auto" as const),
    }),
    [pageLayout],
  );

  // Handle search results
  const handleSearchResults = useEpubSearch({
    renditionRef,
    setLocation,
    onSearchResults,
  });

  // Cleanup timeout on unmount
  useProgressCleanup(progressCalculationTimeoutRef);

  if (isLoading) {
    return (
      <div
        className={cn(
          "flex h-full w-full items-center justify-center",
          className,
        )}
      >
        <span className="text-text-a40">Loading EPUB...</span>
      </div>
    );
  }

  if (isError || !bookArrayBuffer) {
    return (
      <div
        className={cn(
          "flex h-full w-full items-center justify-center",
          className,
        )}
      >
        <span className="text-text-a60">Error loading EPUB</span>
      </div>
    );
  }

  return (
    <div className={cn("h-full w-full", className)}>
      <style>{tocHoverStyles}</style>
      <ReactReader
        ref={reactReaderRef}
        url={bookArrayBuffer}
        location={location}
        locationChanged={handleLocationChanged}
        tocChanged={handleTocChanged}
        getRendition={handleGetRendition}
        epubInitOptions={createEpubInitOptions()}
        epubOptions={epubOptions}
        readerStyles={readerStyles}
        showToc={true}
        searchQuery={searchQuery}
        onSearchResults={onSearchResults ? handleSearchResults : undefined}
        contextLength={100}
      />
    </div>
  );
}
