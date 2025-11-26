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

import type { MetadataFieldKey } from "@/components/metadata/metadataFields";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";

/**
 * Create a filtered metadata record with only selected fields.
 *
 * Follows SRP by focusing solely on record filtering logic.
 * Follows DRY by centralizing field filtering logic.
 *
 * Parameters
 * ----------
 * record : MetadataRecord
 *     Original metadata record.
 * selectedFields : Set<MetadataFieldKey>
 *     Set of field keys to include in the filtered record.
 *
 * Returns
 * -------
 * MetadataRecord
 *     Filtered metadata record with only selected fields populated.
 */
export function createFilteredMetadataRecord(
  record: MetadataRecord,
  selectedFields: Set<MetadataFieldKey>,
): MetadataRecord {
  return {
    ...record,
    title: selectedFields.has("title") ? record.title : "",
    authors: selectedFields.has("authors") ? record.authors : [],
    series: selectedFields.has("series") ? record.series : null,
    series_index: selectedFields.has("series") ? record.series_index : null,
    publisher: selectedFields.has("publisher") ? record.publisher : null,
    published_date: selectedFields.has("published_date")
      ? record.published_date
      : null,
    description: selectedFields.has("description") ? record.description : null,
    identifiers: selectedFields.has("identifiers")
      ? record.identifiers
      : undefined,
    tags: selectedFields.has("tags") ? record.tags : undefined,
    rating: selectedFields.has("rating") ? record.rating : null,
    languages: selectedFields.has("languages") ? record.languages : undefined,
    cover_url: selectedFields.has("cover") ? record.cover_url : null,
  };
}
