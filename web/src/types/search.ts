/**
 * TypeScript types for search-related data structures.
 *
 * These types match the backend API schemas for search suggestions.
 */

export interface SearchSuggestionItem {
  /** Identifier for the item (book ID, author ID, tag ID, etc.). */
  id: number;
  /** Display name for the suggestion. */
  name: string;
}

export interface SearchSuggestionsResponse {
  /** List of book title matches. */
  books: SearchSuggestionItem[];
  /** List of author name matches. */
  authors: SearchSuggestionItem[];
  /** List of tag matches. */
  tags: SearchSuggestionItem[];
  /** List of series matches. */
  series: SearchSuggestionItem[];
}

export type SearchSuggestionType = "BOOK" | "AUTHOR" | "TAG" | "SERIES";

export interface SearchSuggestion {
  /** Type of suggestion (book, author, tag, series). */
  type: SearchSuggestionType;
  /** Identifier for the item. */
  id: number;
  /** Display name for the suggestion. */
  name: string;
}
