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

import type { ComicReadingDirection, ComicReadingMode } from "./ComicReader";
import type { FontFamily, PageColor, PageLayout } from "./ReadingThemeSettings";

/**
 * Book metadata properties.
 *
 * Follows SRP by grouping related book information.
 */
export interface BookMetadata {
  /** Book title to display. */
  title: string | null;
  /** Name of the series if part of one. */
  seriesName?: string | null;
  /** Current book ID. */
  bookId?: number;
  /** Book format (EPUB, PDF, CBZ, etc.). */
  format?: string;
}

/**
 * Theme settings properties.
 *
 * Follows SRP by grouping theme-related configuration.
 */
export interface ThemeSettings {
  /** Current font family. */
  fontFamily?: FontFamily;
  /** Callback when font family changes. */
  onFontFamilyChange?: (family: FontFamily) => void;
  /** Current font size in pixels. */
  fontSize?: number;
  /** Callback when font size changes. */
  onFontSizeChange?: (size: number) => void;
  /** Current page color theme. */
  pageColor?: PageColor;
  /** Callback when page color changes. */
  onPageColorChange?: (color: PageColor) => void;
  /** Callback when main app theme should change. */
  onAppThemeChange?: (theme: "light" | "dark") => void;
  /** Current page layout. */
  pageLayout?: PageLayout;
  /** Callback when page layout changes. */
  onPageLayoutChange?: (layout: PageLayout) => void;
}

/**
 * Search settings properties.
 *
 * Follows SRP by grouping search-related configuration.
 */
export interface SearchSettings {
  /** Current search query. */
  searchQuery?: string;
  /** Callback when search query changes. */
  onSearchQueryChange?: (query: string) => void;
  /** Search results to display. */
  searchResults?: import("./EPUBReader").SearchResult[];
  /** Callback when a search result is clicked to navigate to it. */
  onResultClick?: (cfi: string) => void;
}

/**
 * Comic-specific settings properties.
 *
 * Follows SRP by grouping comic-related configuration.
 */
export interface ComicSettings {
  /** Current reading mode (comic). */
  readingMode?: ComicReadingMode;
  /** Callback when reading mode changes (comic). */
  onReadingModeChange?: (mode: ComicReadingMode) => void;
  /** Current reading direction (comic). */
  readingDirection?: ComicReadingDirection;
  /** Callback when reading direction changes (comic). */
  onReadingDirectionChange?: (direction: ComicReadingDirection) => void;
  /** Whether spread mode is enabled (comic). */
  spreadMode?: boolean;
  /** Callback when spread mode changes (comic). */
  onSpreadModeChange?: (enabled: boolean) => void;
  /** Current zoom level (comic). */
  zoomLevel?: number;
  /** Callback when zoom level changes (comic). */
  onZoomLevelChange?: (level: number) => void;
}

/**
 * Common settings panel props interface.
 *
 * Follows LSP by defining a common interface for different settings panels.
 * Allows polymorphic rendering of settings panels.
 */
export interface SettingsPanelProps {
  /** Whether the panel is open. */
  isOpen: boolean;
  /** Callback when the panel should be closed. */
  onClose: () => void;
  /** Current page color theme. */
  pageColor?: PageColor;
  /** Callback when page color changes. */
  onPageColorChange?: (color: PageColor) => void;
  /** Callback when main app theme should change. */
  onAppThemeChange?: (theme: "light" | "dark") => void;
}
