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

import { type BookFormat, FormatItem } from "./FormatItem";

/**
 * Props for FormatList component.
 */
export interface FormatListProps {
  /** List of formats to display. */
  formats: BookFormat[];
  /** Render function for format actions. */
  renderActions?: (format: BookFormat) => React.ReactNode;
}

/**
 * Format list component for displaying book formats.
 *
 * Renders a list of format items with optional action buttons.
 * Follows OCP by accepting render function for extensible actions.
 * Follows SRP by focusing solely on list rendering.
 *
 * Parameters
 * ----------
 * props : FormatListProps
 *     Component props including formats and action renderer.
 */
export function FormatList({ formats, renderActions }: FormatListProps) {
  if (formats.length === 0) {
    return (
      <div className="py-2 text-sm text-text-a30">No formats available</div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {formats.map((format) => (
        <FormatItem
          key={`${format.format}-${format.size}`}
          format={format}
          actions={renderActions?.(format)}
        />
      ))}
    </div>
  );
}
