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

import { useEffect, useMemo, useRef, useState } from "react";
import type { Book } from "@/types/book";
import {
  getAvailableFormats,
  getTargetFormatOptions,
} from "@/utils/conversion";

export interface UseFormatSelectionResult {
  /** Uppercased formats available on the book. */
  availableFormats: string[];
  /** Uppercased target formats the user can convert into. */
  targetFormatOptions: string[];
  /** Selected source format. */
  sourceFormat: string;
  /** Selected target format. */
  targetFormat: string;
  /** Set selected source format. */
  setSourceFormat: (format: string) => void;
  /** Set selected target format. */
  setTargetFormat: (format: string) => void;
}

/**
 * Manage conversion format selection for a book.
 *
 * Handles available/target format computation, default selections when the modal
 * opens, and resets when switching to a different book.
 *
 * Parameters
 * ----------
 * book : Book
 *     Book used to derive available formats.
 * isOpen : boolean
 *     Whether the modal is currently open.
 *
 * Returns
 * -------
 * UseFormatSelectionResult
 *     Computed format options and selection state.
 */
export function useFormatSelection(
  book: Book,
  isOpen: boolean,
): UseFormatSelectionResult {
  const [sourceFormat, setSourceFormat] = useState<string>("");
  const [targetFormat, setTargetFormat] = useState<string>("");

  const previousBookIdRef = useRef<number | null>(null);
  const previousIsOpenRef = useRef<boolean>(false);

  const availableFormats = useMemo(() => getAvailableFormats(book), [book]);
  const targetFormatOptions = useMemo(
    () => getTargetFormatOptions(availableFormats),
    [availableFormats],
  );

  // Reset format selection when opening for a different book.
  useEffect(() => {
    const previousBookId = previousBookIdRef.current;
    const previousIsOpen = previousIsOpenRef.current;
    const isOpening = isOpen && !previousIsOpen;
    const bookChangedWhileOpen =
      isOpen && previousBookId !== null && previousBookId !== book.id;

    if (isOpening || bookChangedWhileOpen) {
      setSourceFormat("");
      setTargetFormat("");
    }

    previousBookIdRef.current = book.id;
    previousIsOpenRef.current = isOpen;
  }, [book.id, isOpen]);

  // Set default source format when modal opens or formats reset.
  useEffect(() => {
    if (!isOpen || sourceFormat) {
      return;
    }
    setSourceFormat(availableFormats[0] ?? "");
  }, [isOpen, availableFormats, sourceFormat]);

  // Set default target format when modal opens or formats reset.
  useEffect(() => {
    if (!isOpen || targetFormat) {
      return;
    }
    setTargetFormat(targetFormatOptions[0] ?? "");
  }, [isOpen, targetFormatOptions, targetFormat]);

  return {
    availableFormats,
    targetFormatOptions,
    sourceFormat,
    targetFormat,
    setSourceFormat,
    setTargetFormat,
  };
}
