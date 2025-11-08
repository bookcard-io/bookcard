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
