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

"use client";

import { Button } from "@/components/forms/Button";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { METADATA_FIELDS, type MetadataFieldKey } from "./metadataFields";

export interface MetadataFieldSelectionDrawerProps {
  record: MetadataRecord;
  selectedFields: Set<MetadataFieldKey>;
  onToggleField: (key: MetadataFieldKey) => void;
  onImport: () => void;
  onCancel: () => void;
  isAnimatingOut: boolean;
}

/**
 * Field selection drawer component for metadata import.
 *
 * Displays checkboxes for each available field with values.
 * Follows SRP by focusing solely on field selection UI.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : MetadataFieldSelectionDrawerProps
 *     Component props including record, selection state, and callbacks.
 */
export function MetadataFieldSelectionDrawer({
  record,
  selectedFields,
  onToggleField,
  onImport,
  onCancel,
  isAnimatingOut,
}: MetadataFieldSelectionDrawerProps) {
  return (
    <div
      className={`overflow-hidden border-surface-a20 border-t pt-3 ${
        isAnimatingOut
          ? "animate-[slideUp_0.5s_ease-out]"
          : "animate-[slideDown_0.5s_ease-out]"
      }`}
    >
      <p className="mb-3 text-sm text-text-a40">
        Select the fields you want to import:
      </p>

      <div className="mb-4 flex gap-3">
        {/* Cover field - spans rows on the left */}
        {record.cover_url && (
          <div
            className={`flex shrink-0 flex-col items-center gap-2 self-start transition-opacity ${
              selectedFields.has("cover") ? "opacity-100" : "opacity-50"
            }`}
          >
            <input
              type="checkbox"
              className="mt-1"
              checked={selectedFields.has("cover")}
              onChange={() => onToggleField("cover")}
            />
            <div className="shrink-0">
              {METADATA_FIELDS.find((f) => f.key === "cover")?.getValue(record)}
            </div>
          </div>
        )}

        {/* Other fields in two-column layout */}
        <div className="grid flex-1 grid-cols-2 gap-2">
          {METADATA_FIELDS.filter(
            (field) =>
              field.key !== "cover" &&
              field.key !== "description" &&
              field.hasValue(record),
          ).map((field) => (
            <label
              key={field.key}
              className={`flex cursor-pointer items-start gap-2 rounded border border-transparent p-2 transition-all hover:bg-surface-a20 ${
                selectedFields.has(field.key) ? "opacity-100" : "opacity-50"
              }`}
            >
              <input
                type="checkbox"
                className="mt-1 shrink-0"
                checked={selectedFields.has(field.key)}
                onChange={() => onToggleField(field.key)}
              />
              <div className="flex min-w-0 flex-1 flex-col gap-1">
                <span className="font-bold text-sm text-text-a20">
                  {field.label}
                </span>
                <div className="break-words text-sm text-text-a0">
                  {field.getValue(record)}
                </div>
              </div>
            </label>
          ))}

          {/* Description - spans 2 columns */}
          {record.description && (
            <label
              className={`col-span-2 flex cursor-pointer items-start gap-2 rounded border border-transparent p-2 transition-all hover:bg-surface-a20 ${
                selectedFields.has("description") ? "opacity-100" : "opacity-50"
              }`}
            >
              <input
                type="checkbox"
                className="mt-1 shrink-0"
                checked={selectedFields.has("description")}
                onChange={() => onToggleField("description")}
              />
              <div className="flex min-w-0 flex-1 flex-col gap-1">
                <span className="font-bold text-sm text-text-a20">
                  Description
                </span>
                <div className="break-words text-sm text-text-a0">
                  {METADATA_FIELDS.find(
                    (f) => f.key === "description",
                  )?.getValue(record)}
                </div>
              </div>
            </label>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-3">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="button" variant="primary" onClick={onImport}>
          Import
        </Button>
      </div>
    </div>
  );
}
