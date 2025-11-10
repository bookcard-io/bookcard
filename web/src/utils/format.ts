/**
 * Formatting utility functions.
 *
 * Provides reusable formatting functions for dates, file sizes, and other data.
 * Follows SRP by separating formatting logic from presentation.
 * Follows DRY by centralizing formatting logic.
 */

/**
 * Format file size in bytes to human-readable string.
 *
 * Parameters
 * ----------
 * bytes : number
 *     File size in bytes.
 *
 * Returns
 * -------
 * string
 *     Human-readable file size (e.g., "1.5 MB").
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / k ** i).toFixed(2)} ${sizes[i]}`;
}

/**
 * Format date string to human-readable format.
 *
 * Parameters
 * ----------
 * dateString : string | null
 *     ISO date string or null.
 *
 * Returns
 * -------
 * string
 *     Human-readable date (e.g., "January 15, 2024") or "—" if null.
 */
export function formatDate(dateString: string | null): string {
  if (!dateString) return "—";
  try {
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) {
      return dateString;
    }
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  } catch {
    return dateString;
  }
}

/**
 * Extract year from date string.
 *
 * Parameters
 * ----------
 * dateString : string | null
 *     ISO date string or null.
 *
 * Returns
 * -------
 * string
 *     Year as string (e.g., "2024") or "—" if null.
 */
export function formatYear(dateString: string | null): string {
  if (!dateString) return "—";
  try {
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) {
      return "—";
    }
    return date.getFullYear().toString();
  } catch {
    return "—";
  }
}
