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

import type { Rendition } from "epubjs";
import type { RefObject } from "react";
import { useEffect } from "react";
import type { PageLayout } from "../ReadingThemeSettings";

/**
 * Options for useEpubLayout hook.
 */
export interface UseEpubLayoutOptions {
  /** Ref to rendition instance. */
  renditionRef: RefObject<Rendition | undefined>;
  /** Page layout (single or two-column). */
  pageLayout: PageLayout;
}

/**
 * Hook to manage EPUB page layout (spread) settings.
 *
 * Updates the rendition spread setting when pageLayout changes.
 * Follows SRP by focusing solely on layout management.
 * Follows IOC by accepting dependencies as parameters.
 *
 * Parameters
 * ----------
 * options : UseEpubLayoutOptions
 *     Hook options including ref and layout value.
 */
export function useEpubLayout({
  renditionRef,
  pageLayout,
}: UseEpubLayoutOptions): void {
  useEffect(() => {
    const rendition = renditionRef.current;
    if (!rendition) {
      return;
    }

    const spreadValue = pageLayout === "single" ? "none" : "auto";
    rendition.spread(spreadValue);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageLayout, renditionRef]);
}
