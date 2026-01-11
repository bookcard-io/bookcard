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
 * Normalize a Content-Type header value to its mime type.
 *
 * Parameters
 * ----------
 * contentType : string
 *     Content-Type header value.
 */
export function normalizeMimeType(contentType: string): string {
  const [mimeRaw] = contentType.split(";");
  return (mimeRaw ?? "").trim().toLowerCase();
}

const MIME_TO_EXTENSION = new Map<string, string>([
  ["image/jpeg", "jpg"],
  ["image/jpg", "jpg"],
  ["image/png", "png"],
  ["image/gif", "gif"],
  ["image/webp", "webp"],
  ["image/bmp", "bmp"],
  ["image/tiff", "tiff"],
  ["image/svg+xml", "svg"],
  ["image/avif", "avif"],
  ["image/heic", "heic"],
]);

const VALID_IMAGE_EXTENSIONS = new Set([
  "jpg",
  "jpeg",
  "png",
  "gif",
  "webp",
  "bmp",
  "tiff",
  "svg",
  "avif",
  "heic",
]);

/**
 * Map an image mime type to a common file extension.
 *
 * Parameters
 * ----------
 * mimeType : string
 *     Mime type (e.g. "image/jpeg").
 */
export function extensionFromMimeType(mimeType: string): string | null {
  return MIME_TO_EXTENSION.get(mimeType) ?? null;
}

/**
 * Whether a mime type is an image mime type.
 *
 * Parameters
 * ----------
 * mimeType : string
 *     Mime type.
 */
export function isImageMimeType(mimeType: string): boolean {
  return mimeType.startsWith("image/");
}

/**
 * Validate that an extension is a known image extension.
 *
 * Parameters
 * ----------
 * extension : string
 *     File extension without dot.
 */
export function isValidImageExtension(extension: string): boolean {
  return VALID_IMAGE_EXTENSIONS.has(extension.toLowerCase());
}
