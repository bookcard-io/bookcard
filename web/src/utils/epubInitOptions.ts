// Copyright (C) 2025 khoa and others
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

import type { BookOptions } from "epubjs/types/book";

/**
 * EPUB initialization options utilities.
 *
 * Centralized configuration for EPUB.js initialization.
 * Follows SRP by separating configuration from UI components.
 */

/**
 * Create EPUB.js initialization options.
 *
 * Configures EPUB.js to load books as binary data and prevents
 * external HTTP requests to ensure all resources come from the archive.
 *
 * Returns
 * -------
 * Partial<BookOptions>
 *     Configuration object for EPUB.js initialization.
 */
export function createEpubInitOptions(): Partial<BookOptions> {
  return {
    openAs: "binary",
    // Prevent epubjs from making external HTTP requests
    requestMethod: (
      url: string,
      _type: string,
      _withCredentials: object,
      _headers: object,
    ) => {
      if (
        typeof url === "string" &&
        (url.startsWith("http://") || url.startsWith("https://"))
      ) {
        return Promise.reject(
          new Error("Resource should be loaded from EPUB archive"),
        );
      }
      // Allow internal paths (starting with /) and other schemes
      return fetch(url).then((response) => {
        if (!response.ok) {
          throw new Error(
            `Failed to load resource: ${response.status} ${response.statusText}`,
          );
        }
        return response.blob();
      }) as Promise<Blob>;
    },
  };
}
