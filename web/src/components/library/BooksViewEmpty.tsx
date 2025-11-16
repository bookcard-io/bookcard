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
 * Empty state component for books view.
 *
 * Displays message when no books are found.
 * Follows SRP by handling only empty state display.
 */
export function BooksViewEmpty() {
  return (
    <div className="flex min-h-[400px] items-center justify-center p-8">
      <p className="m-0 text-base text-text-a40">No books found</p>
    </div>
  );
}
