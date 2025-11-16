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
import type { Book } from "@/types/book";

export interface BookEditModalHeaderProps {
  /** Current book being edited. */
  book: Book;
  /** Current form title value. */
  formTitle?: string | null;
  /** Whether update is in progress. */
  isUpdating: boolean;
  /** Callback to open metadata fetch modal. */
  onFetchMetadata: () => void;
}

/**
 * Header component for book edit modal.
 *
 * Displays the title and fetch metadata button.
 * Follows SRP by focusing solely on header presentation.
 */
export function BookEditModalHeader({
  book,
  formTitle,
  isUpdating,
  onFetchMetadata,
}: BookEditModalHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-4 border-surface-a20 border-b pt-6 pr-16 pb-4 pl-6">
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
          Editing {formTitle || book.title || "Untitled"}
        </h2>
        <p className="m-0 text-sm text-text-a30 leading-6">
          Multi-valued values like Authors, Tags, Languages: comma or enter to
          add.
        </p>
      </div>
      <div className="flex items-center gap-3">
        <Button
          type="button"
          variant="success"
          size="medium"
          onClick={onFetchMetadata}
          disabled={isUpdating}
        >
          Fetch metadata
        </Button>
        <Button
          type="button"
          variant="success"
          size="medium"
          onClick={() => {}}
          disabled={isUpdating}
        >
          I'm feelin' lucky!
        </Button>
      </div>
    </div>
  );
}
