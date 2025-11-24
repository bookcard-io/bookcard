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

/**
 * Type definitions for PDF.js library.
 *
 * These types are based on the PDF.js API when loaded from CDN.
 */

/**
 * PDF.js viewport for rendering pages.
 */
export interface PDFViewport {
  /** Viewport width. */
  width: number;
  /** Viewport height. */
  height: number;
}

/**
 * PDF.js page object.
 *
 * Represents a single page in a PDF document.
 */
export interface PDFPage {
  /** Get the viewport for this page at a given scale. */
  getViewport(params: { scale: number }): PDFViewport;
  /** Render the page to a canvas context. */
  render(params: {
    canvasContext: CanvasRenderingContext2D;
    viewport: PDFViewport;
  }): {
    promise: Promise<void>;
  };
}

/**
 * PDF.js document object.
 *
 * Represents a loaded PDF document.
 */
export interface PDFDocument {
  /** Total number of pages in the document. */
  numPages: number;
  /** Get a specific page by page number (1-indexed). */
  getPage(pageNumber: number): Promise<PDFPage>;
}

/**
 * PDF.js loading task.
 *
 * Returned by getDocument() before the document is loaded.
 */
export interface PDFLoadingTask {
  /** Promise that resolves to the PDF document. */
  promise: Promise<PDFDocument>;
}

/**
 * PDF.js global worker options.
 */
export interface PDFJSGlobalWorkerOptions {
  /** Path to the PDF.js worker script. */
  workerSrc: string;
}

/**
 * PDF.js library interface.
 *
 * Main entry point for PDF.js functionality.
 */
export interface PDFJSLib {
  /** Global worker options. */
  GlobalWorkerOptions: PDFJSGlobalWorkerOptions;
  /** Load a PDF document from a URL or data source. */
  getDocument(src: string | ArrayBuffer | Uint8Array): PDFLoadingTask;
}

/**
 * Global window extension for PDF.js.
 */
declare global {
  interface Window {
    /** PDF.js library instance (loaded from CDN). */
    pdfjsLib: PDFJSLib;
  }
}
