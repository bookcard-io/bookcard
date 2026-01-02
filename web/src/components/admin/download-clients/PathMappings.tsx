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

import { FaPlus, FaTrash } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { TextInput } from "@/components/forms/TextInput";
import type { PathMapping } from "./types";

interface PathMappingsProps {
  mappings: PathMapping[];
  onChange: (mappings: PathMapping[]) => void;
}

export function PathMappings({ mappings, onChange }: PathMappingsProps) {
  const handleAdd = () => {
    onChange([...mappings, { remote: "", local: "" }]);
  };

  const handleRemove = (index: number) => {
    const newMappings = [...mappings];
    newMappings.splice(index, 1);
    onChange(newMappings);
  };

  const handleChange = (
    index: number,
    field: keyof PathMapping,
    value: string,
  ) => {
    const newMappings = [...mappings];
    const item = { ...newMappings[index] } as PathMapping;
    item[field] = value;
    newMappings[index] = item;
    onChange(newMappings);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="font-medium text-sm text-text-a0">
          Remote Path Mappings
        </span>
        <Button
          type="button"
          variant="secondary"
          size="small"
          onClick={handleAdd}
          className="text-xs"
        >
          <FaPlus className="mr-1 h-3 w-3" />
          Add Mapping
        </Button>
      </div>

      <p className="text-text-a20 text-xs">
        Map remote paths reported by the download client (e.g., inside Docker)
        to local paths accessible by BookCard.
      </p>

      {mappings.length === 0 ? (
        <div className="rounded-md border border-surface-a20 border-dashed bg-[var(--color-surface-tonal-a0)] p-4 text-center text-sm text-text-a20">
          No mappings defined. Click "Add Mapping" to create one.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {mappings.map((mapping, index) => (
            <div
              // biome-ignore lint/suspicious/noArrayIndexKey: order is stable within form session
              key={index}
              className="flex items-start gap-3 rounded-md border border-surface-a20 bg-[var(--color-surface-tonal-a0)] p-3"
            >
              <div className="grid flex-1 grid-cols-1 gap-3 md:grid-cols-2">
                <TextInput
                  id={`remote-${index}`}
                  label="Remote Path"
                  value={mapping.remote}
                  onChange={(e) =>
                    handleChange(index, "remote", e.target.value)
                  }
                  placeholder="e.g., /downloads/"
                />
                <TextInput
                  id={`local-${index}`}
                  label="Local Path"
                  value={mapping.local}
                  onChange={(e) => handleChange(index, "local", e.target.value)}
                  placeholder="e.g., /mnt/downloads/"
                />
              </div>
              <button
                type="button"
                onClick={() => handleRemove(index)}
                className="mt-8 text-[var(--color-danger-a0)] hover:text-[var(--color-danger-a10)]"
                title="Remove mapping"
              >
                <FaTrash className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
