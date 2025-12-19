import { READABLE_FORMATS } from "./formatUtils";

export interface BookFormat {
  format: string;
}

/**
 * Get the preferred readable format for a book.
 *
 * Priorities: EPUB > PDF > Comic formats (defined in READABLE_FORMATS).
 *
 * @param formats List of available book formats
 * @returns Preferred format string or null if no readable format found
 */
export function getPreferredReadableFormat(
  formats: BookFormat[],
): string | null {
  for (const priority of READABLE_FORMATS) {
    const found = formats.find((f) => f.format.toUpperCase() === priority);
    if (found) return found.format;
  }

  return null;
}
