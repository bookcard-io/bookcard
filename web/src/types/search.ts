// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
