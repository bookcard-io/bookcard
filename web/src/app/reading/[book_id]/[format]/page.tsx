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

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { EBookReader } from "@/components/reading/EBookReader";
import type { SearchResult } from "@/components/reading/EPUBReader";
import { useFullscreen } from "@/components/reading/hooks/useFullscreen";
import { ReadingHeader } from "@/components/reading/ReadingHeader";
import { parseReadingPageParams } from "@/components/reading/utils/parseReadingPageParams";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { LibraryLoadingProvider } from "@/contexts/LibraryLoadingContext";
import {
  ReadingSettingsProvider,
  useReadingSettingsContext,
} from "@/contexts/ReadingSettingsContext";
import { SelectedBooksProvider } from "@/contexts/SelectedBooksContext";
import { SettingsProvider } from "@/contexts/SettingsContext";
import { ShelvesProvider } from "@/contexts/ShelvesContext";
import { UserProvider } from "@/contexts/UserContext";
import { useBook } from "@/hooks/useBook";
import { useTheme } from "@/hooks/useTheme";
import { isComicFormat } from "@/utils/formatUtils";

interface ReadingPageProps {
  params: Promise<{ book_id: string; format: string }>;
}

/**
 * Reading page for e-book reader.
 *
 * Displays the e-book reader for a specific book and format.
 * Manages reading session and progress tracking.
 * Follows SRP by delegating to specialized components and hooks.
 * Follows SOC by separating params parsing, settings, and UI concerns.
 */
export default function ReadingPage({ params }: ReadingPageProps) {
  const router = useRouter();
  const [bookId, setBookId] = useState<number | null>(null);
  const [format, setFormat] = useState<string | null>(null);

  useEffect(() => {
    void params.then((p) => {
      const parsed = parseReadingPageParams(p);
      if (parsed) {
        setBookId(parsed.bookId);
        setFormat(parsed.format);
      } else {
        router.push("/");
      }
    });
  }, [params, router]);

  const { book } = useBook({
    bookId: bookId || 0,
    enabled: bookId !== null,
    full: false,
  });

  if (!bookId || !format) {
    return (
      <div className="flex h-screen items-center justify-center">
        <span className="text-text-a40">Loading...</span>
      </div>
    );
  }

  const isComic = isComicFormat(format);

  return (
    <UserProvider>
      <SettingsProvider>
        <ActiveLibraryProvider>
          <LibraryLoadingProvider>
            <SelectedBooksProvider>
              <ShelvesProvider>
                <ReadingSettingsProvider bookId={bookId} isComic={isComic}>
                  <ReadingPageContent
                    bookId={bookId}
                    format={format}
                    bookTitle={book?.title || null}
                    seriesName={book?.series || null}
                  />
                </ReadingSettingsProvider>
              </ShelvesProvider>
            </SelectedBooksProvider>
          </LibraryLoadingProvider>
        </ActiveLibraryProvider>
      </SettingsProvider>
    </UserProvider>
  );
}

/**
 * Reading page content component.
 *
 * Manages reading UI state and coordinates between header and reader.
 * Follows SRP by delegating settings and fullscreen management to hooks.
 * Follows IOC by using injected hooks for state management.
 * Follows SOC by separating concerns into specialized hooks.
 *
 * Parameters
 * ----------
 * bookId : number
 *     The book ID to display.
 * format : string
 *     The book format (EPUB, PDF, etc.).
 * bookTitle : string | null
 *     The book title to display in the header.
 */
function ReadingPageContent({
  bookId,
  format,
  bookTitle,
  seriesName,
}: {
  bookId: number;
  format: string;
  bookTitle: string | null;
  seriesName: string | null;
}) {
  const { theme: appTheme, toggleTheme } = useTheme();
  const tocToggleRef = useRef<(() => void) | null>(null);
  const [areLocationsReady, setAreLocationsReady] = useState(false);

  // Manage search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const jumpToCfiRef = useRef<((cfi: string) => void) | null>(null);

  // Handle search results
  const handleSearchResults = useCallback((results: SearchResult[]) => {
    setSearchResults(results);
  }, []);

  // Handle result click to navigate to CFI
  const handleResultClick = useCallback((cfi: string) => {
    if (jumpToCfiRef.current) {
      jumpToCfiRef.current(cfi);
    } else {
      // eslint-disable-next-line no-console
      console.warn("jumpToCfi handler not ready yet");
    }
  }, []);

  // Detect if format is a comic
  const isComic = isComicFormat(format);

  // Manage reading settings via centralized hook
  const {
    fontFamily,
    setFontFamily,
    fontSize,
    setFontSize,
    pageColor,
    setPageColor,
    pageLayout,
    setPageLayout,
    readingMode,
    setReadingMode,
    readingDirection,
    setReadingDirection,
    spreadMode,
    setSpreadMode,
    zoomLevel,
    setZoomLevel,
  } = useReadingSettingsContext();

  // Manage fullscreen state via dedicated hook
  const { toggleFullscreen } = useFullscreen();

  // TOC toggle handler
  const handleTocToggle = useCallback(() => {
    tocToggleRef.current?.();
  }, []);

  // App theme change handler
  const handleAppThemeChange = useCallback(
    (newTheme: "light" | "dark") => {
      // Only toggle if the theme is different from current
      if (newTheme !== appTheme) {
        toggleTheme();
      }
    },
    [appTheme, toggleTheme],
  );

  return (
    <>
      <ReadingHeader
        book={{
          title: bookTitle,
          seriesName: seriesName || undefined,
          format,
          bookId,
        }}
        theme={{
          fontFamily,
          onFontFamilyChange: setFontFamily,
          fontSize,
          onFontSizeChange: setFontSize,
          pageColor,
          onPageColorChange: setPageColor,
          onAppThemeChange: handleAppThemeChange,
          pageLayout,
          onPageLayoutChange: setPageLayout,
        }}
        search={{
          searchQuery,
          onSearchQueryChange: setSearchQuery,
          searchResults,
          onResultClick: handleResultClick,
        }}
        comic={
          isComic
            ? {
                readingMode,
                onReadingModeChange: setReadingMode,
                readingDirection,
                onReadingDirectionChange: setReadingDirection,
                spreadMode,
                onSpreadModeChange: setSpreadMode,
                zoomLevel,
                onZoomLevelChange: setZoomLevel,
              }
            : undefined
        }
        onFullscreenToggle={toggleFullscreen}
        onTocToggle={handleTocToggle}
        areLocationsReady={areLocationsReady}
      />
      <EBookReader
        bookId={bookId}
        format={format}
        onTocToggle={(handler) => {
          tocToggleRef.current = handler;
        }}
        onLocationsReadyChange={setAreLocationsReady}
        searchQuery={searchQuery}
        onSearchResults={handleSearchResults}
        onJumpToCfi={(handler) => {
          jumpToCfiRef.current = handler;
        }}
      />
    </>
  );
}
