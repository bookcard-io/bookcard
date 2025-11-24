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
import {
  type HeaderActionHandlers,
  HeaderActions,
} from "./components/HeaderActions";
import { HeaderTitle } from "./components/HeaderTitle";
import { HeaderTriggerZone } from "./components/HeaderTriggerZone";
import { useExclusivePanels } from "./hooks/useExclusivePanels";
import { useFontPanel } from "./hooks/useFontPanel";
import { useSearchPanel } from "./hooks/useSearchPanel";
import { ReadingSearchPanel } from "./ReadingSearchPanel";
import {
  type FontFamily,
  type PageColor,
  type PageLayout,
  ReadingThemeSettings,
} from "./ReadingThemeSettings";

export interface ReadingHeaderProps {
  /** Book title to display. */
  title: string | null;
  /** Callback when fullscreen toggle is clicked. */
  onFullscreenToggle?: () => void;
  /** Callback when TOC toggle is clicked. */
  onTocToggle?: () => void;
  /** Whether EPUB locations are ready (for EPUB format). */
  areLocationsReady?: boolean;
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
 *
 * Parameters
 * ----------
 * props : ReadingHeaderProps
 *     Component props including book title and action handlers.
 */
export function ReadingHeader({
  title,
  onFullscreenToggle,
  onTocToggle,
  areLocationsReady = true,
  fontFamily = "Bookerly",
  onFontFamilyChange,
  fontSize = 16,
  onFontSizeChange,
  pageColor = "light",
  onPageColorChange,
  onAppThemeChange,
  pageLayout = "two-column",
  onPageLayoutChange,
  className,
}: ReadingHeaderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const fontPanel = useFontPanel();
  const searchPanel = useSearchPanel();

  // Configure mutually exclusive panels
  // To disable mutual exclusivity, set enabled: false
  // To add more panels, add them to the panels array
  const { openFunctions } = useExclusivePanels({
    panels: [fontPanel, searchPanel],
    enabled: true, // Set to false to allow multiple panels open simultaneously
  });

  // Extract open functions - we know these exist since we provided 2 panels
  const openFontPanel = openFunctions[0] ?? fontPanel.open;
  const openSearchPanel = openFunctions[1] ?? searchPanel.open;

  const { isVisible, handleMouseEnter, handleMouseLeave, hideHeader } =
    useHeaderVisibility(
      areLocationsReady,
      fontPanel.isOpen || searchPanel.isOpen,
    );

  const handleFontPanelClose = useCallback(() => {
    fontPanel.close();
    hideHeader();
  }, [fontPanel, hideHeader]);

  const handleSearchPanelClose = useCallback(() => {
    searchPanel.close();
    hideHeader();
  }, [searchPanel, hideHeader]);

  // Memoize no-op handlers to prevent unnecessary recreations
  const handleSearch = useCallback(() => {
    openSearchPanel();
  }, [openSearchPanel]);

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
      onFontSettings: openFontPanel,
      onNotebook: handleNotebook,
      onBookmark: handleBookmark,
      onFullscreenToggle,
      onMoreOptions: handleMoreOptions,
    }),
    [
      onTocToggle,
      handleSearch,
      openFontPanel,
      handleNotebook,
      handleBookmark,
      onFullscreenToggle,
      handleMoreOptions,
    ],
  );

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
            <HeaderTitle title={title} />
            <HeaderActions handlers={actionHandlers} />
          </div>
        </div>
      </header>
      <ReadingThemeSettings
        isOpen={fontPanel.isOpen}
        onClose={handleFontPanelClose}
        fontFamily={fontFamily}
        onFontFamilyChange={onFontFamilyChange || (() => {})}
        fontSize={fontSize}
        onFontSizeChange={onFontSizeChange || (() => {})}
        pageColor={pageColor}
        onPageColorChange={onPageColorChange}
        onAppThemeChange={onAppThemeChange}
        pageLayout={pageLayout}
        onPageLayoutChange={onPageLayoutChange}
      />
      <ReadingSearchPanel
        isOpen={searchPanel.isOpen}
        onClose={handleSearchPanelClose}
      />
    </>
  );
}
