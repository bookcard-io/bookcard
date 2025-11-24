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
import { useFullscreen } from "@/components/reading/hooks/useFullscreen";
import { useReadingSettings } from "@/components/reading/hooks/useReadingSettings";
import { ReadingHeader } from "@/components/reading/ReadingHeader";
import { parseReadingPageParams } from "@/components/reading/utils/parseReadingPageParams";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { LibraryLoadingProvider } from "@/contexts/LibraryLoadingContext";
import { SettingsProvider } from "@/contexts/SettingsContext";
import { UserProvider } from "@/contexts/UserContext";
import { useBook } from "@/hooks/useBook";
import { useTheme } from "@/hooks/useTheme";

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

  return (
    <UserProvider>
      <SettingsProvider>
        <ActiveLibraryProvider>
          <LibraryLoadingProvider>
            <ReadingPageContent
              bookId={bookId}
              format={format}
              bookTitle={book?.title || null}
            />
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
}: {
  bookId: number;
  format: string;
  bookTitle: string | null;
}) {
  const { theme: appTheme, toggleTheme } = useTheme();
  const tocToggleRef = useRef<(() => void) | null>(null);
  const [areLocationsReady, setAreLocationsReady] = useState(false);

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
  } = useReadingSettings();

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
        title={bookTitle}
        onFullscreenToggle={toggleFullscreen}
        onTocToggle={handleTocToggle}
        fontFamily={fontFamily}
        onFontFamilyChange={setFontFamily}
        fontSize={fontSize}
        onFontSizeChange={setFontSize}
        pageColor={pageColor}
        onPageColorChange={setPageColor}
        onAppThemeChange={handleAppThemeChange}
        pageLayout={pageLayout}
        onPageLayoutChange={setPageLayout}
        areLocationsReady={areLocationsReady}
      />
      <EBookReader
        bookId={bookId}
        format={format}
        onTocToggle={(handler) => {
          tocToggleRef.current = handler;
        }}
        onLocationsReadyChange={setAreLocationsReady}
        fontFamily={fontFamily}
        fontSize={fontSize}
        pageColor={pageColor}
        pageLayout={pageLayout}
      />
    </>
  );
}
