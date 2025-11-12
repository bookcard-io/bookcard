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
import styles from "./BookEditModal.module.scss";

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
    <div className={styles.header}>
      <div className={styles.titleSection}>
        <h2 className={styles.title}>
          Editing {formTitle || book.title || "Untitled"}
        </h2>
        <p className={styles.helperText}>
          Multi-valued values like Authors, Tags, Languages: comma or enter to
          add.
        </p>
      </div>
      <Button
        type="button"
        variant="success"
        size="medium"
        onClick={onFetchMetadata}
        disabled={isUpdating}
      >
        Fetch metadata
      </Button>
    </div>
  );
}
