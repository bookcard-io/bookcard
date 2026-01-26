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

import { useCallback } from "react";
import { ConversionHistoryTable } from "@/components/books/conversion/ConversionHistoryTable";
import { Button } from "@/components/forms/Button";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useBookConversion } from "@/hooks/useBookConversion";
import { useConversionHistory } from "@/hooks/useConversionHistory";
import { useFormatSelection } from "@/hooks/useFormatSelection";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import type { Book } from "@/types/book";
import type { ConversionStartedCallback } from "@/types/conversion";
import { getConversionValidationError } from "@/utils/conversion";
import { renderModalPortal } from "@/utils/modal";

interface ConversionModalDisplayProps {
  /** Book data. */
  book: Book;
  /** Whether modal is open. */
  isOpen: boolean;
  /** Callback when modal should be closed. */
  onClose: () => void;
}

interface ConversionModalActionsProps {
  /** Callback when conversion is started. */
  onConversionStarted?: ConversionStartedCallback;
}

export interface ConversionModalProps
  extends ConversionModalDisplayProps,
    ConversionModalActionsProps {}

/**
 * Conversion modal component.
 *
 * Displays format conversion interface with source/target format selection
 * and conversion history.
 *
 * Parameters
 * ----------
 * props : ConversionModalProps
 *     Modal input props including book data and close handlers.
 */
export function ConversionModal({
  book,
  isOpen,
  onClose,
  onConversionStarted,
}: ConversionModalProps) {
  const { showDanger } = useGlobalMessages();

  const {
    availableFormats,
    targetFormatOptions,
    sourceFormat,
    targetFormat,
    setSourceFormat,
    setTargetFormat,
  } = useFormatSelection(book, isOpen);

  const { data: conversionHistory, refetch: refetchHistory } =
    useConversionHistory(book.id, isOpen);

  const { queueConversion } = useBookConversion({
    bookId: book.id,
    onConversionStarted,
    refetchHistory: () => refetchHistory(),
  });

  // Prevent body scroll when modal is open
  useModal(isOpen);

  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({
      onClose,
    });

  const handleConvert = useCallback(() => {
    const error = getConversionValidationError(sourceFormat, targetFormat);
    if (error) {
      showDanger(error);
      return;
    }

    // Fire-and-forget: queue conversion and close modal immediately.
    queueConversion(sourceFormat, targetFormat);

    // Close modal immediately (fire-and-forget)
    onClose();
  }, [sourceFormat, targetFormat, showDanger, onClose, queueConversion]);

  if (!isOpen) {
    return null;
  }
  if (typeof document === "undefined") {
    return null;
  }

  const modalContent = (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className="modal-container modal-container-shadow-large max-h-[90vh] w-full max-w-[600px] overflow-y-auto rounded-md bg-[var(--color-surface-a0)] p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="conversion-modal-title"
        onMouseDown={handleModalClick}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2
            id="conversion-modal-title"
            className="m-0 font-bold text-[var(--color-text-a0)] text-xl"
          >
            Convert Book Format
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full transition hover:bg-[var(--color-surface-a20)] focus:outline-2 focus:outline-[var(--color-primary-a0)] focus:outline-offset-2"
            aria-label="Close modal"
          >
            <i className="pi pi-times text-[var(--color-text-a30)]" />
          </button>
        </div>

        <div className="mb-4">
          <p className="text-[var(--color-text-a20)] text-sm">{book.title}</p>
        </div>

        <div className="mb-6 flex flex-col gap-4">
          <div>
            <label
              htmlFor="source-format"
              className="mb-2 block font-medium text-[var(--color-text-a0)] text-sm"
            >
              Source Format
            </label>
            <select
              id="source-format"
              value={sourceFormat}
              onChange={(e) => setSourceFormat(e.target.value)}
              className="w-full rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a0)] px-3 py-2 text-[var(--color-text-a0)] text-sm focus:border-[var(--color-primary-a0)] focus:outline-none"
            >
              <option value="">Select source format</option>
              {availableFormats.map((format) => (
                <option key={format} value={format}>
                  {format}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="target-format"
              className="mb-2 block font-medium text-[var(--color-text-a0)] text-sm"
            >
              Target Format
            </label>
            <select
              id="target-format"
              value={targetFormat}
              onChange={(e) => setTargetFormat(e.target.value)}
              className="w-full rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a0)] px-3 py-2 text-[var(--color-text-a0)] text-sm focus:border-[var(--color-primary-a0)] focus:outline-none"
            >
              <option value="">Select target format</option>
              {targetFormatOptions.map((format) => (
                <option key={format} value={format}>
                  {format}
                </option>
              ))}
            </select>
          </div>
        </div>

        <ConversionHistoryTable history={conversionHistory} />

        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleConvert}
            disabled={!sourceFormat || !targetFormat}
          >
            Convert
          </Button>
        </div>
      </div>
    </div>
  );

  return renderModalPortal(modalContent);
}
