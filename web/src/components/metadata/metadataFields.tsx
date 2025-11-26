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

import type React from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";

/**
 * Field key type for metadata import selection.
 */
export type MetadataFieldKey =
  | "cover"
  | "title"
  | "authors"
  | "series"
  | "publisher"
  | "published_date"
  | "description"
  | "identifiers"
  | "tags"
  | "rating"
  | "languages";

/**
 * Field definition for metadata import.
 *
 * Defines how to display and validate a metadata field.
 */
export interface MetadataFieldDefinition {
  key: MetadataFieldKey;
  label: string;
  getValue: (record: MetadataRecord) => string | React.ReactNode | null;
  hasValue: (record: MetadataRecord) => boolean;
}

/**
 * Metadata field definitions for import selection.
 *
 * Follows DRY by centralizing field definitions.
 * Follows SRP by focusing solely on field metadata.
 */
export const METADATA_FIELDS: MetadataFieldDefinition[] = [
  {
    key: "cover",
    label: "Cover",
    getValue: (record) =>
      record.cover_url ? (
        <ImageWithLoading
          src={record.cover_url}
          alt={`Cover for ${record.title}`}
          width={60}
          height={90}
          className="rounded border object-cover"
          unoptimized
        />
      ) : null,
    hasValue: (record) => !!record.cover_url,
  },
  {
    key: "title",
    label: "Title",
    getValue: (record) => record.title,
    hasValue: (record) => !!record.title,
  },
  {
    key: "authors",
    label: "Author",
    getValue: (record) => record.authors.join(", "),
    hasValue: (record) => record.authors && record.authors.length > 0,
  },
  {
    key: "series",
    label: "Series",
    getValue: (record) =>
      record.series
        ? `${record.series}${record.series_index ? ` #${record.series_index}` : ""}`
        : null,
    hasValue: (record) => !!record.series,
  },
  {
    key: "publisher",
    label: "Publisher",
    getValue: (record) => record.publisher,
    hasValue: (record) => !!record.publisher,
  },
  {
    key: "published_date",
    label: "Date",
    getValue: (record) => record.published_date,
    hasValue: (record) => !!record.published_date,
  },
  {
    key: "rating",
    label: "Rating",
    getValue: (record) => (record.rating ? `${record.rating}/5` : null),
    hasValue: (record) => record.rating !== null && record.rating !== undefined,
  },
  {
    key: "identifiers",
    label: "Identifiers",
    getValue: (record) =>
      record.identifiers
        ? Object.entries(record.identifiers)
            .map(([k, v]) => `${k}:${v}`)
            .join(", ")
        : null,
    hasValue: (record) =>
      !!record.identifiers && Object.keys(record.identifiers).length > 0,
  },
  {
    key: "tags",
    label: "Tags",
    getValue: (record) => record.tags?.join(", "),
    hasValue: (record) => !!record.tags && record.tags.length > 0,
  },
  {
    key: "languages",
    label: "Languages",
    getValue: (record) => record.languages?.join(", "),
    hasValue: (record) => !!record.languages && record.languages.length > 0,
  },
  {
    key: "description",
    label: "Description",
    getValue: (record) => (
      <span className="line-clamp-3 block text-sm">
        {record.description || ""}
      </span>
    ),
    hasValue: (record) => !!record.description,
  },
];

/**
 * Get all available field keys for a record.
 *
 * Parameters
 * ----------
 * record : MetadataRecord
 *     Metadata record to check.
 *
 * Returns
 * -------
 * Set<MetadataFieldKey>
 *     Set of field keys that have values in the record.
 */
export function getAvailableFieldKeys(
  record: MetadataRecord,
): Set<MetadataFieldKey> {
  const availableFields = new Set<MetadataFieldKey>();
  for (const field of METADATA_FIELDS) {
    if (field.hasValue(record)) {
      availableFields.add(field.key);
    }
  }
  return availableFields;
}
