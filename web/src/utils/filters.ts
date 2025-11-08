import type { FilterValues } from "@/components/library/widgets/FiltersPanel";

/**
 * Create empty filter values.
 *
 * Returns
 * -------
 * FilterValues
 *     Empty filter values with all arrays initialized to empty.
 */
export function createEmptyFilters(): FilterValues {
  return {
    authorIds: [],
    titleIds: [],
    genreIds: [],
    publisherIds: [],
    identifierIds: [],
    seriesIds: [],
    formats: [],
    ratingIds: [],
    languageIds: [],
  };
}

/**
 * Get all filter array values from FilterValues.
 *
 * Extracts all filter arrays (authorIds, titleIds, etc.) into a single array
 * for iteration. This centralizes the filter property access logic.
 *
 * Parameters
 * ----------
 * filters : FilterValues | undefined
 *     Filter values to extract.
 *
 * Returns
 * -------
 * Array<Array<number | string>>
 *     Array of all filter arrays.
 */
function getFilterArrays(
  filters: FilterValues | undefined,
): Array<number[] | string[]> {
  if (!filters) {
    return [];
  }

  return [
    filters.authorIds,
    filters.titleIds,
    filters.genreIds,
    filters.publisherIds,
    filters.identifierIds,
    filters.seriesIds,
    filters.formats,
    filters.ratingIds,
    filters.languageIds,
  ];
}

/**
 * Check if any filter values are active.
 *
 * Parameters
 * ----------
 * filters : FilterValues | undefined
 *     Filter values to check.
 *
 * Returns
 * -------
 * bool
 *     True if any filter is active, false otherwise.
 */
export function hasActiveFilters(filters: FilterValues | undefined): boolean {
  const filterArrays = getFilterArrays(filters);
  return filterArrays.some((arr) => arr.length > 0);
}

/**
 * Count the number of active filter types.
 *
 * Each filter type (author, title, genre, etc.) counts as 1,
 * regardless of how many values are selected within that type.
 *
 * Parameters
 * ----------
 * filters : FilterValues | undefined
 *     Filter values to count.
 *
 * Returns
 * -------
 * number
 *     Number of active filter types (0-9).
 */
export function countActiveFilterTypes(
  filters: FilterValues | undefined,
): number {
  const filterArrays = getFilterArrays(filters);
  return filterArrays.filter((arr) => arr.length > 0).length;
}

/**
 * Convert FilterValues to API request body format.
 *
 * Parameters
 * ----------
 * filters : FilterValues
 *     Filter values to convert.
 *
 * Returns
 * -------
 * object
 *     API request body with snake_case keys and null for empty arrays.
 */
export function filtersToApiBody(filters: FilterValues) {
  return {
    author_ids:
      filters.authorIds && filters.authorIds.length > 0
        ? filters.authorIds
        : null,
    title_ids:
      filters.titleIds && filters.titleIds.length > 0 ? filters.titleIds : null,
    genre_ids:
      filters.genreIds && filters.genreIds.length > 0 ? filters.genreIds : null,
    publisher_ids:
      filters.publisherIds && filters.publisherIds.length > 0
        ? filters.publisherIds
        : null,
    identifier_ids:
      filters.identifierIds && filters.identifierIds.length > 0
        ? filters.identifierIds
        : null,
    series_ids:
      filters.seriesIds && filters.seriesIds.length > 0
        ? filters.seriesIds
        : null,
    formats:
      filters.formats && filters.formats.length > 0 ? filters.formats : null,
    rating_ids:
      filters.ratingIds && filters.ratingIds.length > 0
        ? filters.ratingIds
        : null,
    language_ids:
      filters.languageIds && filters.languageIds.length > 0
        ? filters.languageIds
        : null,
  };
}
