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

import { useCallback, useEffect, useRef, useState } from "react";
import { BrandLogo } from "@/components/common/BrandLogo";
import { BookmarkOutline } from "@/icons/BookmarkOutline";
import { LetterCase } from "@/icons/LetterCase";
import { MaximizeStroke12 } from "@/icons/MaximizeStroke12";
import { Notebook } from "@/icons/Notebook";
import { cn } from "@/libs/utils";
import {
  type FontFamily,
  type PageColor,
  ReadingThemeSettings,
} from "./ReadingThemeSettings";

export interface ReadingHeaderProps {
  /** Book title to display. */
  title: string | null;
  /** Callback when fullscreen toggle is clicked. */
  onFullscreenToggle?: () => void;
  /** Callback when TOC toggle is clicked. */
  onTocToggle?: () => void;
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
  /** Optional className. */
  className?: string;
}

/**
 * Self-hiding sticky header for reading page.
 *
 * Slides down on mouseover and slides up immediately on mouseout.
 * Displays book title centered.
 *
 * Parameters
 * ----------
 * props : ReadingHeaderProps
 *     Component props including book title.
 */
export function ReadingHeader({
  title,
  onFullscreenToggle,
  onTocToggle,
  fontFamily = "Bookerly",
  onFontFamilyChange,
  fontSize = 16,
  onFontSizeChange,
  pageColor = "light",
  onPageColorChange,
  onAppThemeChange,
  className,
}: ReadingHeaderProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isFontPanelOpen, setIsFontPanelOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerZoneRef = useRef<HTMLButtonElement>(null);

  // Show on mouse enter (hovering near top of page or header)
  const handleMouseEnter = () => {
    setIsVisible(true);
  };

  // Hide immediately on mouse leave, unless font panel is open
  const handleMouseLeave = () => {
    if (!isFontPanelOpen) {
      setIsVisible(false);
    }
  };

  // No-op handlers for menu items
  const handleSearch = useCallback(() => {
    // No-op for now
  }, []);

  const handleLetterCase = useCallback(() => {
    setIsFontPanelOpen(true);
  }, []);

  const handleNotebook = useCallback(() => {
    // No-op for now
  }, []);

  const handleBookmark = useCallback(() => {
    // No-op for now
  }, []);

  const handleEllipsis = useCallback(() => {
    // No-op for now
  }, []);

  // Keep header visible when font panel is open
  useEffect(() => {
    if (isFontPanelOpen) {
      setIsVisible(true);
    }
  }, [isFontPanelOpen]);

  return (
    <>
      {/* Invisible trigger zone at top of page to detect mouseover */}
      {!isVisible && (
        <button
          ref={triggerZoneRef}
          onMouseEnter={handleMouseEnter}
          type="button"
          className="fixed top-0 right-0 left-0 z-[850] h-8 cursor-default border-0 bg-transparent p-0"
          aria-hidden="true"
          tabIndex={-1}
        />
      )}
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
            <div className="-translate-x-1/2 absolute left-1/2">
              <h1 className="max-w-4xl truncate font-medium text-lg text-text-a0">
                {title || "Loading..."}
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onTocToggle}
                className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-3 text-text-a40 transition-colors hover:text-text-a0"
                aria-label="Toggle table of contents"
              >
                <i className="pi pi-list text-lg" />
              </button>
              <button
                type="button"
                onClick={handleSearch}
                className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-3 text-text-a40 transition-colors hover:text-text-a0"
                aria-label="Search"
              >
                <i className="pi pi-search text-lg" />
              </button>
              <button
                type="button"
                onClick={handleLetterCase}
                className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-3 text-text-a40 transition-colors hover:text-text-a0"
                aria-label="Letter case"
              >
                <LetterCase className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={handleNotebook}
                className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-3 text-text-a40 transition-colors hover:text-text-a0"
                aria-label="Notebook"
              >
                <Notebook className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={handleBookmark}
                className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-3 text-text-a40 transition-colors hover:text-text-a0"
                aria-label="Bookmark"
              >
                <BookmarkOutline className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={onFullscreenToggle}
                className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-3 text-text-a40 transition-colors hover:text-text-a0"
                aria-label="Toggle fullscreen"
              >
                <MaximizeStroke12 className="h-5 w-5" />
              </button>
              <button
                type="button"
                onClick={handleEllipsis}
                className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-3 text-text-a40 transition-colors hover:text-text-a0"
                aria-label="More options"
              >
                <i className="pi pi-ellipsis-v text-lg" />
              </button>
            </div>
          </div>
        </div>
      </header>
      <ReadingThemeSettings
        isOpen={isFontPanelOpen}
        onClose={() => {
          setIsFontPanelOpen(false);
          setIsVisible(false);
        }}
        fontFamily={fontFamily}
        onFontFamilyChange={onFontFamilyChange || (() => {})}
        fontSize={fontSize}
        onFontSizeChange={onFontSizeChange || (() => {})}
        pageColor={pageColor}
        onPageColorChange={onPageColorChange}
        onAppThemeChange={onAppThemeChange}
      />
    </>
  );
}
