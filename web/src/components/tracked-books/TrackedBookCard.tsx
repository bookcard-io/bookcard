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

import Link from "next/link";
import { ROUTES } from "@/constants/routes";
import type { TrackedBook } from "@/types/trackedBook";
import { formatStatus, getStatusStyles } from "@/utils/bookStatus";

interface TrackedBookCardProps {
  book: TrackedBook;
}

export function TrackedBookCard({ book }: TrackedBookCardProps) {
  return (
    <Link
      href={`${ROUTES.TRACKED_BOOKS}/${book.id}`}
      className="flex gap-4 overflow-hidden rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
    >
      {book.cover_url ? (
        <img
          src={book.cover_url}
          alt={book.title}
          className="h-24 w-16 rounded object-cover shadow-sm"
        />
      ) : (
        <div className="flex h-24 w-16 items-center justify-center rounded bg-gray-100 dark:bg-gray-700">
          <span className="text-gray-400 text-xs">No Cover</span>
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col justify-between">
        <div>
          <h3 className="truncate font-medium text-gray-900 dark:text-gray-100">
            {book.title}
          </h3>
          <p className="truncate text-gray-500 text-sm dark:text-gray-400">
            {book.author}
          </p>
        </div>
        <div className="mt-2">
          <span
            className={`inline-flex items-center rounded-full px-2 py-1 font-medium text-xs ${getStatusStyles(
              book.status,
            )}`}
          >
            {formatStatus(book.status)}
          </span>
        </div>
      </div>
    </Link>
  );
}
