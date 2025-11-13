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

import Link from "next/link";
import type { Shelf } from "@/types/shelf";

export interface ShelfCardProps {
  /** Shelf data to display. */
  shelf: Shelf;
}

/**
 * Shelf card component.
 *
 * Displays a shelf as a card with name, book count, and public status.
 */
export function ShelfCard({ shelf }: ShelfCardProps) {
  return (
    <Link
      href={`/shelves/${shelf.id}`}
      className="block rounded-lg border border-gray-200 bg-bg-primary p-4 shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{shelf.name}</h3>
          <p className="mt-1 text-gray-600 text-sm">
            {shelf.book_count} {shelf.book_count === 1 ? "book" : "books"}
          </p>
        </div>
        {shelf.is_public && (
          <span className="rounded-full bg-blue-100 px-2 py-1 text-blue-800 text-xs">
            Public
          </span>
        )}
      </div>
    </Link>
  );
}
