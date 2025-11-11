/**
 * Configuration constants for user preferences.
 *
 * Centralized location for available options.
 * Follows SOC by separating data from components.
 */

export const AVAILABLE_LANGUAGES = [
  "English",
  "Spanish",
  "French",
  "German",
  "Italian",
  "Portuguese",
  "Chinese",
  "Japanese",
  "Korean",
] as const;

export const AVAILABLE_METADATA_PROVIDERS = [
  "Google Books",
  "Amazon",
  "豆瓣",
  "Google Scholar",
  "LubimyCzytac.pl",
  "ComicVine",
] as const;

export const DISPLAY_MODE_OPTIONS = [
  { value: "pagination", label: "Use Pagination" },
  { value: "infinite-scroll", label: "Use Infinite Scroll" },
] as const;

export const SORT_FIELD_OPTIONS = [
  { value: "timestamp", label: "Added Date" },
  { value: "title", label: "Title" },
  { value: "author_sort", label: "Author" },
  { value: "pubdate", label: "Modified Date" },
  { value: "series_index", label: "Size" },
] as const;

export const SORT_ORDER_OPTIONS = [
  { value: "asc", label: "Ascending" },
  { value: "desc", label: "Descending" },
] as const;

export const PAGE_SIZE_OPTIONS = [
  { value: "10", label: "10" },
  { value: "20", label: "20" },
  { value: "30", label: "30" },
  { value: "50", label: "50" },
  { value: "100", label: "100" },
] as const;

export const VIEW_MODE_OPTIONS = [
  { value: "grid", label: "Grid" },
  { value: "list", label: "List" },
] as const;

export const BOOK_DETAILS_OPEN_MODE_OPTIONS = [
  { value: "modal", label: "Open in Modal" },
  { value: "page", label: "Navigate to Page" },
] as const;
