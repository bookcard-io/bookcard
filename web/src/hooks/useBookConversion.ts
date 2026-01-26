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

import { useCallback } from "react";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import {
  type BookConvertResponse,
  convertBookFormat,
} from "@/services/bookService";

export interface UseBookConversionOptions {
  /** Book ID to convert. */
  bookId: number;
  /** Callback fired once a conversion is queued. */
  onConversionStarted?: (
    taskId: number,
    sourceFormat: string,
    targetFormat: string,
  ) => void;
  /**
   * Best-effort history refetch callback.
   *
   * Should resolve when refetch completes and reject on error.
   */
  refetchHistory: () => Promise<unknown>;
}

export interface UseBookConversionResult {
  /** Queue a conversion (fire-and-forget). */
  queueConversion: (sourceFormat: string, targetFormat: string) => void;
}

/**
 * Queue a book format conversion and surface UX messaging.
 *
 * Parameters
 * ----------
 * options : UseBookConversionOptions
 *     Hook configuration including book ID and callbacks.
 *
 * Returns
 * -------
 * UseBookConversionResult
 *     A function for queueing conversions.
 */
export function useBookConversion(
  options: UseBookConversionOptions,
): UseBookConversionResult {
  const { bookId, onConversionStarted, refetchHistory } = options;
  const { showSuccess, showDanger } = useGlobalMessages();

  const queueConversion = useCallback(
    (sourceFormat: string, targetFormat: string) => {
      convertBookFormat(bookId, sourceFormat, targetFormat)
        .then((response: BookConvertResponse) => {
          if (response.message) {
            showSuccess(response.message);
            return;
          }

          showSuccess(
            `Conversion from ${sourceFormat} to ${targetFormat} has been queued. You can track progress in the tasks panel.`,
          );
          onConversionStarted?.(response.task_id, sourceFormat, targetFormat);
        })
        .then(() => {
          // Refresh history in background (best-effort).
          return refetchHistory().catch((error: unknown) => {
            console.debug("Failed to refresh conversion history:", error);
          });
        })
        .catch((error: unknown) => {
          const errorMessage =
            error instanceof Error
              ? error.message
              : "Failed to queue conversion";
          showDanger(errorMessage);
        });
    },
    [bookId, onConversionStarted, refetchHistory, showDanger, showSuccess],
  );

  return { queueConversion };
}
