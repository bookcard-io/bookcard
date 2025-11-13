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

import type { Book } from "./book";

/**
 * Column identifier for list view.
 *
 * Each column represents a field that can be displayed in the list view.
 */
export type ListColumnId =
  | "title"
  | "authors"
  | "series"
  | "series_index"
  | "pubdate"
  | "timestamp"
  | "publisher"
  | "isbn"
  | "tags"
  | "languages"
  | "rating"
  | "formats"
  | "description";

/**
 * Column definition for list view.
 *
 * Defines metadata and rendering information for a column.
 */
export interface ListColumnDefinition {
  /** Unique identifier for the column. */
  id: ListColumnId;
  /** Display label for the column header. */
  label: string;
  /** Whether this column is shown by default. */
  defaultVisible: boolean;
  /** Minimum width in pixels. */
  minWidth?: number;
  /** Text alignment for the column content. */
  align?: "left" | "center" | "right";
  /** Function to extract and format the value from a book. */
  getValue: (book: Book) => string | null;
}

/**
 * Default visible columns for list view.
 */
export const DEFAULT_VISIBLE_COLUMNS: ListColumnId[] = [
  "title",
  "authors",
  "series",
  "pubdate",
  "rating",
];

/**
 * All available column definitions.
 */
export const LIST_COLUMN_DEFINITIONS: Record<
  ListColumnId,
  ListColumnDefinition
> = {
  title: {
    id: "title",
    label: "Title",
    defaultVisible: true,
    minWidth: 200,
    getValue: (book) => book.title,
  },
  authors: {
    id: "authors",
    label: "Authors",
    defaultVisible: true,
    minWidth: 180,
    getValue: (book) =>
      book.authors.length > 0 ? book.authors.join(", ") : "Unknown Author",
  },
  series: {
    id: "series",
    label: "Series",
    defaultVisible: true,
    minWidth: 150,
    align: "left",
    getValue: (book) => book.series ?? null,
  },
  series_index: {
    id: "series_index",
    label: "#",
    defaultVisible: false,
    minWidth: 60,
    getValue: (book) =>
      book.series_index !== null && book.series_index !== undefined
        ? book.series_index.toString()
        : null,
  },
  pubdate: {
    id: "pubdate",
    label: "Published",
    defaultVisible: true,
    minWidth: 150,
    align: "left",
    getValue: (book) => book.pubdate,
  },
  timestamp: {
    id: "timestamp",
    label: "Added",
    defaultVisible: false,
    minWidth: 150,
    getValue: (book) => book.timestamp,
  },
  publisher: {
    id: "publisher",
    label: "Publisher",
    defaultVisible: false,
    minWidth: 150,
    getValue: (book) => book.publisher ?? null,
    align: "left",
  },
  isbn: {
    id: "isbn",
    label: "ISBN",
    defaultVisible: false,
    minWidth: 140,
    getValue: (book) => book.isbn ?? null,
  },
  tags: {
    id: "tags",
    label: "Tags",
    defaultVisible: false,
    minWidth: 200,
    align: "left",
    getValue: (book) =>
      book.tags && book.tags.length > 0 ? book.tags.join(", ") : null,
  },
  languages: {
    id: "languages",
    label: "Languages",
    defaultVisible: false,
    minWidth: 120,
    getValue: (book) =>
      book.languages && book.languages.length > 0
        ? book.languages.map((lang) => lang.toUpperCase()).join(", ")
        : null,
  },
  rating: {
    id: "rating",
    label: "Rating",
    defaultVisible: true,
    minWidth: 100,
    getValue: (book) =>
      book.rating !== null && book.rating !== undefined
        ? `${book.rating}/5`
        : null,
  },
  formats: {
    id: "formats",
    label: "Formats",
    defaultVisible: false,
    minWidth: 120,
    getValue: (book) =>
      book.formats && book.formats.length > 0
        ? book.formats.map((f) => f.format.toUpperCase()).join(", ")
        : null,
  },
  description: {
    id: "description",
    label: "Description",
    defaultVisible: false,
    minWidth: 300,
    getValue: (book) => book.description ?? null,
  },
};
