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

import { BooksViewSplash } from "./BooksViewSplash";

/**
 * Error state component for books view.
 *
 * Displays error message when book loading fails.
 * Shows splash screen for no active library error.
 * Follows SRP by handling only error display.
 */
export function BooksViewError({ error }: { error: string }) {
  // Show splash screen for no active library error
  if (error === "no_active_library") {
    return <BooksViewSplash />;
  }

  // Show friendly message for other errors
  const friendlyMessage = `Error loading books: ${error}`;

  return (
    <div className="flex min-h-[400px] items-center justify-center p-8">
      <p className="m-0 text-base text-danger-a10">{friendlyMessage}</p>
    </div>
  );
}
