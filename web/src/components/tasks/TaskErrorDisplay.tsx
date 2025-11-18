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

export interface TaskErrorDisplayProps {
  /**Error message to display. */
  error: string;
}

/**
 * Task error display component.
 *
 * Displays error messages in a styled container.
 * Follows SRP by handling only error display UI.
 */
export function TaskErrorDisplay({ error }: TaskErrorDisplayProps) {
  return (
    <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-200">
      {error}
    </div>
  );
}
