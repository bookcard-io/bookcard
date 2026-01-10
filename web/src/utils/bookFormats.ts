import { COMIC_FORMATS, READABLE_FORMATS } from "./formatUtils";

export interface BookFormat {
  format: string;
}

/**
 * Get the preferred readable format for opening in the reader.
 *
 * Native comic formats (CBZ/CBR/CB7/CBC) are always preferred when available.
 * Next preferred is EPUB, then PDF, then any other readable formats as defined in
 * `READABLE_FORMATS`.
 *
 * Parameters
 * ----------
 * formats : BookFormat[]
 *     List of available book formats (e.g., from `book.formats`).
 *
 * Returns
 * -------
 * string | null
 *     Preferred readable format (always returned in uppercase), or null if no
 *     readable format is available.
 */
export function getPreferredReadableFormat(
  formats: BookFormat[],
): string | null {
  const available = new Set(formats.map((f) => f.format.toUpperCase()));

  for (const priority of READABLE_FORMATS) {
    if (available.has(priority)) {
      return priority;
    }
  }

  return null;
}

/**
 * Resolve the best readable format for the reader, honoring an optional
 * preferred format while still preferring native comic formats when available.
 *
 * Parameters
 * ----------
 * formats : BookFormat[]
 *     Available book formats.
 * preferredFormat : string | undefined
 *     Optional preferred format to use when available.
 *
 * Returns
 * -------
 * string | null
 *     Resolved readable format (uppercase) or null if none is readable.
 */
export function getReadableFormatForReader(
  formats: BookFormat[],
  preferredFormat?: string,
): string | null {
  const available = new Set(formats.map((f) => f.format.toUpperCase()));

  const preferredUpper = preferredFormat?.toUpperCase();

  // If the preferred format is a native comic and it exists, honor it.
  if (
    preferredUpper &&
    available.has(preferredUpper) &&
    (COMIC_FORMATS as readonly string[]).includes(preferredUpper)
  ) {
    return preferredUpper;
  }

  // Native comics always win when present, regardless of a non-comic preference.
  if ((COMIC_FORMATS as readonly string[]).some((c) => available.has(c))) {
    return getPreferredReadableFormat(formats);
  }

  // Otherwise, honor the preferred format when it is readable and available.
  if (
    preferredUpper &&
    available.has(preferredUpper) &&
    (READABLE_FORMATS as readonly string[]).includes(preferredUpper)
  ) {
    return preferredUpper;
  }

  return getPreferredReadableFormat(formats);
}
