import { isComicFormat } from "./formatUtils";

export interface BookFormat {
  format: string;
}

/**
 * Get the preferred readable format for a book.
 *
 * Priorities: EPUB > PDF > Comic formats.
 *
 * @param formats List of available book formats
 * @returns Preferred format string or null if no readable format found
 */
export function getPreferredReadableFormat(
  formats: BookFormat[],
): string | null {
  const priorityOrder = ["EPUB", "PDF"];

  for (const priority of priorityOrder) {
    const found = formats.find((f) => f.format.toUpperCase() === priority);
    if (found) return found.format;
  }

  const comic = formats.find((f) => isComicFormat(f.format));
  return comic?.format ?? null;
}
