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

import type { ReactNode } from "react";
import { cn } from "@/libs/utils";

export interface ThemeSettingsPanelProps {
  /** Whether the panel is open. */
  isOpen: boolean;
  /** Callback when the panel should be closed. */
  onClose: () => void;
  /** Panel content. */
  children: ReactNode;
  /** Optional className. */
  className?: string;
  /** Optional header title. Defaults to "Reader Themes". */
  title?: string;
  /** Optional aria-label for the dialog. Defaults to "Font settings". */
  ariaLabel?: string;
  /** Optional close button aria-label. Defaults to "Close font settings". */
  closeAriaLabel?: string;
}

/**
 * Theme settings panel container component.
 *
 * Provides the slide-out panel structure and header.
 * Follows SRP by handling only panel layout and structure.
 * Follows IOC by accepting children for content composition.
 *
 * Parameters
 * ----------
 * props : ThemeSettingsPanelProps
 *     Component props including open state and content.
 */
export function ThemeSettingsPanel({
  isOpen,
  onClose,
  children,
  className,
  title = "Reader Themes",
  ariaLabel = "Font settings",
  closeAriaLabel = "Close font settings",
}: ThemeSettingsPanelProps) {
  return (
    <div
      className={cn(
        "fixed top-[5rem] right-0 z-[901] h-[calc(100vh-64px)] w-96 bg-surface-a10 shadow-lg transition-transform duration-300 ease-in-out",
        isOpen ? "translate-x-0" : "translate-x-full",
        !isOpen && "pointer-events-none",
        className,
      )}
      role="dialog"
      aria-modal={isOpen}
      aria-label={ariaLabel}
      aria-hidden={!isOpen}
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
            <h2 className="font-medium text-lg text-text-a0">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              className="flex cursor-pointer items-center justify-center border-0 bg-transparent p-2 text-text-a40 transition-colors hover:text-text-a0"
              aria-label={closeAriaLabel}
            >
              <i className="pi pi-times text-lg" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">{children}</div>
      </div>
    </div>
  );
}
