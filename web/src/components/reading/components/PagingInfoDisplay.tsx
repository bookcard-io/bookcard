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

import type { PagingInfo } from "../ReaderControls";
import { formatPagingText } from "../utils/pagingTextFormatter";

export interface PagingInfoDisplayProps {
  /** Paging information for display. */
  pagingInfo?: PagingInfo;
}

/**
 * Paging information display component.
 *
 * Follows SRP by focusing solely on displaying paging information.
 * Follows SOC by delegating formatting logic to utility function.
 *
 * Parameters
 * ----------
 * props : PagingInfoDisplayProps
 *     Component props including paging information.
 */
export function PagingInfoDisplay({ pagingInfo }: PagingInfoDisplayProps) {
  const pagingText = formatPagingText(pagingInfo);

  if (!pagingText) {
    return null;
  }

  return (
    <div className="flex justify-center">
      <span className="text-text-a40 text-xs">{pagingText}</span>
    </div>
  );
}
