/**
 * TypeScript types for book-related data structures.
 *
 * These types match the backend API schemas defined in fundamental/api/schemas.py
 */

export interface Book {
  /** Calibre book ID. */
  id: number;
  /** Book title. */
  title: string;
  /** List of author names. */
  authors: string[];
  /** Sortable author name. */
  author_sort: string | null;
  /** Publication date. */
  pubdate: string | null;
  /** Date book was added to library. */
  timestamp: string | null;
  /** Series name if part of a series. */
  series: string | null;
  /** Series ID if part of a series. */
  series_id: number | null;
  /** Position in series. */
  series_index: number | null;
  /** ISBN identifier. */
  isbn: string | null;
  /** Unique identifier for the book. */
  uuid: string;
  /** URL to book cover thumbnail. */
  thumbnail_url: string | null;
  /** Whether the book has a cover image. */
  has_cover: boolean;
  /** List of tag names. */
  tags?: string[];
  /** List of identifiers, each with 'type' and 'val' keys. */
  identifiers?: Array<{ type: string; val: string }>;
  /** Book description/comment text. */
  description?: string | null;
  /** Publisher name. */
  publisher?: string | null;
  /** Publisher ID. */
  publisher_id?: number | null;
  /** Language code. */
  language?: string | null;
  /** Language ID. */
  language_id?: number | null;
  /** Rating value (0-5). */
  rating?: number | null;
  /** Rating ID. */
  rating_id?: number | null;
}

export interface BookUpdate {
  /** Book title to update. */
  title?: string | null;
  /** Publication date to update. */
  pubdate?: string | null;
  /** List of author names to set (replaces existing). */
  author_names?: string[] | null;
  /** Series name to set (creates if doesn't exist). */
  series_name?: string | null;
  /** Series ID to set (if provided, series_name is ignored). */
  series_id?: number | null;
  /** Series index to update. */
  series_index?: number | null;
  /** List of tag names to set (replaces existing). */
  tag_names?: string[] | null;
  /** List of identifiers with 'type' and 'val' keys (replaces existing). */
  identifiers?: Array<{ type: string; val: string }> | null;
  /** Book description/comment to set. */
  description?: string | null;
  /** Publisher name to set (creates if doesn't exist). */
  publisher_name?: string | null;
  /** Publisher ID to set (if provided, publisher_name is ignored). */
  publisher_id?: number | null;
  /** Language code to set (creates if doesn't exist). */
  language_code?: string | null;
  /** Language ID to set (if provided, language_code is ignored). */
  language_id?: number | null;
  /** Rating value to set (0-5). */
  rating_value?: number | null;
  /** Rating ID to set (if provided, rating_value is ignored). */
  rating_id?: number | null;
}

export interface BookListResponse {
  /** List of books for current page. */
  items: Book[];
  /** Total number of books matching the query. */
  total: number;
  /** Current page number (1-indexed). */
  page: number;
  /** Number of items per page. */
  page_size: number;
  /** Total number of pages. */
  total_pages: number;
}

export interface BooksQueryParams {
  /** Page number (1-indexed). */
  page?: number;
  /** Number of items per page. */
  page_size?: number;
  /** Search query to filter by title or author. */
  search?: string;
  /** Field to sort by. */
  sort_by?: "timestamp" | "pubdate" | "title" | "author_sort" | "series_index";
  /** Sort order. */
  sort_order?: "asc" | "desc";
}
