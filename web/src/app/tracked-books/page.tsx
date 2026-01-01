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
import { useEffect, useState } from "react";
import { FaPlus, FaSearch } from "react-icons/fa";
import { PageLayout } from "@/components/layout/PageLayout";
import { trackedBookService } from "@/services/trackedBookService";
import type { TrackedBook } from "@/types/trackedBook";

export default function TrackedBooksPage() {
  const [trackedBooks, setTrackedBooks] = useState<TrackedBook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    trackedBookService
      .getAll()
      .then(setTrackedBooks)
      .catch((error) => {
        console.error("Failed to fetch tracked books:", error);
        // Keep empty list on error
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <PageLayout>
      <div className="flex h-full flex-col p-4 md:p-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="font-bold text-2xl text-gray-900 dark:text-gray-100">
              Tracked Books
            </h1>
            <p className="text-gray-500 text-sm dark:text-gray-400">
              Manage your book watch list
            </p>
          </div>
          <Link
            href="/tracked-books/add"
            className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 font-medium text-sm text-white transition-colors hover:bg-blue-700"
          >
            <FaPlus />
            <span className="hidden sm:inline">Add New</span>
          </Link>
        </div>

        {loading ? (
          <div className="flex flex-1 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          </div>
        ) : trackedBooks.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center text-center">
            <div className="mb-4 rounded-full bg-gray-100 p-4 dark:bg-gray-800">
              <FaSearch className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="mb-2 font-medium text-gray-900 text-lg dark:text-gray-100">
              No books tracked yet
            </h3>
            <p className="mb-6 max-w-sm text-gray-500 dark:text-gray-400">
              Search for books to add them to your watch list. We'll
              automatically download them when they become available.
            </p>
            <Link
              href="/tracked-books/add"
              className="rounded-md bg-blue-600 px-4 py-2 font-medium text-sm text-white hover:bg-blue-700"
            >
              Add Your First Book
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {trackedBooks.map((book) => (
              <div
                key={book.id}
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
                      className={`inline-flex items-center rounded-full px-2 py-1 font-medium text-xs ${
                        book.status === "completed"
                          ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                          : book.status === "downloading"
                            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                            : book.status === "failed"
                              ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                              : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400"
                      }`}
                    >
                      {book.status.charAt(0).toUpperCase() +
                        book.status.slice(1)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
