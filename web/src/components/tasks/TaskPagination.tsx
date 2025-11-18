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

import { Button } from "@/components/forms/Button";

export interface TaskPaginationProps {
  /**Current page number (1-indexed). */
  page: number;
  /**Number of items per page. */
  pageSize: number;
  /**Total number of items. */
  total: number;
  /**Total number of pages. */
  totalPages: number;
  /**Callback to go to previous page. */
  onPreviousPage: () => void;
  /**Callback to go to next page. */
  onNextPage: () => void;
}

/**
 * Task pagination component.
 *
 * Displays pagination controls and page information.
 * Follows SRP by handling only pagination UI.
 * Follows IOC by accepting callbacks as props.
 */
export function TaskPagination({
  page,
  pageSize,
  total,
  totalPages,
  onPreviousPage,
  onNextPage,
}: TaskPaginationProps) {
  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="mt-4 flex items-center justify-between">
      <div className="text-gray-600 text-sm dark:text-gray-400">
        Showing {(page - 1) * pageSize + 1} to{" "}
        {Math.min(page * pageSize, total)} of {total} tasks
      </div>
      <div className="flex gap-2">
        <Button
          variant="secondary"
          size="small"
          onClick={onPreviousPage}
          disabled={page === 1}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          size="small"
          onClick={onNextPage}
          disabled={page >= totalPages}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
