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

import { useCallback, useEffect, useState } from "react";
import { cn } from "@/libs/utils";

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
  /** Optional className. */
  className?: string;
}

/**
 * Slide-out theme settings panel for the reading page.
 *
 * Allows users to customize font family and font size.
 * Slides in from the right side with smooth animation.
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
  className,
}: ReadingThemeSettingsProps) {
  const [showOverlay, setShowOverlay] = useState(true);

  // Reset overlay visibility when panel opens
  useEffect(() => {
    if (isOpen) {
      setShowOverlay(true);
    }
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  const fontFamilies: FontFamily[] = [
    "Bookerly",
    "Amazon Ember",
    "OpenDyslexic",
  ];

  const handleFontSizeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newSize = parseFloat(e.target.value);
      onFontSizeChange(newSize);
    },
    [onFontSizeChange],
  );

  if (!isOpen) {
    return null;
  }

  return (
    <>
      {/* Overlay backdrop - starts below header, behind header */}
      {showOverlay && (
        <div
          className="fixed top-[69px] right-0 bottom-0 left-0 z-[750] bg-black/50 transition-opacity duration-300"
          onClick={handleOverlayClick}
          role="presentation"
          aria-hidden="true"
        />
      )}
      {/* Slide-out panel - starts below header */}
      <div
        className={cn(
          "fixed top-[69px] right-0 z-[901] h-[calc(100vh-64px)] w-96 bg-surface-a10 shadow-lg transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full",
          className,
        )}
        role="dialog"
        aria-modal="true"
        aria-label="Font settings"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key === "Escape") {
            e.stopPropagation();
          }
        }}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="border-surface-a20 border-b bg-surface-a10 px-6 py-4">
            <div className="flex items-center justify-between">
              <h2 className="font-medium text-lg text-text-a0">
                Reader Themes
              </h2>
              <button
                type="button"
                onClick={onClose}
                className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-2 text-text-a40 transition-colors hover:text-text-a0"
                aria-label="Close font settings"
              >
                <i className="pi pi-times text-lg" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 py-6">
            {/* Font Family Section */}
            <div className="mb-8">
              <h3 className="mb-4 font-medium text-sm text-text-a0">Font</h3>
              <div className="grid grid-cols-3 gap-3">
                {fontFamilies.map((family) => {
                  const isSelected = fontFamily === family;
                  return (
                    <button
                      key={family}
                      type="button"
                      onClick={() => onFontFamilyChange(family)}
                      className={cn(
                        "flex flex-col items-center gap-2 rounded-md border p-2 transition-colors",
                        isSelected
                          ? "border-primary-a0 bg-primary-a0/10"
                          : "border-surface-a20 bg-surface-a10 hover:border-surface-a30 hover:bg-surface-a20",
                      )}
                      aria-label={`Select ${family} font`}
                      aria-pressed={isSelected}
                    >
                      <div
                        className={cn(
                          "flex h-12 w-12 items-center justify-center rounded border text-3xl",
                          isSelected
                            ? "border-primary-a0 bg-primary-a0/20 text-primary-a0"
                            : "border-surface-a30 bg-surface-a20 text-text-a40",
                        )}
                        style={{
                          fontFamily: `${family}, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`,
                        }}
                      >
                        Aa
                      </div>
                      <span
                        className={cn(
                          "text-xs",
                          isSelected ? "text-primary-a0" : "text-text-a40",
                        )}
                      >
                        {family}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Font Size Section */}
            <div className="mb-8">
              <h3 className="mb-4 font-medium text-sm text-text-a0">
                Font Size
              </h3>
              <div className="flex items-center gap-4">
                <span className="text-sm text-text-a40">A</span>
                <div className="relative flex-1">
                  <input
                    type="range"
                    min="12"
                    max="24"
                    step="1"
                    value={fontSize}
                    onChange={handleFontSizeChange}
                    className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-surface-a20 accent-primary-a0"
                    style={{
                      background: `linear-gradient(to right, var(--clr-primary-a0) 0%, var(--clr-primary-a0) ${((fontSize - 12) / (24 - 12)) * 100}%, var(--clr-surface-a20) ${((fontSize - 12) / (24 - 12)) * 100}%, var(--clr-surface-a20) 100%)`,
                    }}
                    aria-label="Font size"
                  />
                </div>
                <span className="text-2xl text-text-a40">A</span>
                <span className="min-w-[3rem] text-right text-sm text-text-a0">
                  {fontSize}px
                </span>
              </div>
            </div>

            {/* Page Color Section */}
            <div>
              <h3 className="mb-4 font-medium text-sm text-text-a0">
                Page Color
              </h3>
              <div className="flex items-center gap-4">
                {/* Light theme circle */}
                <button
                  type="button"
                  onClick={() => {
                    onPageColorChange?.("light");
                    onAppThemeChange?.("light");
                    setShowOverlay(false);
                  }}
                  className={cn(
                    "h-12 w-12 cursor-pointer rounded-full border-2 transition-all",
                    pageColor === "light"
                      ? "border-primary-a0 ring-2 ring-primary-a0 ring-offset-2"
                      : "border-surface-a30 hover:border-surface-a40",
                  )}
                  style={{
                    backgroundColor: "var(--clr-surface-a0)",
                  }}
                  aria-label="Light theme"
                  aria-pressed={pageColor === "light"}
                />
                {/* Dark theme circle */}
                <button
                  type="button"
                  onClick={() => {
                    onPageColorChange?.("dark");
                    onAppThemeChange?.("dark");
                    setShowOverlay(false);
                  }}
                  className={cn(
                    "h-12 w-12 cursor-pointer rounded-full border-2 transition-all",
                    pageColor === "dark"
                      ? "border-primary-a0 ring-2 ring-primary-a0 ring-offset-2"
                      : "border-surface-a30 hover:border-surface-a40",
                  )}
                  style={{
                    backgroundColor: "#000",
                  }}
                  aria-label="Dark theme"
                  aria-pressed={pageColor === "dark"}
                />
                {/* Sepia circle */}
                <button
                  type="button"
                  onClick={() => {
                    onPageColorChange?.("sepia");
                    onAppThemeChange?.("light");
                    setShowOverlay(false);
                  }}
                  className={cn(
                    "h-12 w-12 cursor-pointer rounded-full border-2 transition-all",
                    pageColor === "sepia"
                      ? "border-primary-a0 ring-2 ring-primary-a0 ring-offset-2"
                      : "border-surface-a30 hover:border-surface-a40",
                  )}
                  style={{
                    backgroundColor: "#f4e4c1",
                  }}
                  aria-label="Sepia theme"
                  aria-pressed={pageColor === "sepia"}
                />
                {/* Light green circle */}
                <button
                  type="button"
                  onClick={() => {
                    onPageColorChange?.("lightGreen");
                    onAppThemeChange?.("light");
                    setShowOverlay(false);
                  }}
                  className={cn(
                    "h-12 w-12 cursor-pointer rounded-full border-2 transition-all",
                    pageColor === "lightGreen"
                      ? "border-primary-a0 ring-2 ring-primary-a0 ring-offset-2"
                      : "border-surface-a30 hover:border-surface-a40",
                  )}
                  style={{
                    backgroundColor: "#e8f5e9",
                  }}
                  aria-label="Light green theme"
                  aria-pressed={pageColor === "lightGreen"}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
