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

/**
 * Get CSS classes for column alignment.
 *
 * Follows SRP by handling only alignment class generation.
 * Follows DRY by centralizing alignment logic.
 *
 * Parameters
 * ----------
 * align : "left" | "center" | "right" | undefined
 *     Column alignment preference.
 *
 * Returns
 * -------
 * string
 *     CSS classes for the alignment.
 */
export function getColumnAlignClass(
  align?: "left" | "center" | "right",
): string {
  const defaultAlign = align ?? "center";
  switch (defaultAlign) {
    case "left":
      return "justify-start text-left";
    case "right":
      return "justify-end text-right";
    default:
      return "justify-center text-center";
  }
}

/**
 * Get inline styles for column width constraints.
 *
 * Locks column width so rows align regardless of content length.
 * Follows SRP by handling only style generation.
 * Follows DRY by centralizing column width logic.
 *
 * Parameters
 * ----------
 * minWidth : number | undefined
 *     Minimum width for the column.
 *
 * Returns
 * -------
 * React.CSSProperties
 *     Inline styles for the column container.
 */
export function getColumnWidthStyles(minWidth?: number): React.CSSProperties {
  if (!minWidth) {
    return {};
  }

  return {
    width: minWidth,
    minWidth: minWidth,
    maxWidth: minWidth,
    flexGrow: 0,
    flexShrink: 0,
    flexBasis: minWidth,
  };
}
