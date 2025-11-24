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

import { useEffect, useRef } from "react";
import {
  READING_FONT_FAMILY_SETTING_KEY,
  READING_FONT_SIZE_SETTING_KEY,
  READING_PAGE_COLOR_SETTING_KEY,
  READING_PAGE_LAYOUT_SETTING_KEY,
} from "@/components/profile/config/configurationConstants";
import { useSetting } from "@/hooks/useSetting";
import type {
  FontFamily,
  PageColor,
  PageLayout,
} from "../ReadingThemeSettings";
import {
  getDefaultFontFamily,
  getDefaultFontSize,
  getDefaultPageColor,
  getDefaultPageLayout,
  isValidFontFamily,
  isValidPageColor,
  isValidPageLayout,
  parseFontSize,
} from "../utils/readingSettingsValidators";

export interface UseReadingSettingsResult {
  /** Current font family. */
  fontFamily: FontFamily;
  /** Callback to update font family. */
  setFontFamily: (family: FontFamily) => void;
  /** Current font size in pixels. */
  fontSize: number;
  /** Callback to update font size. */
  setFontSize: (size: number) => void;
  /** Current page color theme. */
  pageColor: PageColor;
  /** Callback to update page color. */
  setPageColor: (color: PageColor) => void;
  /** Current page layout. */
  pageLayout: PageLayout;
  /** Callback to update page layout. */
  setPageLayout: (layout: PageLayout) => void;
  /** Refs for current values (for callbacks that need latest values). */
  refs: {
    fontFamily: React.MutableRefObject<FontFamily>;
    fontSize: React.MutableRefObject<number>;
  };
}

/**
 * Custom hook for managing reading settings.
 *
 * Handles loading, validation, and persistence of reading settings.
 * Follows SRP by centralizing all reading settings management.
 * Follows IOC by using useSetting hook for persistence.
 * Follows DRY by eliminating duplicate validation logic.
 *
 * Returns
 * -------
 * UseReadingSettingsResult
 *     Current settings values, update functions, and refs.
 */
export function useReadingSettings(): UseReadingSettingsResult {
  // Load persisted settings
  const { value: persistedFontFamily, setValue: setPersistedFontFamily } =
    useSetting({
      key: READING_FONT_FAMILY_SETTING_KEY,
      defaultValue: getDefaultFontFamily(),
    });

  const { value: persistedFontSize, setValue: setPersistedFontSize } =
    useSetting({
      key: READING_FONT_SIZE_SETTING_KEY,
      defaultValue: getDefaultFontSize().toString(),
    });

  const { value: persistedPageColor, setValue: setPersistedPageColor } =
    useSetting({
      key: READING_PAGE_COLOR_SETTING_KEY,
      defaultValue: getDefaultPageColor(),
    });

  const { value: persistedPageLayout, setValue: setPersistedPageLayout } =
    useSetting({
      key: READING_PAGE_LAYOUT_SETTING_KEY,
      defaultValue: getDefaultPageLayout(),
    });

  // Validate and convert string settings to typed values
  const fontFamily: FontFamily = isValidFontFamily(persistedFontFamily)
    ? persistedFontFamily
    : getDefaultFontFamily();

  const fontSize = (() => {
    const parsed = parseFontSize(persistedFontSize);
    return parsed ?? getDefaultFontSize();
  })();

  const pageColor: PageColor = isValidPageColor(persistedPageColor)
    ? persistedPageColor
    : getDefaultPageColor();

  const pageLayout: PageLayout = isValidPageLayout(persistedPageLayout)
    ? persistedPageLayout
    : getDefaultPageLayout();

  // Refs for callbacks that need latest values
  const fontFamilyRef = useRef<FontFamily>(fontFamily);
  const fontSizeRef = useRef<number>(fontSize);

  // Keep refs in sync with validated values
  useEffect(() => {
    fontFamilyRef.current = fontFamily;
  }, [fontFamily]);

  useEffect(() => {
    fontSizeRef.current = fontSize;
  }, [fontSize]);

  // Update handlers
  const handleFontFamilyChange = (family: FontFamily) => {
    setPersistedFontFamily(family);
  };

  const handleFontSizeChange = (size: number) => {
    setPersistedFontSize(size.toString());
  };

  const handlePageColorChange = (color: PageColor) => {
    setPersistedPageColor(color);
  };

  const handlePageLayoutChange = (layout: PageLayout) => {
    setPersistedPageLayout(layout);
  };

  return {
    fontFamily,
    setFontFamily: handleFontFamilyChange,
    fontSize,
    setFontSize: handleFontSizeChange,
    pageColor,
    setPageColor: handlePageColorChange,
    pageLayout,
    setPageLayout: handlePageLayoutChange,
    refs: {
      fontFamily: fontFamilyRef,
      fontSize: fontSizeRef,
    },
  };
}
