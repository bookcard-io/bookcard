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

import { BookmarkOutline } from "@/icons/BookmarkOutline";
import { LetterCase } from "@/icons/LetterCase";
import { MaximizeStroke12 } from "@/icons/MaximizeStroke12";
import { Notebook } from "@/icons/Notebook";
import { HeaderButton } from "./HeaderButton";

export interface HeaderActionHandlers {
  /** Handler for TOC toggle action. */
  onTocToggle?: () => void;
  /** Handler for search action. */
  onSearch?: () => void;
  /** Handler for font settings action. */
  onFontSettings?: () => void;
  /** Handler for notebook action. */
  onNotebook?: () => void;
  /** Handler for bookmark action. */
  onBookmark?: () => void;
  /** Handler for fullscreen toggle action. */
  onFullscreenToggle?: () => void;
  /** Handler for more options action. */
  onMoreOptions?: () => void;
}

export interface HeaderActionsProps {
  /** Action handlers for header buttons. */
  handlers: HeaderActionHandlers;
}

/**
 * Header action buttons component.
 *
 * Follows SOC by separating action buttons from header layout.
 * Follows IOC by accepting handlers as props.
 * Follows DRY by using reusable HeaderButton component.
 *
 * Parameters
 * ----------
 * props : HeaderActionsProps
 *     Component props including action handlers.
 */
export function HeaderActions({ handlers }: HeaderActionsProps) {
  return (
    <div className="flex items-center gap-2">
      <HeaderButton
        onClick={handlers.onTocToggle}
        ariaLabel="Toggle table of contents"
      >
        <i className="pi pi-list text-lg" />
      </HeaderButton>
      <HeaderButton onClick={handlers.onSearch} ariaLabel="Search">
        <i className="pi pi-search text-lg" />
      </HeaderButton>
      <HeaderButton onClick={handlers.onFontSettings} ariaLabel="Letter case">
        <LetterCase className="h-5 w-5" />
      </HeaderButton>
      <HeaderButton onClick={handlers.onNotebook} ariaLabel="Notebook">
        <Notebook className="h-5 w-5" />
      </HeaderButton>
      <HeaderButton onClick={handlers.onBookmark} ariaLabel="Bookmark">
        <BookmarkOutline className="h-5 w-5" />
      </HeaderButton>
      <HeaderButton
        onClick={handlers.onFullscreenToggle}
        ariaLabel="Toggle fullscreen"
      >
        <MaximizeStroke12 className="h-5 w-5" />
      </HeaderButton>
      <HeaderButton onClick={handlers.onMoreOptions} ariaLabel="More options">
        <i className="pi pi-ellipsis-v text-lg" />
      </HeaderButton>
    </div>
  );
}
