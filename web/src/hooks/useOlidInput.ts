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

import { useCallback, useRef, useState } from "react";
import type { AuthorWithMetadata } from "@/types/author";
import { normalizeAuthorKey, validateOlid } from "@/utils/openLibrary";

export interface UseOlidInputOptions {
  /** Author data to determine initial OLID value. */
  author: AuthorWithMetadata;
}

export interface UseOlidInputResult {
  /** Whether the OLID input form is visible. */
  showOlidInput: boolean;
  /** Current OLID input value. */
  olidInput: string;
  /** Validation error message, if any. */
  olidError: string | null;
  /** Input ref for focusing. */
  olidInputRef: React.RefObject<HTMLInputElement>;
  /** Show the OLID input form. */
  showInput: () => void;
  /** Hide the OLID input form. */
  hideInput: () => void;
  /** Handle input value change. */
  handleInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** Handle input blur with validation. */
  handleInputBlur: () => void;
  /** Validate and get the current OLID value. */
  getValidatedOlid: () => string | null;
}

/**
 * Custom hook for managing OLID input form state.
 *
 * Handles OLID input visibility, validation, and state management.
 * Follows SRP by managing only OLID input concerns.
 * Follows IOC by accepting author data and returning state/actions.
 *
 * Parameters
 * ----------
 * options : UseOlidInputOptions
 *     Hook options including author data.
 *
 * Returns
 * -------
 * UseOlidInputResult
 *     OLID input state and control functions.
 */
export function useOlidInput(options: UseOlidInputOptions): UseOlidInputResult {
  const { author } = options;
  const [showOlidInput, setShowOlidInput] = useState(false);
  const [olidInput, setOlidInput] = useState("");
  const [olidError, setOlidError] = useState<string | null>(null);
  const olidInputRef = useRef<HTMLInputElement>(null);

  const showInput = useCallback(() => {
    setShowOlidInput(true);
    setOlidError(null); // Clear any previous errors
    const normalizedKey = normalizeAuthorKey(author.key);
    // For already-matched authors, prefill with existing OLID.
    // For unmatched authors, leave blank so user must provide an OLID.
    const initialOlid =
      author.is_unmatched || author.key?.startsWith("calibre-")
        ? ""
        : normalizedKey;
    setOlidInput(initialOlid);
    // Focus the input after it's rendered
    setTimeout(() => {
      olidInputRef.current?.focus();
    }, 0);
  }, [author.is_unmatched, author.key]);

  const hideInput = useCallback(() => {
    setShowOlidInput(false);
    setOlidInput("");
    setOlidError(null);
  }, []);

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setOlidInput(value);

      // Clear error when user starts typing
      if (olidError) {
        setOlidError(null);
      }
    },
    [olidError],
  );

  const handleInputBlur = useCallback(() => {
    // Validate on blur if there's input
    if (olidInput.trim()) {
      const validation = validateOlid(olidInput.trim());
      if (!validation.isValid) {
        setOlidError(validation.error || "Invalid OLID format");
      }
    }
  }, [olidInput]);

  const getValidatedOlid = useCallback((): string | null => {
    const trimmedOlid = olidInput.trim();
    if (!trimmedOlid) {
      return null;
    }

    const validation = validateOlid(trimmedOlid);
    if (!validation.isValid) {
      setOlidError(validation.error || "Invalid OLID format");
      return null;
    }

    return trimmedOlid;
  }, [olidInput]);

  return {
    showOlidInput,
    olidInput,
    olidError,
    olidInputRef,
    showInput,
    hideInput,
    handleInputChange,
    handleInputBlur,
    getValidatedOlid,
  };
}
