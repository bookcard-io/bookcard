// Copyright (C) 2025 khoa and others
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

import { FontFamilySelector } from "./components/FontFamilySelector";
import { FontSizeSlider } from "./components/FontSizeSlider";
import { LayoutSelector, type PageLayout } from "./components/LayoutSelector";
import { PageColorSelector } from "./components/PageColorSelector";
import { ThemeSettingsOverlay } from "./components/ThemeSettingsOverlay";
import { ThemeSettingsPanel } from "./components/ThemeSettingsPanel";
import { useThemeSettingsPanel } from "./hooks/useThemeSettingsPanel";

export type FontFamily =
  | "Literata"
  | "Bookerly"
  | "Amazon Ember"
  | "OpenDyslexic"
  | "Georgia"
  | "Palatino"
  | "Times New Roman"
  | "Arial"
  | "Helvetica"
  | "Verdana"
  | "Courier New"
  | "Monaco";

export type PageColor = "light" | "dark" | "sepia" | "lightGreen";

export type { PageLayout };

export interface ReadingThemeSettingsProps {
  /** Whether the panel is open. */
  isOpen: boolean;
  /** Callback when the panel should be closed. */
  onClose: () => void;
  /** Current font family. */
  fontFamily: FontFamily;
  /** Callback when font family changes. */
  onFontFamilyChange: (family: FontFamily) => void;
  /** Current font size in pixels. */
  fontSize: number;
  /** Callback when font size changes. */
  onFontSizeChange: (size: number) => void;
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
 * Slide-out theme settings panel for the reading page.
 *
 * Allows users to customize font family, font size, and page color.
 * Slides in from the right side with smooth animation.
 *
 * Follows SRP by delegating to specialized components.
 * Follows SOC by separating concerns into components and hooks.
 * Follows IOC by accepting callbacks as props.
 * Follows DRY by reusing shared components.
 *
 * Parameters
 * ----------
 * props : ReadingThemeSettingsProps
 *     Component props including open state and callbacks.
 */
export function ReadingThemeSettings({
  isOpen,
  onClose,
  fontFamily,
  onFontFamilyChange,
  fontSize,
  onFontSizeChange,
  pageColor = "light",
  onPageColorChange,
  onAppThemeChange,
  pageLayout = "two-column",
  onPageLayoutChange,
  className,
}: ReadingThemeSettingsProps) {
  const { showOverlay, hideOverlay } = useThemeSettingsPanel({
    isOpen,
    onClose,
  });

  if (!isOpen) {
    return null;
  }

  return (
    <>
      <ThemeSettingsOverlay isVisible={showOverlay} onClick={onClose} />
      <ThemeSettingsPanel
        isOpen={isOpen}
        onClose={onClose}
        className={className}
      >
        <FontFamilySelector
          selectedFamily={fontFamily}
          onFamilyChange={onFontFamilyChange}
        />
        <FontSizeSlider
          fontSize={fontSize}
          onFontSizeChange={onFontSizeChange}
        />
        <PageColorSelector
          selectedColor={pageColor}
          onPageColorChange={onPageColorChange}
          onAppThemeChange={onAppThemeChange}
          onOverlayHide={hideOverlay}
        />
        <LayoutSelector
          selectedLayout={pageLayout}
          onLayoutChange={onPageLayoutChange || (() => {})}
        />
      </ThemeSettingsPanel>
    </>
  );
}
