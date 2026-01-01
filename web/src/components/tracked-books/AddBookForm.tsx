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

import { Select } from "@/components/forms/Select";
import { TagInput } from "@/components/forms/TagInput";
import { TextInput } from "@/components/forms/TextInput";
import {
  type FormatMode,
  formatModeService,
} from "@/services/FormatModeService";
import type { MonitorMode } from "@/types/trackedBook";

export interface AddBookFormProps {
  libraryId: number | undefined;
  monitor: MonitorMode;
  monitorValue: string;
  tags: string[];
  currentFormatMode: FormatMode;
  libraries: Array<{ id: number; name: string }>;
  onLibraryChange: (id: number) => void;
  onMonitorChange: (mode: MonitorMode) => void;
  onMonitorValueChange: (value: string) => void;
  onFormatModeChange: (mode: string) => void;
  onTagsChange: (tags: string[]) => void;
}

export function AddBookForm({
  libraryId,
  monitor,
  monitorValue,
  tags,
  currentFormatMode,
  libraries,
  onLibraryChange,
  onMonitorChange,
  onMonitorValueChange,
  onFormatModeChange,
  onTagsChange,
}: AddBookFormProps) {
  const isValidMonitorMode = (value: string): value is MonitorMode => {
    // Ideally this check could be imported from a shared validator
    // For now we trust the caller or check roughly
    return ["book_only", "series", "author"].includes(value);
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Library */}
      <Select
        id="library-select"
        label="Library"
        value={libraryId || ""}
        onChange={(e) => onLibraryChange(Number(e.target.value))}
      >
        {libraries.map((lib) => (
          <option key={lib.id} value={lib.id}>
            {lib.name}
          </option>
        ))}
        {libraries.length === 0 && <option disabled>No libraries found</option>}
      </Select>

      {/* Wanted Formats */}
      <Select
        id="format-mode-select"
        label="Wanted Formats"
        value={currentFormatMode === "custom" ? "book" : currentFormatMode}
        onChange={(e) => onFormatModeChange(e.target.value)}
        options={formatModeService.getOptions().map((opt) => ({
          value: opt.id,
          label: opt.label,
        }))}
      />

      {/* Monitor */}
      <Select
        id="monitor-select"
        label="Monitor"
        value={monitor}
        onChange={(e) => {
          // We might need to cast or validate here, but for now passing string to handler
          // The parent/hook handles the type safety for state
          // But here we need to cast to call onMonitorChange which expects MonitorMode
          // Let's do a safe cast if possible
          const val = e.target.value;
          if (isValidMonitorMode(val)) {
            onMonitorChange(val);
          }
        }}
      >
        <option value="book_only">Book Only</option>
        <option value="series">Series</option>
        <option value="author">Author</option>
      </Select>

      {/* Monitor Value (conditional) */}
      {monitor !== "book_only" && (
        <TextInput
          id="monitor-value-input"
          label={monitor === "series" ? "Series Name" : "Author Name"}
          value={monitorValue}
          onChange={(e) => onMonitorValueChange(e.target.value)}
          placeholder={
            monitor === "series" ? "Enter series name" : "Enter author name"
          }
        />
      )}

      {/* Tags */}
      <div className="flex flex-col gap-2 md:col-span-2">
        <TagInput
          label="Tags"
          tags={tags}
          onChange={onTagsChange}
          placeholder="Press enter to add tags..."
        />
      </div>
    </div>
  );
}
