"use client";

import { createContext, type ReactNode, useContext } from "react";
import type {
  ComicReadingDirection,
  ComicReadingMode,
} from "@/components/reading/ComicReader";
import { useComicSettings } from "@/components/reading/hooks/useComicSettings";
import { useReadingSettings } from "@/components/reading/hooks/useReadingSettings";
import type {
  FontFamily,
  PageColor,
  PageLayout,
} from "@/components/reading/ReadingThemeSettings";

interface ReadingSettingsContextValue {
  // General / EPUB
  fontFamily: FontFamily;
  setFontFamily: (family: FontFamily) => void;
  fontSize: number;
  setFontSize: (size: number) => void;
  pageColor: PageColor;
  setPageColor: (color: PageColor) => void;
  pageLayout: PageLayout;
  setPageLayout: (layout: PageLayout) => void;

  // Comic
  readingMode: ComicReadingMode;
  setReadingMode: (mode: ComicReadingMode) => void;
  readingDirection: ComicReadingDirection;
  setReadingDirection: (direction: ComicReadingDirection) => void;
  spreadMode: boolean;
  setSpreadMode: (enabled: boolean) => void;
  zoomLevel: number;
  setZoomLevel: (level: number) => void;
  resetComicSettings: () => void;
}

const ReadingSettingsContext =
  createContext<ReadingSettingsContextValue | null>(null);

interface ReadingSettingsProviderProps {
  children: ReactNode;
  bookId?: number;
  isComic?: boolean;
}

export function ReadingSettingsProvider({
  children,
  bookId,
  isComic = false,
}: ReadingSettingsProviderProps) {
  // Always initialize general settings
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

  // Always initialize comic settings, but potentially with no bookId if not comic
  // Note: We might want to pass bookId even if not comic if we want per-book comic settings
  // to be ready if we switch formats, but usually format is fixed per page load.
  const comicSettings = useComicSettings({
    bookId: isComic ? bookId : undefined,
  });

  const value: ReadingSettingsContextValue = {
    fontFamily,
    setFontFamily,
    fontSize,
    setFontSize,
    pageColor,
    setPageColor,
    pageLayout,
    setPageLayout,

    readingMode: comicSettings.readingMode,
    setReadingMode: comicSettings.setReadingMode,
    readingDirection: comicSettings.readingDirection,
    setReadingDirection: comicSettings.setReadingDirection,
    spreadMode: comicSettings.spreadMode,
    setSpreadMode: comicSettings.setSpreadMode,
    zoomLevel: comicSettings.zoomLevel,
    setZoomLevel: comicSettings.setZoomLevel,
    resetComicSettings: comicSettings.resetSettings,
  };

  return (
    <ReadingSettingsContext.Provider value={value}>
      {children}
    </ReadingSettingsContext.Provider>
  );
}

export function useReadingSettingsContext() {
  const context = useContext(ReadingSettingsContext);
  if (!context) {
    throw new Error(
      "useReadingSettingsContext must be used within a ReadingSettingsProvider",
    );
  }
  return context;
}
