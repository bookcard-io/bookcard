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

interface GeneralTabProps {
  author: AuthorWithMetadata;
  form: AuthorUpdate;
  onFieldChange: <K extends keyof AuthorUpdate>(
    field: K,
    value: AuthorUpdate[K],
  ) => void;
}

/**
 * Component for the general information tab.
 *
 * Follows SRP by handling only general form fields.
 */
export function GeneralTab({
  author: _author,
  form,
  onFieldChange,
}: GeneralTabProps) {
  const inputBaseClasses =
    "w-full min-h-[38px] rounded-md border border-surface-a20 bg-surface-a20 px-[10px] py-1.5 text-sm text-text-a0 transition-colors focus:outline-none focus:border-primary-a0 focus:bg-surface-a10 disabled:cursor-not-allowed disabled:opacity-50";
  const textareaBaseClasses =
    "w-full h-full min-h-[120px] rounded-md border border-surface-a20 bg-surface-a20 px-[10px] py-1.5 text-sm text-text-a0 transition-colors focus:outline-none focus:border-primary-a0 focus:bg-surface-a10 resize-y";
  const labelDivClasses = "font-semibold text-sm text-text-a10";

  return (
    <div className="flex h-full w-full flex-col">
      <div className="flex flex-col gap-4">
        <label className="flex flex-col gap-2">
          <div className={labelDivClasses}>Author</div>
          <input
            className={inputBaseClasses}
            value={form.name || ""}
            onChange={(e) => onFieldChange("name", e.target.value || undefined)}
            placeholder="Author name"
          />
        </label>
        <label className="flex flex-col gap-2">
          <div className={labelDivClasses}>Location</div>
          <input
            className={inputBaseClasses}
            value={form.location || ""}
            onChange={(e) => onFieldChange("location", e.target.value || null)}
            placeholder="Country or location"
          />
        </label>
        <label className="flex min-h-0 flex-1 flex-col gap-2">
          <div className={labelDivClasses}>Biography</div>
          <textarea
            className={`${textareaBaseClasses} flex-1`}
            value={form.biography || ""}
            onChange={(e) => onFieldChange("biography", e.target.value || null)}
          />
        </label>
      </div>
    </div>
  );
}
