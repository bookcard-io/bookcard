import { useMemo } from "react";

/**
 * Hook to determine the EPUB download URL.
 *
 * @param url - Direct URL to the EPUB file.
 * @param bookId - ID of the book to construct the download URL.
 * @returns The URL to download/stream the EPUB.
 */
export function useEpubUrl(url?: string, bookId?: number): string | null {
  return useMemo(() => {
    if (url) {
      return url;
    }
    if (bookId) {
      return `/api/books/${bookId}/download/EPUB`;
    }
    return null;
  }, [url, bookId]);
}
