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

import { useEffect, useState } from "react";
import {
  getAvailableFieldKeys,
  type MetadataFieldKey,
} from "@/components/metadata/metadataFields";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";

export interface UseMetadataFieldSelectionOptions {
  /** Metadata record to select fields from. */
  record: MetadataRecord;
  /** Whether the selection UI is currently expanded. */
  isExpanded: boolean;
}

export interface UseMetadataFieldSelectionResult {
  /** Set of selected field keys. */
  selectedFields: Set<MetadataFieldKey>;
  /** Toggle a field's selection state. */
  toggleField: (key: MetadataFieldKey) => void;
  /** Select all available fields. */
  selectAll: () => void;
  /** Deselect all fields. */
  deselectAll: () => void;
}

/**
 * Hook for managing metadata field selection state.
 *
 * Handles field selection, initialization, and state management.
 * Follows SRP by focusing solely on field selection logic.
 * Follows IOC by accepting record and expanded state via options.
 *
 * Parameters
 * ----------
 * options : UseMetadataFieldSelectionOptions
 *     Configuration including record and expanded state.
 *
 * Returns
 * -------
 * UseMetadataFieldSelectionResult
 *     Selection state and manipulation functions.
 */
export function useMetadataFieldSelection({
  record,
  isExpanded,
}: UseMetadataFieldSelectionOptions): UseMetadataFieldSelectionResult {
  const [selectedFields, setSelectedFields] = useState<Set<MetadataFieldKey>>(
    new Set(),
  );

  // Initialize selected fields when expanded
  useEffect(() => {
    if (isExpanded) {
      const availableFields = getAvailableFieldKeys(record);
      setSelectedFields(availableFields);
    }
  }, [isExpanded, record]);

  const toggleField = (key: MetadataFieldKey) => {
    setSelectedFields((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const selectAll = () => {
    const availableFields = getAvailableFieldKeys(record);
    setSelectedFields(availableFields);
  };

  const deselectAll = () => {
    setSelectedFields(new Set());
  };

  return {
    selectedFields,
    toggleField,
    selectAll,
    deselectAll,
  };
}
