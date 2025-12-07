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

import { withDefault } from "@/utils/callbackUtils";
import { isComicFormat } from "@/utils/formatUtils";

import { ComicReadingSettings } from "./ComicReadingSettings";
import { READING_DEFAULTS } from "./constants";
import { ReadingThemeSettings } from "./ReadingThemeSettings";
import type { ComicSettings, SettingsPanelProps, ThemeSettings } from "./types";

export interface SettingsPanelFactoryProps extends SettingsPanelProps {
  /** Book format to determine which settings panel to render. */
  format?: string;
  /** Theme settings for EPUB/PDF formats. */
  theme?: ThemeSettings;
  /** Comic settings for comic formats. */
  comic?: ComicSettings;
}

/**
 * Factory component for rendering format-appropriate settings panels.
 *
 * Follows LSP by using polymorphic rendering based on format type.
 * Follows OCP by allowing easy extension for new formats without modifying this component.
 * Follows SRP by delegating rendering to specialized components.
 *
 * Parameters
 * ----------
 * props : SettingsPanelFactoryProps
 *     Props including format, theme settings, and comic settings.
 */
export function SettingsPanelFactory({
  format,
  isOpen,
  onClose,
  pageColor,
  onPageColorChange,
  onAppThemeChange,
  theme,
  comic,
}: SettingsPanelFactoryProps) {
  const isComic = isComicFormat(format);

  if (isComic) {
    return (
      <ComicReadingSettings
        isOpen={isOpen}
        onClose={onClose}
        readingMode={comic?.readingMode || "paged"}
        onReadingModeChange={withDefault(comic?.onReadingModeChange)}
        readingDirection={comic?.readingDirection || "ltr"}
        onReadingDirectionChange={withDefault(comic?.onReadingDirectionChange)}
        spreadMode={comic?.spreadMode ?? READING_DEFAULTS.spreadMode}
        onSpreadModeChange={withDefault(comic?.onSpreadModeChange)}
        zoomLevel={comic?.zoomLevel || READING_DEFAULTS.zoomLevel}
        onZoomLevelChange={withDefault(comic?.onZoomLevelChange)}
        pageColor={pageColor}
        onPageColorChange={onPageColorChange}
        onAppThemeChange={onAppThemeChange}
      />
    );
  }

  return (
    <ReadingThemeSettings
      isOpen={isOpen}
      onClose={onClose}
      fontFamily={theme?.fontFamily || READING_DEFAULTS.fontFamily}
      onFontFamilyChange={withDefault(theme?.onFontFamilyChange)}
      fontSize={theme?.fontSize || READING_DEFAULTS.fontSize}
      onFontSizeChange={withDefault(theme?.onFontSizeChange)}
      pageColor={pageColor}
      onPageColorChange={onPageColorChange}
      onAppThemeChange={onAppThemeChange}
      pageLayout={theme?.pageLayout || READING_DEFAULTS.pageLayout}
      onPageLayoutChange={withDefault(theme?.onPageLayoutChange)}
    />
  );
}
