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

import type { Book, Contents, Rendition } from "epubjs";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ReactReader } from "react-reader";
import { useEPUBBook } from "@/hooks/useEPUBBook";
import { cn } from "@/libs/utils";
import { calculateProgressFromCfi } from "@/utils/epubLocation";
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
  applyDocumentTheme,
  applyThemeToRendition,
  ensureFontFacesInjected,
} from "@/utils/epubRendering";
import { getThemeColors } from "@/utils/readingTheme";
import { useEpubUrl } from "./hooks/useEpubUrl";
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
  // Store current theme values in refs so content hook can access latest values
  const pageColorRef = useRef<PageColor>(pageColor);
  const fontFamilyRef = useRef<FontFamily>(fontFamily);
  const fontSizeRef = useRef<number>(fontSize);

  const downloadUrl = useEpubUrl(url, bookId);

  // Fetch book as ArrayBuffer using hook
  const { bookArrayBuffer, isLoading, isError } = useEPUBBook(downloadUrl);

  // Track if we've applied initial CFI to avoid re-applying
  const hasAppliedInitialCfiRef = useRef(false);
  const locationRef = useRef<string | number>(location);

  // Update location ref when location changes (for use in other effects)
  useEffect(() => {
    locationRef.current = location;
  }, [location]);

  // Apply initialCfi only once when both initialCfi and rendition are available
  // NOTE: We intentionally don't include 'location' in deps to avoid resetting on page turns
  // The effect should only run when initialCfi changes, not when location changes
  useEffect(() => {
    // Only apply if:
    // 1. We have an initialCfi
    // 2. We haven't applied it yet
    // 3. Rendition is ready
    // 4. We're not currently navigating
    if (
      initialCfi &&
      !hasAppliedInitialCfiRef.current &&
      renditionRef.current &&
      !isNavigatingRef.current
    ) {
      const currentLocation = locationRef.current;
      // If location already matches initialCfi (from initialization), just mark as applied
      if (
        typeof currentLocation === "string" &&
        currentLocation === initialCfi
      ) {
        hasAppliedInitialCfiRef.current = true;
      } else if (
        currentLocation === 0 ||
        typeof currentLocation === "number" ||
        (typeof currentLocation === "string" && currentLocation !== initialCfi)
      ) {
        // Apply initialCfi if location is at initial value or doesn't match
        hasAppliedInitialCfiRef.current = true;
        isNavigatingRef.current = true;
        setLocation(initialCfi);
        // Reset flag after a short delay
        setTimeout(() => {
          isNavigatingRef.current = false;
        }, 100);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialCfi]); // Only depend on initialCfi, not location - this prevents resetting on page turns

  // Update refs when theme values change
  useEffect(() => {
    pageColorRef.current = pageColor;
    fontFamilyRef.current = fontFamily;
    fontSizeRef.current = fontSize;
  }, [pageColor, fontFamily, fontSize]);

  // Update theme colors and fonts when they change
  // NOTE: We use locationRef to access location without including it in deps to avoid interfering with page turns
  useEffect(() => {
    if (!renditionRef.current) {
      return;
    }

    const rendition = renditionRef.current;
    applyThemeToRendition(rendition, pageColor, fontFamily, fontSize);

    // Force refresh of the current page to apply theme changes immediately
    // Use the current location from ref, but only refresh if we have a valid location
    const currentLocation = locationRef.current;
    if (currentLocation && typeof currentLocation === "string") {
      try {
        // Use a small delay to ensure overrides are applied before refresh
        // Only refresh if we're not currently navigating (to avoid interfering with page turns)
        if (!isNavigatingRef.current) {
          setTimeout(() => {
            if (!isNavigatingRef.current && renditionRef.current) {
              renditionRef.current.display(currentLocation);
            }
          }, 50);
        }
      } catch (error) {
        console.warn("Could not refresh page for theme update:", error);
      }
    }
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
  const handleGetRendition = useCallback(
    (rendition: Rendition) => {
      renditionRef.current = rendition;
      bookRef.current = rendition.book;

      // Apply initialCfi if we have one and haven't applied it yet
      // This ensures the saved page is displayed when the rendition becomes ready
      if (
        initialCfi &&
        !hasAppliedInitialCfiRef.current &&
        !isNavigatingRef.current
      ) {
        // Always apply initialCfi when rendition becomes ready, even if location was initialized with it
        // This ensures ReactReader receives the location prop after it's ready to display it
        hasAppliedInitialCfiRef.current = true;
        isNavigatingRef.current = true;
        setLocation(initialCfi);
        // Reset flag after a short delay
        setTimeout(() => {
          isNavigatingRef.current = false;
        }, 100);
      }

      // Apply initial theme
      applyThemeToRendition(rendition, pageColor, fontFamily, fontSize);

      // Register content hook to ensure styles are applied to all pages
      // Use refs to access latest theme values since hook closure captures initial values
      rendition.hooks.content.register((contents: Contents) => {
        // Get latest values from refs
        const currentPageColor = pageColorRef.current;
        const currentFontFamily = fontFamilyRef.current;
        const currentFontSize = fontSizeRef.current;

        const document = contents.window.document;
        if (!document) {
          return;
        }

        ensureFontFacesInjected(document);

        // Apply current theme settings using latest values from refs
        const currentColors = getThemeColors(currentPageColor);

        // Apply theme overrides using latest values
        applyThemeToRendition(
          rendition,
          currentPageColor,
          currentFontFamily,
          currentFontSize,
        );

        applyDocumentTheme(document, currentColors);
      });

      // Generate locations and notify when ready
      if (bookRef.current?.locations && onLocationsReadyChange) {
        bookRef.current.locations.generate(200).then(() => {
          onLocationsReadyChange(true);

          // If we have an initial CFI, calculate progress from it now that locations are ready
          if (initialCfi && onLocationChange) {
            try {
              const book = bookRef.current;
              if (book) {
                const calculatedProgress = calculateProgressFromCfi(
                  book,
                  initialCfi,
                );
                // Update with calculated progress, but skip backend update (initial load)
                onLocationChange(
                  initialCfi,
                  calculatedProgress,
                  true, // Skip backend update during initial load
                );
              }
            } catch (error) {
              console.warn(
                "Error calculating initial progress from CFI:",
                error,
              );
            }
          }

          // Mark initial load as complete after locations are ready
          setTimeout(() => {
            isInitialLoadRef.current = false;
          }, 500);
        });
      } else if (onLocationsReadyChange) {
        onLocationsReadyChange(false);
        setTimeout(() => {
          isInitialLoadRef.current = false;
        }, 500);
      } else {
        setTimeout(() => {
          isInitialLoadRef.current = false;
        }, 500);
      }
    },
    [
      fontFamily,
      fontSize,
      pageColor,
      onLocationsReadyChange,
      initialCfi,
      onLocationChange,
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
        epubInitOptions={{
          openAs: "binary",
          // Prevent epubjs from making external HTTP requests
          requestMethod: (url: string) => {
            if (
              typeof url === "string" &&
              (url.startsWith("http://") ||
                url.startsWith("https://") ||
                url.startsWith("/"))
            ) {
              return Promise.reject(
                new Error("Resource should be loaded from EPUB archive"),
              );
            }
            return Promise.reject(
              new Error("All EPUB resources must come from the archive"),
            );
          },
        }}
        readerStyles={readerStyles}
        showToc={true}
      />
    </div>
  );
}
