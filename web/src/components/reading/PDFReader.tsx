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

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/libs/utils";
import type { PDFDocument } from "@/types/pdfjs";

export interface PDFReaderProps {
  /** PDF file URL. */
  url: string;
  /** Initial page number (optional). */
  initialPage?: number | null;
  /** Callback when page changes. */
  onPageChange?: (page: number, totalPages: number, progress: number) => void;
  /** Callback to register jump handler. Receives a function that takes progress (0.0 to 1.0). */
  onJumpToProgress?: (handler: (progress: number) => void) => void;
  /** Zoom level (default: 1.0). */
  zoom?: number;
  /** Theme: 'light' or 'dark'. */
  theme?: "light" | "dark";
  /** Optional className. */
  className?: string;
}

/**
 * PDF reader component using PDF.js.
 *
 * Renders PDF pages and tracks page number.
 * Updates progress on page changes.
 * Follows SRP by focusing solely on PDF rendering.
 *
 * Parameters
 * ----------
 * props : PDFReaderProps
 *     Component props including PDF URL and callbacks.
 */
export function PDFReader({
  url,
  initialPage,
  onPageChange,
  onJumpToProgress,
  zoom = 1.0,
  theme = "light",
  className,
}: PDFReaderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInitialLoadRef = useRef(true);
  const hasNavigatedToInitialPageRef = useRef(false);
  const [currentPage, setCurrentPage] = useState(initialPage || 1);
  const [totalPages, setTotalPages] = useState(0);
  const [pdfDoc, setPdfDoc] = useState<PDFDocument | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load PDF.js from CDN if not already loaded
    if (!window.pdfjsLib) {
      const script = document.createElement("script");
      script.src =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
      script.onload = () => {
        window.pdfjsLib.GlobalWorkerOptions.workerSrc =
          "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
        loadPDF();
      };
      document.body.appendChild(script);
    } else {
      loadPDF();
    }

    function loadPDF() {
      setIsLoading(true);
      setError(null);

      window.pdfjsLib
        .getDocument(url)
        .promise.then((pdf: PDFDocument) => {
          setPdfDoc(pdf);
          setTotalPages(pdf.numPages);
          setIsLoading(false);
          // Mark as initial load when PDF is loaded
          isInitialLoadRef.current = true;
          if (initialPage) {
            setCurrentPage(initialPage);
            hasNavigatedToInitialPageRef.current = true;
          }
          // After initial page is rendered, allow future page changes to update progress
          setTimeout(() => {
            isInitialLoadRef.current = false;
          }, 500);
        })
        .catch((err: Error) => {
          setError(err.message);
          setIsLoading(false);
        });
    }
  }, [url, initialPage]);

  const renderPage = useCallback(
    async (pageNum: number) => {
      if (!pdfDoc || !containerRef.current) {
        return;
      }

      try {
        const page = await pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: zoom });
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        if (!context) {
          throw new Error("Failed to get canvas context");
        }
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        await page.render({
          canvasContext: context,
          viewport,
        }).promise;

        // Clear container and add canvas
        containerRef.current.innerHTML = "";
        containerRef.current.appendChild(canvas);

        // Update progress (skip during initial load)
        if (!isInitialLoadRef.current && onPageChange) {
          const progress = pageNum / totalPages;
          onPageChange(pageNum, totalPages, progress);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to render page");
      }
    },
    [pdfDoc, zoom, totalPages, onPageChange],
  );

  useEffect(() => {
    if (pdfDoc && currentPage) {
      renderPage(currentPage);
    }
  }, [pdfDoc, currentPage, renderPage]);

  // Navigate to persisted page when initialPage becomes available
  // This handles the case where progress is loaded asynchronously after component mount
  useEffect(() => {
    if (
      initialPage &&
      pdfDoc &&
      totalPages > 0 &&
      !hasNavigatedToInitialPageRef.current
    ) {
      const validPage = Math.max(1, Math.min(initialPage, totalPages));
      setCurrentPage(validPage);
      hasNavigatedToInitialPageRef.current = true;

      // Calculate progress from page number and report it
      // This ensures the progress bar reflects the persisted location
      if (onPageChange) {
        const calculatedProgress = validPage / totalPages;
        // Mark as initial load to prevent duplicate progress update
        isInitialLoadRef.current = true;
        // Report the calculated progress
        onPageChange(validPage, totalPages, calculatedProgress);
        setTimeout(() => {
          isInitialLoadRef.current = false;
        }, 500);
      } else {
        // If no callback, just mark as initial load
        isInitialLoadRef.current = true;
        setTimeout(() => {
          isInitialLoadRef.current = false;
        }, 500);
      }
    }
  }, [initialPage, pdfDoc, totalPages, onPageChange]);

  // Register jump handler for progress navigation
  useEffect(() => {
    if (onJumpToProgress && pdfDoc && totalPages > 0) {
      const handleJump = (targetProgress: number) => {
        // Calculate page number from progress (0.0 to 1.0)
        const targetPage = Math.max(
          1,
          Math.min(Math.ceil(targetProgress * totalPages), totalPages),
        );
        setCurrentPage(targetPage);
      };
      onJumpToProgress(handleJump);
    }
  }, [onJumpToProgress, pdfDoc, totalPages]);

  const handlePreviousPage = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  }, [currentPage]);

  const handleNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  }, [currentPage, totalPages]);

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <span className="text-text-a40">Loading PDF...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <span className="text-danger-a10">Error: {error}</span>
      </div>
    );
  }

  return (
    <div className={cn("flex h-full flex-col", className)}>
      <div className="flex items-center justify-between border-surface-a20 border-b bg-surface-tonal-a0 p-2">
        <button
          type="button"
          onClick={handlePreviousPage}
          disabled={currentPage <= 1}
          className="rounded px-3 py-1 text-sm transition-colors hover:bg-surface-a20 disabled:opacity-50"
        >
          <i className="pi pi-chevron-left" /> Previous
        </button>
        <span className="text-sm text-text-a0">
          Page {currentPage} of {totalPages}
        </span>
        <button
          type="button"
          onClick={handleNextPage}
          disabled={currentPage >= totalPages}
          className="rounded px-3 py-1 text-sm transition-colors hover:bg-surface-a20 disabled:opacity-50"
        >
          Next <i className="pi pi-chevron-right" />
        </button>
      </div>
      <div
        ref={containerRef}
        className={cn(
          "flex-1 overflow-auto",
          theme === "dark" ? "bg-gray-900" : "bg-white",
        )}
      />
    </div>
  );
}
