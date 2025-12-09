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

import { cn } from "@/libs/utils";
import type { ShelfType } from "@/types/shelf";

export interface ShelfTypeSelectorProps {
  /** Current shelf type. */
  value: ShelfType;
  /** Callback when type changes. */
  onChange: (type: ShelfType) => void;
  /** Additional CSS classes. */
  className?: string;
}

/**
 * Component for selecting shelf type (shelf vs read_list).
 *
 * Allows users to choose between a regular shelf and a read list
 * when creating or editing shelves.
 */
export function ShelfTypeSelector({
  value,
  onChange,
  className,
}: ShelfTypeSelectorProps) {
  return (
    <div className={cn("flex gap-2", className)}>
      <label className="flex items-center gap-2">
        <input
          type="radio"
          name="shelf_type"
          value="shelf"
          checked={value === "shelf"}
          onChange={() => onChange("shelf")}
          className="h-4 w-4 text-primary-a90"
        />
        <span className="text-sm">Shelf</span>
      </label>
      <label className="flex items-center gap-2">
        <input
          type="radio"
          name="shelf_type"
          value="read_list"
          checked={value === "read_list"}
          onChange={() => onChange("read_list")}
          className="h-4 w-4 text-primary-a90"
        />
        <span className="text-sm">Read List</span>
      </label>
    </div>
  );
}
