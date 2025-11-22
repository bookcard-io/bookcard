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

import type { AuthorUpdate, AuthorWithMetadata } from "@/types/author";

interface AdvancedTabProps {
  author: AuthorWithMetadata;
  form: AuthorUpdate;
  onFieldChange: <K extends keyof AuthorUpdate>(
    field: K,
    value: AuthorUpdate[K],
  ) => void;
}

/**
 * Component for the advanced information tab.
 *
 * Follows SRP by handling only advanced form fields.
 */
export function AdvancedTab({ form, onFieldChange }: AdvancedTabProps) {
  const inputBaseClasses =
    "w-full min-h-[38px] rounded-md border border-surface-a20 bg-surface-a20 px-[10px] py-1.5 text-sm text-text-a0 transition-colors focus:outline-none focus:border-primary-a0 focus:bg-surface-a10 disabled:cursor-not-allowed disabled:opacity-50";
  const labelDivClasses = "font-semibold text-sm text-text-a10";

  return (
    <div className="h-full w-full overflow-auto">
      <div className="grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-2">
          <div className={labelDivClasses}>Personal Name</div>
          <input
            className={inputBaseClasses}
            value={form.personal_name || ""}
            onChange={(e) =>
              onFieldChange("personal_name", e.target.value || null)
            }
          />
        </label>
        <label className="flex flex-col gap-2">
          <div className={labelDivClasses}>Fuller Name</div>
          <input
            className={inputBaseClasses}
            value={form.fuller_name || ""}
            onChange={(e) =>
              onFieldChange("fuller_name", e.target.value || null)
            }
          />
        </label>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-2">
          <div className={labelDivClasses}>Title</div>
          <input
            className={inputBaseClasses}
            value={form.title || ""}
            onChange={(e) => onFieldChange("title", e.target.value || null)}
            placeholder="e.g., OBE, Sir"
          />
        </label>
        <label className="flex flex-col gap-2">
          <div className={labelDivClasses}>Entity Type</div>
          <input
            className={inputBaseClasses}
            value={form.entity_type || ""}
            onChange={(e) =>
              onFieldChange("entity_type", e.target.value || null)
            }
            placeholder="e.g., person, corporate"
          />
        </label>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-2">
          <div className={labelDivClasses}>Birth Date</div>
          <input
            className={inputBaseClasses}
            type="date"
            value={form.birth_date || ""}
            onChange={(e) =>
              onFieldChange("birth_date", e.target.value || null)
            }
          />
        </label>
        <label className="flex flex-col gap-2">
          <div className={labelDivClasses}>Death Date</div>
          <input
            className={inputBaseClasses}
            type="date"
            value={form.death_date || ""}
            onChange={(e) =>
              onFieldChange("death_date", e.target.value || null)
            }
          />
        </label>
      </div>
    </div>
  );
}
