/**
 * Metadata utility functions.
 *
 * Provides reusable functions for converting and transforming metadata records.
 * Follows SRP by separating metadata transformation logic from presentation.
 * Follows DRY by centralizing metadata conversion logic.
 */

import type {
  MetadataRecord,
  ProviderStatus,
} from "@/hooks/useMetadataSearchStream";
import type { BookUpdate } from "@/types/book";

/**
 * Convert identifiers from Record format to array format.
 *
 * Parameters
 * ----------
 * identifiers : Record<string, string> | undefined
 *     Dictionary of identifier type -> value.
 *
 * Returns
 * -------
 * Array<{ type: string; val: string }>
 *     Array of identifier objects with type and val properties.
 */
function convertIdentifiers(
  identifiers: Record<string, string> | undefined,
): Array<{ type: string; val: string }> {
  const result: Array<{ type: string; val: string }> = [];
  if (identifiers) {
    for (const [type, val] of Object.entries(identifiers)) {
      if (type && val) {
        result.push({ type, val });
      }
    }
  }
  return result;
}

/**
 * Convert published_date to pubdate format (YYYY-MM-DD).
 *
 * Parameters
 * ----------
 * publishedDate : string | null | undefined
 *     Published date string in various formats.
 *
 * Returns
 * -------
 * string | null
 *     Date in YYYY-MM-DD format or null if invalid/missing.
 */
function convertPublishedDate(
  publishedDate: string | null | undefined,
): string | null {
  if (!publishedDate) {
    return null;
  }
  // Try to extract date part from various formats
  const dateMatch = publishedDate.match(/^(\d{4}-\d{2}-\d{2})/);
  if (dateMatch?.[1]) {
    // Validate the date
    const date = new Date(dateMatch[1]);
    if (!Number.isNaN(date.getTime())) {
      return dateMatch[1];
    }
  }
  return null;
}

/**
 * Convert rating to 0-5 scale.
 *
 * Parameters
 * ----------
 * rating : number | null | undefined
 *     Rating value (may be in various scales).
 *
 * Returns
 * -------
 * number | null
 *     Rating normalized to 0-5 scale or null if invalid/missing.
 */
function convertRating(rating: number | null | undefined): number | null {
  if (rating === null || rating === undefined) {
    return null;
  }
  // Ensure rating is in 0-5 range
  return Math.max(0, Math.min(5, Math.round(rating)));
}

/**
 * Convert a metadata record to BookUpdate format.
 *
 * Transforms external metadata record into the format expected by the book update API.
 * Handles type conversions, format normalization, and data validation.
 *
 * Parameters
 * ----------
 * record : MetadataRecord
 *     Metadata record from external source.
 *
 * Returns
 * -------
 * BookUpdate
 *     Book update payload ready for API submission.
 */
export function convertMetadataRecordToBookUpdate(
  record: MetadataRecord,
): BookUpdate {
  const identifiers = convertIdentifiers(record.identifiers);
  const pubdate = convertPublishedDate(record.published_date);
  const ratingValue = convertRating(record.rating);

  const update: BookUpdate = {};

  if (record.title) {
    update.title = record.title;
  }

  if (record.authors && record.authors.length > 0) {
    update.author_names = record.authors;
  }

  if (record.series) {
    update.series_name = record.series;
  }

  if (record.series_index !== null && record.series_index !== undefined) {
    update.series_index = record.series_index;
  } else if (record.series_index === null) {
    update.series_index = null;
  }

  if (record.description) {
    update.description = record.description;
  }

  if (record.publisher) {
    update.publisher_name = record.publisher;
  }

  if (pubdate !== null && pubdate !== undefined) {
    update.pubdate = pubdate;
  } else if (record.published_date !== undefined) {
    // Explicitly set to null if published_date was provided but invalid
    update.pubdate = null;
  }

  if (identifiers.length > 0) {
    update.identifiers = identifiers;
  }

  if (record.languages && record.languages.length > 0) {
    update.language_codes = record.languages;
  }

  if (record.tags && record.tags.length > 0) {
    update.tag_names = record.tags;
  }

  if (ratingValue !== null) {
    update.rating_value = ratingValue;
  }

  return update;
}

/**
 * Apply BookUpdate fields to a form using a field change handler.
 *
 * Parameters
 * ----------
 * update : BookUpdate
 *     Book update object with fields to apply.
 * handleFieldChange : <K extends keyof BookUpdate>(field: K, value: BookUpdate[K]) => void
 *     Function to handle individual field changes.
 */
export function applyBookUpdateToForm(
  update: BookUpdate,
  handleFieldChange: <K extends keyof BookUpdate>(
    field: K,
    value: BookUpdate[K],
  ) => void,
): void {
  // Apply each field explicitly for type safety
  if (update.title !== undefined && update.title !== null) {
    handleFieldChange("title", update.title);
  }
  if (update.author_names !== undefined && update.author_names !== null) {
    handleFieldChange("author_names", update.author_names);
  }
  if (update.series_name !== undefined && update.series_name !== null) {
    handleFieldChange("series_name", update.series_name);
  }
  if (update.series_index !== undefined && update.series_index !== null) {
    handleFieldChange("series_index", update.series_index);
  }
  if (update.description !== undefined && update.description !== null) {
    handleFieldChange("description", update.description);
  }
  if (update.publisher_name !== undefined && update.publisher_name !== null) {
    handleFieldChange("publisher_name", update.publisher_name);
  }
  if (update.pubdate !== undefined && update.pubdate !== null) {
    handleFieldChange("pubdate", update.pubdate);
  }
  if (update.identifiers !== undefined && update.identifiers !== null) {
    handleFieldChange("identifiers", update.identifiers);
  }
  if (update.language_codes !== undefined && update.language_codes !== null) {
    handleFieldChange("language_codes", update.language_codes);
  }
  if (update.tag_names !== undefined && update.tag_names !== null) {
    handleFieldChange("tag_names", update.tag_names);
  }
  if (update.rating_value !== undefined && update.rating_value !== null) {
    handleFieldChange("rating_value", update.rating_value);
  }
}

/**
 * Sort provider statuses by priority.
 *
 * Sorts providers by status priority: searching > pending > completed > failed.
 * Follows SRP by focusing solely on sorting logic.
 *
 * Parameters
 * ----------
 * providerStatuses : Map<string, ProviderStatus>
 *     Map of provider statuses to sort.
 *
 * Returns
 * -------
 * Array<ProviderStatus>
 *     Sorted array of provider statuses.
 */
export function sortProviderStatuses(
  providerStatuses: Map<string, ProviderStatus>,
): Array<ProviderStatus> {
  return Array.from(providerStatuses.values()).sort((a, b) => {
    // Sort by status priority: searching > pending > completed > failed
    const statusOrder: Record<string, number> = {
      searching: 0,
      pending: 1,
      completed: 2,
      failed: 3,
    };
    return (statusOrder[a.status] ?? 99) - (statusOrder[b.status] ?? 99);
  });
}

/**
 * Check if any provider has failed.
 *
 * Parameters
 * ----------
 * providerStatuses : Map<string, ProviderStatus>
 *     Map of provider statuses to check.
 *
 * Returns
 * -------
 * boolean
 *     True if any provider has failed, false otherwise.
 */
export function hasFailedProviders(
  providerStatuses: Map<string, ProviderStatus>,
): boolean {
  return Array.from(providerStatuses.values()).some(
    (status) => status.status === "failed",
  );
}

/**
 * Normalize provider name to source ID format.
 *
 * Converts provider display name to the format used in source_id fields.
 * Example: "Google Books" -> "google-books"
 *
 * Parameters
 * ----------
 * providerName : string
 *     Provider display name to normalize.
 *
 * Returns
 * -------
 * string
 *     Normalized provider name in source ID format.
 */
export function normalizeProviderName(providerName: string): string {
  return providerName.toLowerCase().replace(/\s+/g, "-");
}
