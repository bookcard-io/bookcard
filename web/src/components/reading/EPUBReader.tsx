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

import type { Book, Rendition } from "epubjs";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ReactReader } from "react-reader";
import { useEPUBBook } from "@/hooks/useEPUBBook";
import { cn } from "@/libs/utils";
import { createEpubInitOptions } from "@/utils/epubInitOptions";
import {
  createJumpToProgressHandler,
  createLocationChangedHandler,
  type JumpToProgressHandlerOptions,
  type LocationChangedHandlerOptions,
} from "@/utils/epubLocationHandlers";
import {
  createReaderStyles,
  createTocHoverStyles,
} from "@/utils/epubReaderStyles";
import {
  applyThemeToRendition,
  refreshPageForTheme,
} from "@/utils/epubRendering";
import { setupRendition } from "@/utils/epubRenditionSetup";
import { useEpubUrl } from "./hooks/useEpubUrl";
import { useInitialCfi } from "./hooks/useInitialCfi";
import { useThemeRefs } from "./hooks/useThemeRefs";
import type { FontFamily, PageColor } from "./ReadingThemeSettings";

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
  /** Font family. */
  fontFamily?: FontFamily;
  /** Font size in pixels. */
  fontSize?: number;
  /** Current theme. */
  theme?: "light" | "dark";
  /** Page color theme. */
  pageColor?: PageColor;
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
  fontFamily = "Bookerly",
  fontSize = 16,
  pageColor = "light",
  className,
}: EPUBReaderProps) {
  const [location, setLocation] = useState<string | number>(initialCfi || 0);
  const renditionRef = useRef<Rendition | undefined>(undefined);
  const bookRef = useRef<Book | null>(null);
  const reactReaderRef = useRef<ReactReader | null>(null);
  const isNavigatingRef = useRef(false);
  const progressCalculationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isInitialLoadRef = useRef(true);
  const locationRef = useRef<string | number>(location);

  const downloadUrl = useEpubUrl(url, bookId);

  // Fetch book as ArrayBuffer using hook
  const { bookArrayBuffer, isLoading, isError } = useEPUBBook(downloadUrl);

  // Manage theme refs for content hooks
  const { pageColorRef, fontFamilyRef, fontSizeRef } = useThemeRefs(
    pageColor,
    fontFamily,
    fontSize,
  );

  // Update location ref when location changes (for use in other effects)
  useEffect(() => {
    locationRef.current = location;
  }, [location]);

  // Manage initial CFI application
  const { applyInitialCfi } = useInitialCfi(
    initialCfi,
    renditionRef,
    isNavigatingRef,
    locationRef,
    setLocation,
  );

  // Update theme colors and fonts when they change
  // NOTE: We use locationRef to access location without including it in deps to avoid interfering with page turns
  useEffect(() => {
    if (!renditionRef.current) {
      return;
    }

    const rendition = renditionRef.current;
    applyThemeToRendition(rendition, pageColor, fontFamily, fontSize);

    // Force refresh of the current page to apply theme changes immediately
    refreshPageForTheme(rendition, locationRef.current, isNavigatingRef);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fontFamily, fontSize, pageColor]); // Removed 'location' from deps

  // Handle location changes and calculate progress
  const handleLocationChanged = useMemo(
    () =>
      createLocationChangedHandler({
        isNavigatingRef,
        location,
        setLocation,
        bookRef,
        onLocationChange,
        isInitialLoadRef,
        progressCalculationTimeoutRef,
      } satisfies LocationChangedHandlerOptions),
    [location, onLocationChange],
  );

  // Register jump to progress handler
  useEffect(() => {
    if (!onJumpToProgress) {
      return;
    }

    const jumpToProgress = createJumpToProgressHandler({
      bookRef,
      renditionRef,
      isNavigatingRef,
      setLocation,
      onLocationChange,
    } satisfies JumpToProgressHandlerOptions);

    onJumpToProgress(jumpToProgress);

    return () => {
      onJumpToProgress(null);
    };
  }, [onJumpToProgress, onLocationChange]);

  // Register TOC toggle handler
  useEffect(() => {
    if (!onTocToggle) {
      return;
    }

    const toggleToc = () => {
      // Call toggleToc method on ReactReader instance
      if (reactReaderRef.current?.toggleToc) {
        reactReaderRef.current.toggleToc();
      }
    };

    onTocToggle(toggleToc);

    return () => {
      onTocToggle(null);
    };
  }, [onTocToggle]);

  // Get rendition and apply initial settings
  // Refs are stable objects and don't need to be in deps
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const handleGetRendition = useCallback(
    (rendition: Rendition) => {
      renditionRef.current = rendition;

      setupRendition({
        rendition,
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
    },
    [
      fontFamily,
      fontSize,
      pageColor,
      onLocationsReadyChange,
      initialCfi,
      onLocationChange,
      applyInitialCfi,
      // Refs are stable objects - included only to satisfy exhaustive-deps
      pageColorRef,
      fontFamilyRef,
      fontSizeRef,
    ],
  );

  // Create reader styles based on page color theme
  const readerStyles = useMemo(() => {
    return createReaderStyles(pageColor);
  }, [pageColor]);

  // Generate TOC hover styles based on theme
  const tocHoverStyles = useMemo(() => {
    return createTocHoverStyles(pageColor);
  }, [pageColor]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (progressCalculationTimeoutRef.current) {
        clearTimeout(progressCalculationTimeoutRef.current);
      }
    };
  }, []);

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
        getRendition={handleGetRendition}
        epubInitOptions={createEpubInitOptions()}
        readerStyles={readerStyles}
        showToc={true}
      />
    </div>
  );
}
