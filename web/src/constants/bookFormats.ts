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
 * Supported book file formats.
 *
 * Single source of truth for all supported book formats in the frontend.
 * Matches DEFAULT_SUPPORTED_FORMATS from backend (fundamental/repositories/ingest_repository.py).
 *
 * Follows DRY principle by centralizing format definitions.
 * Follows SOC by separating format data from components.
 */

/**
 * List of supported book file format extensions (without dots).
 *
 * Matches Calibre-supported formats: 31 formats total.
 * Order matches backend DEFAULT_SUPPORTED_FORMATS for consistency.
 */
export const SUPPORTED_BOOK_FORMAT_EXTENSIONS = [
  "acsm",
  "azw",
  "azw3",
  "azw4",
  "cbz",
  "cbr",
  "cb7",
  "cbc",
  "chm",
  "djvu",
  "docx",
  "epub",
  "fb2",
  "fbz",
  "html",
  "htmlz",
  "kepub",
  "lit",
  "lrf",
  "mobi",
  "odt",
  "pdf",
  "prc",
  "pdb",
  "pml",
  "rb",
  "rtf",
  "snb",
  "tcr",
  "txt",
  "txtz",
] as const;

/**
 * Generate accept attribute string for file input elements.
 *
 * Returns a comma-separated string of file extensions with dots,
 * suitable for use in HTML file input accept attribute.
 *
 * Returns
 * -------
 * string
 *     Accept attribute string (e.g., ".epub,.mobi,.pdf").
 */
export function getBookFormatsAcceptString(): string {
  return SUPPORTED_BOOK_FORMAT_EXTENSIONS.map((ext) => `.${ext}`).join(",");
}

/**
 * Format label mapping for display purposes.
 *
 * Maps format extensions to user-friendly labels.
 * Formats not in this map will use uppercase extension as label.
 */
const FORMAT_LABELS: Record<string, string> = {
  acsm: "ACSM",
  azw: "AZW",
  azw3: "AZW3",
  azw4: "AZW4",
  cbz: "CBZ",
  cbr: "CBR",
  cb7: "CB7",
  cbc: "CBC",
  chm: "CHM",
  djvu: "DJVU",
  docx: "DOCX",
  epub: "EPUB",
  fb2: "FB2",
  fbz: "FBZ",
  html: "HTML",
  htmlz: "HTMLZ",
  kepub: "KEPUB",
  lit: "LIT",
  lrf: "LRF",
  mobi: "MOBI",
  odt: "ODT",
  pdf: "PDF",
  prc: "PRC",
  pdb: "PDB",
  pml: "PML",
  rb: "RB",
  rtf: "RTF",
  snb: "SNB",
  tcr: "TCR",
  txt: "TXT",
  txtz: "TXTZ",
};

/**
 * Get user-friendly label for a format extension.
 *
 * Parameters
 * ----------
 * format : string
 *     Format extension (e.g., "epub", "mobi").
 *
 * Returns
 * -------
 * string
 *     User-friendly label (e.g., "EPUB", "MOBI").
 */
export function getFormatLabel(format: string): string {
  return FORMAT_LABELS[format.toLowerCase()] || format.toUpperCase();
}

/**
 * Supported book formats for UI components.
 *
 * Array of format objects with value and label for use in select dropdowns,
 * checkboxes, and other UI components.
 */
export const SUPPORTED_BOOK_FORMATS = SUPPORTED_BOOK_FORMAT_EXTENSIONS.map(
  (format) => ({
    value: format,
    label: getFormatLabel(format),
  }),
) as Array<{ value: string; label: string }>;
