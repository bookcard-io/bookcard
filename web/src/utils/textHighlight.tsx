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

import type React from "react";

/**
 * Highlight matching text in a string (case-insensitive).
 *
 * Parameters
 * ----------
 * text : str
 *     The text to highlight.
 * query : str
 *     The search query to highlight.
 * highlightClassName : str | undefined
 *     CSS class name for the highlight span (optional).
 *
 * Returns
 * -------
 * React.ReactNode
 *     JSX with highlighted text.
 */
export function highlightText(
  text: string,
  query: string,
  highlightClassName?: string,
): React.ReactNode {
  if (!query.trim()) {
    return text;
  }

  const queryLower = query.toLowerCase();
  const textLower = text.toLowerCase();
  const index = textLower.indexOf(queryLower);

  if (index === -1) {
    return text;
  }

  // Use the original text for the match to preserve case
  const before = text.slice(0, index);
  const match = text.slice(index, index + query.length);
  const after = text.slice(index + query.length);

  return (
    <>
      {before}
      <span className={highlightClassName || ""}>{match}</span>
      {after}
    </>
  );
}
