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

import type { ComicReadingDirection, ComicReadingMode } from "./ComicReader";
import { PageColorSelector } from "./components/PageColorSelector";
import { ReadingDirectionSelector } from "./components/ReadingDirectionSelector";
import { ReadingModeSelector } from "./components/ReadingModeSelector";
import { SpreadModeToggle } from "./components/SpreadModeToggle";
import { ThemeSettingsOverlay } from "./components/ThemeSettingsOverlay";
import { ThemeSettingsPanel } from "./components/ThemeSettingsPanel";
import { ZoomLevelSlider } from "./components/ZoomLevelSlider";
import { useThemeSettingsPanel } from "./hooks/useThemeSettingsPanel";
import type { PageColor } from "./ReadingThemeSettings";

export interface ComicReadingSettingsProps {
  /** Whether the panel is open. */
  isOpen: boolean;
  /** Callback when the panel should be closed. */
  onClose: () => void;
  /** Current reading mode. */
  readingMode: ComicReadingMode;
  /** Callback when reading mode changes. */
  onReadingModeChange: (mode: ComicReadingMode) => void;
  /** Current reading direction. */
  readingDirection: ComicReadingDirection;
  /** Callback when reading direction changes. */
  onReadingDirectionChange: (direction: ComicReadingDirection) => void;
  /** Whether spread mode is enabled. */
  spreadMode: boolean;
  /** Callback when spread mode changes. */
  onSpreadModeChange: (enabled: boolean) => void;
  /** Current zoom level. */
  zoomLevel: number;
  /** Callback when zoom level changes. */
  onZoomLevelChange: (level: number) => void;
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
 * Slide-out comic reading settings panel.
 *
 * Allows users to customize reading mode, direction, spread mode, zoom, and page color.
 * Slides in from the right side with smooth animation.
 *
 * Follows SRP by delegating to specialized components.
 * Follows SOC by separating concerns into components and hooks.
 * Follows IOC by accepting callbacks as props.
 * Follows DRY by reusing shared components.
 *
 * Parameters
 * ----------
 * props : ComicReadingSettingsProps
 *     Component props including open state and callbacks.
 */
export function ComicReadingSettings({
  isOpen,
  onClose,
  readingMode,
  onReadingModeChange,
  readingDirection,
  onReadingDirectionChange,
  spreadMode,
  onSpreadModeChange,
  zoomLevel,
  onZoomLevelChange,
  pageColor = "light",
  onPageColorChange,
  onAppThemeChange,
  className,
}: ComicReadingSettingsProps) {
  const { showOverlay, hideOverlay } = useThemeSettingsPanel({
    isOpen,
    onClose,
  });

  return (
    <>
      <ThemeSettingsOverlay
        isVisible={showOverlay && isOpen}
        onClick={onClose}
      />
      <ThemeSettingsPanel
        isOpen={isOpen}
        onClose={onClose}
        title="Comic Settings"
        ariaLabel="Comic reading settings"
        closeAriaLabel="Close comic settings"
        className={className}
      >
        <ReadingModeSelector
          selectedMode={readingMode}
          onModeChange={onReadingModeChange}
        />
        {readingMode === "paged" && (
          <ReadingDirectionSelector
            selectedDirection={readingDirection}
            onDirectionChange={onReadingDirectionChange}
          />
        )}
        {readingMode === "paged" && (
          <SpreadModeToggle
            enabled={spreadMode}
            onToggle={onSpreadModeChange}
          />
        )}
        <ZoomLevelSlider
          zoomLevel={zoomLevel}
          onZoomLevelChange={onZoomLevelChange}
        />
        <PageColorSelector
          selectedColor={pageColor}
          onPageColorChange={onPageColorChange}
          onAppThemeChange={onAppThemeChange}
          onOverlayHide={hideOverlay}
        />
      </ThemeSettingsPanel>
    </>
  );
}
