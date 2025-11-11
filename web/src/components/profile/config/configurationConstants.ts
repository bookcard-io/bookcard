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
  "Open Library",
  "Goodreads",
  "LibraryThing",
] as const;

export const DISPLAY_MODE_OPTIONS = [
  { value: "pagination", label: "Use Pagination" },
  { value: "infinite-scroll", label: "Use Infinite Scroll" },
] as const;
