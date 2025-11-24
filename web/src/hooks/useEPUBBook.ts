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

import { useEffect, useRef, useState } from "react";

/**
 * Hook for fetching EPUB book as ArrayBuffer.
 *
 * Handles book fetching logic separately from rendering.
 * Follows SRP by separating data fetching from UI.
 * Follows IOC by providing a reusable hook interface.
 *
 * Parameters
 * ----------
 * downloadUrl : string | null
 *     URL to download the book from.
 *
 * Returns
 * -------
 * object
 *     Book data and loading/error states.
 */
export function useEPUBBook(downloadUrl: string | null) {
  const [bookArrayBuffer, setBookArrayBuffer] = useState<ArrayBuffer | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);
  const bookArrayBufferRef = useRef<ArrayBuffer | null>(null);

  useEffect(() => {
    if (!downloadUrl) {
      setIsError(true);
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    const fetchBook = async () => {
      setIsLoading(true);
      setIsError(false);

      try {
        const response = await fetch(downloadUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch book: ${response.statusText}`);
        }

        const blob = await response.blob();
        const arrayBuffer = await blob.arrayBuffer();

        if (!cancelled) {
          bookArrayBufferRef.current = arrayBuffer;
          setBookArrayBuffer(arrayBuffer);
          setIsLoading(false);
        }
      } catch (error) {
        console.error("Error fetching EPUB:", error);
        if (!cancelled) {
          setIsError(true);
          setIsLoading(false);
        }
      }
    };

    void fetchBook();

    return () => {
      cancelled = true;
    };
  }, [downloadUrl]);

  return {
    bookArrayBuffer,
    isLoading,
    isError,
    bookArrayBufferRef,
  };
}
