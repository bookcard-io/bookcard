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

import { useCallback, useMemo, useRef } from "react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { useHeaderVisibility } from "@/hooks/useHeaderVisibility";
import { cn } from "@/libs/utils";
import { isComicFormat } from "@/utils/formatUtils";

import {
  type HeaderActionHandlers,
  HeaderActions,
} from "./components/HeaderActions";
import { HeaderTitle } from "./components/HeaderTitle";
import { HeaderTriggerZone } from "./components/HeaderTriggerZone";
import { ThemeSettingsOverlay } from "./components/ThemeSettingsOverlay";
import { useExclusivePanels } from "./hooks/useExclusivePanels";
import { useFontPanel } from "./hooks/useFontPanel";
import { usePanelCloseHandler } from "./hooks/usePanelCloseHandler";
import { useSearchPanel } from "./hooks/useSearchPanel";
import { useSeriesPanel } from "./hooks/useSeriesPanel";
import { ReadingSearchPanel } from "./ReadingSearchPanel";
import { ReadingSeriesPanel } from "./ReadingSeriesPanel";
import { SettingsPanelFactory } from "./SettingsPanelFactory";
import type {
  BookMetadata,
  ComicSettings,
  SearchSettings,
  ThemeSettings,
} from "./types";

export interface ReadingHeaderProps {
  /** Book metadata. */
  book: BookMetadata;
  /** Theme settings for EPUB/PDF formats. */
  theme?: ThemeSettings;
  /** Search settings. */
  search?: SearchSettings;
  /** Comic-specific settings (only used when format is comic). */
  comic?: ComicSettings;
  /** Callback when fullscreen toggle is clicked. */
  onFullscreenToggle?: () => void;
  /** Callback when TOC toggle is clicked. */
  onTocToggle?: () => void;
  /** Whether EPUB locations are ready (for EPUB format). */
  areLocationsReady?: boolean;
  /** Optional className. */
  className?: string;
}

/**
 * Self-hiding sticky header for reading page.
 *
 * Slides down on mouseover and slides up immediately on mouseout.
 * Displays book title centered.
 *
 * Follows SRP by delegating to specialized components.
 * Follows SOC by separating concerns into distinct components.
 * Follows IOC by accepting handlers as props.
 * Follows DRY by reusing HeaderButton and other components.
 * Follows OCP by using format detection utility and settings factory.
 *
 * Parameters
 * ----------
 * props : ReadingHeaderProps
 *     Component props including book metadata and grouped settings.
 */
export function ReadingHeader({
  book,
  theme,
  search,
  comic,
  onFullscreenToggle,
  onTocToggle,
  areLocationsReady = true,
  className,
}: ReadingHeaderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const fontPanel = useFontPanel();
  const searchPanel = useSearchPanel();
  const seriesPanel = useSeriesPanel();

  // Configure mutually exclusive panels
  // To disable mutual exclusivity, set enabled: false
  // To add more panels, add them to the panels array
  const { openFunctions } = useExclusivePanels({
    panels: [fontPanel, searchPanel, seriesPanel],
    enabled: true, // Set to false to allow multiple panels open simultaneously
  });

  // Extract open functions - we know these exist since we provided 3 panels
  const openFontPanel = openFunctions[0] ?? fontPanel.open;
  const openSearchPanel = openFunctions[1] ?? searchPanel.open;
  const openSeriesPanel = openFunctions[2] ?? seriesPanel.open;

  const { isVisible, handleMouseEnter, handleMouseLeave, hideHeader } =
    useHeaderVisibility(
      areLocationsReady,
      fontPanel.isOpen || searchPanel.isOpen || seriesPanel.isOpen,
    );

  // Use factory hook for panel close handlers (DRY)
  const handleFontPanelClose = usePanelCloseHandler(fontPanel, hideHeader);
  const handleSearchPanelClose = usePanelCloseHandler(searchPanel, hideHeader);
  const handleSeriesPanelClose = usePanelCloseHandler(seriesPanel, hideHeader);

  // Memoize no-op handlers to prevent unnecessary recreations
  const handleSearch = useCallback(() => {
    openSearchPanel();
  }, [openSearchPanel]);

  // Toggle series panel: if open, close it; if closed, open it
  const handleSeries = useCallback(() => {
    if (seriesPanel.isOpen) {
      handleSeriesPanelClose();
    } else {
      openSeriesPanel();
    }
  }, [seriesPanel.isOpen, openSeriesPanel, handleSeriesPanelClose]);

  const handleNotebook = useCallback(() => {
    // No-op for now
  }, []);

  const handleBookmark = useCallback(() => {
    // No-op for now
  }, []);

  const handleMoreOptions = useCallback(() => {
    // No-op for now
  }, []);

  const actionHandlers: HeaderActionHandlers = useMemo(
    () => ({
      onTocToggle,
      onSearch: handleSearch,
      onSeries: book.seriesName ? handleSeries : undefined,
      onFontSettings: openFontPanel,
      onNotebook: handleNotebook,
      onBookmark: handleBookmark,
      onFullscreenToggle,
      onMoreOptions: handleMoreOptions,
    }),
    [
      onTocToggle,
      handleSearch,
      book.seriesName,
      handleSeries,
      openFontPanel,
      handleNotebook,
      handleBookmark,
      onFullscreenToggle,
      handleMoreOptions,
    ],
  );

  const isComic = isComicFormat(book.format);

  return (
    <>
      <HeaderTriggerZone
        isVisible={isVisible}
        onMouseEnter={handleMouseEnter}
      />
      {/* biome-ignore lint/a11y/noStaticElementInteractions: Header uses hover for show/hide, not keyboard interaction */}
      <header
        ref={containerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className={cn(
          "fixed top-0 right-0 left-0 z-[800] transition-transform duration-300 ease-in-out",
          isVisible ? "translate-y-0" : "-translate-y-full",
          className,
        )}
      >
        <div className="border-surface-a20 border-b bg-surface-a0 px-4 py-3 backdrop-blur-sm">
          <div className="flex items-center justify-between">
            <BrandLogo showText={true} />
            <HeaderTitle title={book.title} />
            <HeaderActions
              handlers={actionHandlers}
              hideTocAndSearch={isComic}
            />
          </div>
        </div>
      </header>
      <SettingsPanelFactory
        format={book.format}
        isOpen={fontPanel.isOpen}
        onClose={handleFontPanelClose}
        pageColor={theme?.pageColor}
        onPageColorChange={theme?.onPageColorChange}
        onAppThemeChange={theme?.onAppThemeChange}
        theme={theme}
        comic={comic}
      />
      <ReadingSearchPanel
        isOpen={searchPanel.isOpen}
        onClose={handleSearchPanelClose}
        searchQuery={search?.searchQuery}
        onSearchQueryChange={search?.onSearchQueryChange}
        searchResults={search?.searchResults}
        onResultClick={search?.onResultClick}
      />
      <ThemeSettingsOverlay
        isVisible={seriesPanel.isOpen}
        onClick={handleSeriesPanelClose}
      />
      <ReadingSeriesPanel
        isOpen={seriesPanel.isOpen}
        onClose={handleSeriesPanelClose}
        seriesName={book.seriesName ?? null}
        currentBookId={book.bookId ?? 0}
      />
    </>
  );
}
