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
import {
  READING_FONT_FAMILY_SETTING_KEY,
  READING_FONT_SIZE_SETTING_KEY,
  READING_PAGE_COLOR_SETTING_KEY,
} from "@/components/profile/config/configurationConstants";
import { EBookReader } from "@/components/reading/EBookReader";
import { ReadingHeader } from "@/components/reading/ReadingHeader";
import type {
  FontFamily,
  PageColor,
} from "@/components/reading/ReadingThemeSettings";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { LibraryLoadingProvider } from "@/contexts/LibraryLoadingContext";
import { SettingsProvider } from "@/contexts/SettingsContext";
import { UserProvider } from "@/contexts/UserContext";
import { useBook } from "@/hooks/useBook";
import { useSetting } from "@/hooks/useSetting";
import { useTheme } from "@/hooks/useTheme";

interface ReadingPageProps {
  params: Promise<{ book_id: string; format: string }>;
}

/**
 * Reading page for e-book reader.
 *
 * Displays the e-book reader for a specific book and format.
 * Manages reading session and progress tracking.
 * Follows SRP by delegating to EBookReader component.
 */
export default function ReadingPage({ params }: ReadingPageProps) {
  const router = useRouter();
  const [bookId, setBookId] = useState<number | null>(null);
  const [format, setFormat] = useState<string | null>(null);

  useEffect(() => {
    void params.then((p) => {
      const id = parseInt(p.book_id, 10);
      if (!Number.isNaN(id)) {
        setBookId(id);
      } else {
        router.push("/");
      }
      if (p.format) {
        setFormat(p.format.toUpperCase());
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

function ReadingPageContent({
  bookId,
  format,
  bookTitle,
}: {
  bookId: number;
  format: string;
  bookTitle: string | null;
}) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { theme: appTheme, toggleTheme } = useTheme();
  const tocToggleRef = useRef<(() => void) | null>(null);

  // Load persisted settings
  const { value: persistedFontFamily, setValue: setPersistedFontFamily } =
    useSetting({
      key: READING_FONT_FAMILY_SETTING_KEY,
      defaultValue: "Bookerly",
    });

  const { value: persistedFontSize, setValue: setPersistedFontSize } =
    useSetting({
      key: READING_FONT_SIZE_SETTING_KEY,
      defaultValue: "16",
    });

  const { value: persistedPageColor, setValue: setPersistedPageColor } =
    useSetting({
      key: READING_PAGE_COLOR_SETTING_KEY,
      defaultValue: "light",
    });

  // Validate and convert string settings to typed values
  const isValidFontFamily = (value: string): value is FontFamily => {
    const validFamilies: FontFamily[] = [
      "Literata",
      "Bookerly",
      "Amazon Ember",
      "OpenDyslexic",
      "Georgia",
      "Palatino",
      "Times New Roman",
      "Arial",
      "Helvetica",
      "Verdana",
      "Courier New",
      "Monaco",
    ];
    return validFamilies.includes(value as FontFamily);
  };

  const isValidPageColor = (value: string): value is PageColor => {
    return ["light", "dark", "sepia", "lightGreen"].includes(value);
  };

  const fontFamily: FontFamily = isValidFontFamily(persistedFontFamily)
    ? persistedFontFamily
    : "Bookerly";
  const fontSize = (() => {
    const parsed = parseInt(persistedFontSize, 10);
    return !Number.isNaN(parsed) && parsed >= 12 && parsed <= 24 ? parsed : 16;
  })();
  const pageColor: PageColor = isValidPageColor(persistedPageColor)
    ? persistedPageColor
    : "light";

  const fontFamilyRef = useRef<FontFamily>(fontFamily);
  const fontSizeRef = useRef<number>(fontSize);

  // Keep refs in sync with persisted values for EBookReader callbacks
  useEffect(() => {
    fontFamilyRef.current = fontFamily;
  }, [fontFamily]);

  useEffect(() => {
    fontSizeRef.current = fontSize;
  }, [fontSize]);

  const handleFullscreenToggle = useCallback(() => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setIsFullscreen(!isFullscreen);
  }, [isFullscreen]);

  const handleTocToggle = useCallback(() => {
    tocToggleRef.current?.();
  }, []);

  const handleFontFamilyChange = useCallback(
    (family: FontFamily) => {
      setPersistedFontFamily(family);
    },
    [setPersistedFontFamily],
  );

  const handleFontSizeChange = useCallback(
    (size: number) => {
      setPersistedFontSize(size.toString());
    },
    [setPersistedFontSize],
  );

  const handlePageColorChange = useCallback(
    (color: PageColor) => {
      setPersistedPageColor(color);
    },
    [setPersistedPageColor],
  );

  const handleAppThemeChange = useCallback(
    (newTheme: "light" | "dark") => {
      // Only toggle if the theme is different from current
      if (newTheme !== appTheme) {
        toggleTheme();
      }
    },
    [appTheme, toggleTheme],
  );

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  return (
    <>
      <ReadingHeader
        title={bookTitle}
        onFullscreenToggle={handleFullscreenToggle}
        onTocToggle={handleTocToggle}
        fontFamily={fontFamily}
        onFontFamilyChange={handleFontFamilyChange}
        fontSize={fontSize}
        onFontSizeChange={handleFontSizeChange}
        pageColor={pageColor}
        onPageColorChange={handlePageColorChange}
        onAppThemeChange={handleAppThemeChange}
      />
      <EBookReader
        bookId={bookId}
        format={format}
        onTocToggle={(handler) => {
          tocToggleRef.current = handler;
        }}
        fontFamily={fontFamily}
        fontSize={fontSize}
        pageColor={pageColor}
      />
    </>
  );
}
