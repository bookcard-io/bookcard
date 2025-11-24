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

import type { NavItem, Rendition } from "epubjs";
import type { RefObject } from "react";
import type { PagingInfo } from "../ReaderControls";
import { calculatePagingInfo } from "../utils/epubPagingInfo";

/**
 * Options for usePagingInfo hook.
 */
export interface UsePagingInfoOptions {
  /** Ref to rendition instance. */
  renditionRef: RefObject<Rendition | undefined>;
  /** Ref to TOC items. */
  tocRef: RefObject<NavItem[]>;
  /** Callback when paging info changes. */
  onPagingInfoChange?: (info: PagingInfo | null) => void;
}

/**
 * Hook to calculate and update paging information.
 *
 * Follows SRP by focusing solely on paging info management.
 * Follows IOC by accepting dependencies as parameters.
 *
 * Parameters
 * ----------
 * options : UsePagingInfoOptions
 *     Hook options including refs and callback.
 *
 * Returns
 * -------
 * (location: string) => void
 *     Function to call when location changes to update paging info.
 */
export function usePagingInfo({
  renditionRef,
  tocRef,
  onPagingInfoChange,
}: UsePagingInfoOptions): (location: string) => void {
  return (_location: string) => {
    const rendition = renditionRef.current;
    const toc = tocRef.current;

    if (!rendition || !toc || toc.length === 0 || !onPagingInfoChange) {
      return;
    }

    const pagingInfo = calculatePagingInfo(rendition, toc);
    if (pagingInfo) {
      onPagingInfoChange(pagingInfo);
    }
  };
}
