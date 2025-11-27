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

import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/forms/Button";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import {
  type BookConversionListResponse,
  convertBookFormat,
  getBookConversions,
} from "@/services/bookService";
import type { Book } from "@/types/book";

export interface ConversionModalProps {
  /** Book data. */
  book: Book;
  /** Whether modal is open. */
  isOpen: boolean;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when conversion is started. */
  onConversionStarted?: (taskId: number) => void;
}

/**
 * Conversion modal component.
 *
 * Displays format conversion interface with source/target format selection
 * and conversion history.
 */
export function ConversionModal({
  book,
  isOpen,
  onClose,
  onConversionStarted,
}: ConversionModalProps) {
  const { showSuccess, showDanger } = useGlobalMessages();
  const [sourceFormat, setSourceFormat] = useState<string>("");
  const [targetFormat, setTargetFormat] = useState<string>("");
  const [isConverting, setIsConverting] = useState(false);

  // Available formats from book
  const availableFormats = useMemo(() => {
    return book.formats?.map((f) => f.format.toUpperCase()) || [];
  }, [book.formats]);

  // Target format options (common formats)
  const targetFormatOptions = useMemo(() => {
    const commonFormats = ["EPUB", "MOBI", "AZW3", "KEPUB", "PDF"];
    // Filter out formats that already exist
    return commonFormats.filter((format) => !availableFormats.includes(format));
  }, [availableFormats]);

  // Load conversion history
  const { data: conversionHistory, refetch: refetchHistory } =
    useQuery<BookConversionListResponse>({
      queryKey: ["book-conversions", book.id],
      queryFn: () => getBookConversions(book.id),
      enabled: isOpen,
    });

  // Set default source format when modal opens
  useEffect(() => {
    if (isOpen && availableFormats.length > 0 && !sourceFormat) {
      const firstFormat = availableFormats[0];
      if (firstFormat) {
        setSourceFormat(firstFormat);
      }
    }
  }, [isOpen, availableFormats, sourceFormat]);

  // Set default target format
  useEffect(() => {
    if (isOpen && targetFormatOptions.length > 0 && !targetFormat) {
      const firstTarget = targetFormatOptions[0];
      if (firstTarget) {
        setTargetFormat(firstTarget);
      }
    }
  }, [isOpen, targetFormatOptions, targetFormat]);

  // Prevent body scroll when modal is open
  useModal(isOpen);

  const { handleOverlayClick, handleOverlayKeyDown } = useModalInteractions({
    onClose,
  });

  const handleConvert = useCallback(async () => {
    if (!sourceFormat || !targetFormat) {
      showDanger("Please select both source and target formats");
      return;
    }

    if (sourceFormat === targetFormat) {
      showDanger("Source and target formats must be different");
      return;
    }

    try {
      setIsConverting(true);
      const response = await convertBookFormat(
        book.id,
        sourceFormat,
        targetFormat,
      );

      if (response.message) {
        // Conversion already exists
        showSuccess(response.message);
        onClose();
      } else {
        // Conversion started
        showSuccess(
          "Conversion started. You can track progress in the tasks panel.",
        );
        onConversionStarted?.(response.task_id);
        await refetchHistory();
        onClose();
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to start conversion";
      showDanger(errorMessage);
    } finally {
      setIsConverting(false);
    }
  }, [
    sourceFormat,
    targetFormat,
    book.id,
    showSuccess,
    showDanger,
    onClose,
    onConversionStarted,
    refetchHistory,
  ]);

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="conversion-modal-title"
    >
      <div className="modal-container modal-container-shadow-large max-h-[90vh] w-full max-w-[600px] overflow-y-auto rounded-md bg-[var(--color-surface-a0)] p-6">
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
              disabled={isConverting}
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
              disabled={isConverting}
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

        {/* Conversion History */}
        {conversionHistory && conversionHistory.items.length > 0 && (
          <div className="mb-6">
            <h3 className="mb-2 font-semibold text-[var(--color-text-a0)] text-sm">
              Conversion History
            </h3>
            <div className="max-h-[200px] overflow-y-auto rounded-md border border-[var(--color-surface-a20)]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-[var(--color-surface-a10)]">
                  <tr>
                    <th className="px-3 py-2 text-left text-[var(--color-text-a20)]">
                      From
                    </th>
                    <th className="px-3 py-2 text-left text-[var(--color-text-a20)]">
                      To
                    </th>
                    <th className="px-3 py-2 text-left text-[var(--color-text-a20)]">
                      Status
                    </th>
                    <th className="px-3 py-2 text-left text-[var(--color-text-a20)]">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {conversionHistory.items.map((conv) => (
                    <tr
                      key={conv.id}
                      className="border-[var(--color-surface-a20)] border-t"
                    >
                      <td className="px-3 py-2 text-[var(--color-text-a0)]">
                        {conv.original_format}
                      </td>
                      <td className="px-3 py-2 text-[var(--color-text-a0)]">
                        {conv.target_format}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`inline-block rounded px-2 py-0.5 text-xs ${
                            conv.status === "completed"
                              ? "bg-green-500/20 text-green-500"
                              : "bg-red-500/20 text-red-500"
                          }`}
                        >
                          {conv.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-[var(--color-text-a20)] text-xs">
                        {new Date(conv.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={isConverting}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleConvert}
            disabled={isConverting || !sourceFormat || !targetFormat}
          >
            {isConverting ? "Converting..." : "Convert"}
          </Button>
        </div>
      </div>
    </div>
  );
}
